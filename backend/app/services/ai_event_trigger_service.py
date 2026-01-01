"""AI Event Trigger Service for Phase 5.2: Snapshot / Clip Triggers.

This service reacts to persisted AI events and triggers snapshot/clip capture
using existing VAS infrastructure. Follows best-effort, fire-and-forget semantics.

Phase 5.2 Constraints:
- Triggers execute AFTER AI event persistence (not before)
- Fire-and-forget execution (asyncio.create_task)
- Silent failures (no exceptions raised, no retries)
- Reuses existing SnapshotService and BookmarkService (no changes)
- Idempotent per AI event (no duplicate triggers)
- Must NOT affect VAS, Ruth AI Core, or AI event persistence
"""
import asyncio
from typing import Optional, Set
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.device import Device
from app.models.ai_event import AIEvent
from app.services.snapshot_service import snapshot_service
from app.services.bookmark_service import bookmark_service
from database import AsyncSessionLocal


class AIEventTriggerService:
    """Service for triggering snapshots/clips based on AI events.

    Phase 5.2 Constraints:
    - Best-effort, fire-and-forget execution
    - Silent failures (no exceptions to caller)
    - Idempotent (no duplicate triggers per event)
    - No retries, no alerts, no queues
    """

    def __init__(self):
        """Initialize AI event trigger service."""
        # Track triggered events for idempotency (in-memory, per-process)
        # Note: This is simple idempotency. Production may use Redis/DB for distributed systems.
        self._triggered_events: Set[UUID] = set()

        # Configuration: Which events trigger what
        # Default: All events trigger snapshots (clips are opt-in via configuration)
        self._trigger_snapshot_enabled = True
        self._trigger_clip_enabled = False  # Disabled by default (clips are expensive)

        logger.info(
            "AIEventTriggerService initialized (Phase 5.2: snapshot/clip triggers) - "
            f"snapshot_enabled={self._trigger_snapshot_enabled}, "
            f"clip_enabled={self._trigger_clip_enabled}"
        )

    def trigger_on_event(self, event_id: UUID) -> None:
        """Trigger snapshot/clip capture for an AI event (fire-and-forget).

        This method spawns a background task and returns immediately.
        Failures are silent and do NOT affect the caller.

        Args:
            event_id: UUID of the AI event that was just persisted

        Phase 5.2 Guarantees:
        - Non-blocking (returns immediately)
        - Idempotent (won't trigger twice for same event)
        - Failures are silent
        """
        # Check idempotency (prevent duplicate triggers)
        if event_id in self._triggered_events:
            logger.debug(f"AI event {event_id} already triggered, skipping")
            return

        # Mark as triggered immediately (before background task starts)
        self._triggered_events.add(event_id)

        # Spawn background task (fire-and-forget)
        asyncio.create_task(self._execute_triggers(event_id))

        logger.debug(f"AI event trigger spawned for event {event_id}")

    async def _execute_triggers(self, event_id: UUID) -> None:
        """Execute snapshot/clip triggers in background (best-effort).

        This method runs in a background task and must NEVER raise exceptions.
        All failures are logged and silently dropped.

        Args:
            event_id: UUID of the AI event
        """
        try:
            # Create separate database session for background task
            async with AsyncSessionLocal() as session:
                # 1. Retrieve AI event
                query = select(AIEvent).where(AIEvent.id == event_id)
                result = await session.execute(query)
                event = result.scalar_one_or_none()

                if not event:
                    logger.warning(
                        f"AI event trigger failed: event {event_id} not found (silent drop)"
                    )
                    return

                # 2. Retrieve device (to get rtsp_url)
                device_query = select(Device).where(Device.id == event.camera_id)
                device_result = await session.execute(device_query)
                device = device_result.scalar_one_or_none()

                if not device:
                    logger.warning(
                        f"AI event trigger failed: device {event.camera_id} not found "
                        f"for event {event_id} (silent drop)"
                    )
                    return

                if not device.rtsp_url:
                    logger.warning(
                        f"AI event trigger failed: device {event.camera_id} has no RTSP URL "
                        f"for event {event_id} (silent drop)"
                    )
                    return

                # 3. Trigger snapshot (if enabled)
                if self._trigger_snapshot_enabled:
                    await self._trigger_snapshot(event, device, session)

                # 4. Trigger clip (if enabled)
                if self._trigger_clip_enabled:
                    await self._trigger_clip(event, device, session)

                logger.info(
                    f"AI event triggers completed for event {event_id} "
                    f"(camera={event.camera_id}, model={event.model_id})"
                )

        except Exception as e:
            # Best-effort semantics: ALL exceptions are silent
            logger.warning(
                f"AI event trigger failed for event {event_id} (silent drop): "
                f"{type(e).__name__}: {str(e)}"
            )

    async def _trigger_snapshot(
        self,
        event: AIEvent,
        device: Device,
        session: AsyncSession
    ) -> None:
        """Trigger snapshot capture for an AI event (best-effort).

        Args:
            event: AI event that triggered this
            device: Device/camera for the event
            session: Database session

        Phase 5.2 Note:
        - Uses existing SnapshotService.capture_from_live_stream()
        - Failures are logged and silently dropped
        - No changes to SnapshotService
        """
        try:
            logger.debug(
                f"Triggering snapshot for AI event {event.id} "
                f"(camera={device.id}, model={event.model_id})"
            )

            # Call existing snapshot service (reuse VAS infrastructure)
            snapshot = await snapshot_service.capture_from_live_stream(
                device_id=str(device.id),
                rtsp_url=device.rtsp_url,
                db=session
            )

            logger.info(
                f"AI-triggered snapshot created: {snapshot.id} "
                f"(event={event.id}, camera={device.id}, model={event.model_id})"
            )

        except Exception as e:
            # Best-effort: snapshot failure is silent
            logger.warning(
                f"AI-triggered snapshot failed for event {event.id} (silent drop): "
                f"{type(e).__name__}: {str(e)}"
            )
            # Rollback to prevent session contamination
            try:
                await session.rollback()
            except Exception:
                pass

    async def _trigger_clip(
        self,
        event: AIEvent,
        device: Device,
        session: AsyncSession
    ) -> None:
        """Trigger clip/bookmark capture for an AI event (best-effort).

        Args:
            event: AI event that triggered this
            device: Device/camera for the event
            session: Database session

        Phase 5.2 Note:
        - Uses existing BookmarkService.capture_from_live_stream()
        - Creates 6-second clip centered at event timestamp
        - Label includes model_id for identification
        - Failures are logged and silently dropped
        - No changes to BookmarkService
        """
        try:
            logger.debug(
                f"Triggering clip for AI event {event.id} "
                f"(camera={device.id}, model={event.model_id})"
            )

            # Generate label with AI context
            label = f"AI: {event.model_id}"
            if event.confidence:
                label += f" ({event.confidence:.2f})"

            # Call existing bookmark service (reuse VAS infrastructure)
            bookmark = await bookmark_service.capture_from_live_stream(
                device_id=str(device.id),
                rtsp_url=device.rtsp_url,
                label=label,
                db=session
            )

            logger.info(
                f"AI-triggered clip created: {bookmark.id} "
                f"(event={event.id}, camera={device.id}, model={event.model_id})"
            )

        except Exception as e:
            # Best-effort: clip failure is silent
            logger.warning(
                f"AI-triggered clip failed for event {event.id} (silent drop): "
                f"{type(e).__name__}: {str(e)}"
            )
            # Rollback to prevent session contamination
            try:
                await session.rollback()
            except Exception:
                pass

    def enable_snapshot_triggers(self, enabled: bool = True) -> None:
        """Enable or disable snapshot triggers.

        Args:
            enabled: True to enable, False to disable
        """
        self._trigger_snapshot_enabled = enabled
        logger.info(f"AI event snapshot triggers: {'enabled' if enabled else 'disabled'}")

    def enable_clip_triggers(self, enabled: bool = True) -> None:
        """Enable or disable clip triggers.

        Args:
            enabled: True to enable, False to disable

        Note: Clips are expensive (FFmpeg, storage), disabled by default.
        """
        self._trigger_clip_enabled = enabled
        logger.info(f"AI event clip triggers: {'enabled' if enabled else 'disabled'}")

    def get_trigger_status(self) -> dict:
        """Get current trigger configuration status.

        Returns:
            dict with trigger status and stats
        """
        return {
            "snapshot_triggers_enabled": self._trigger_snapshot_enabled,
            "clip_triggers_enabled": self._trigger_clip_enabled,
            "triggered_events_count": len(self._triggered_events),
        }


# Global service instance (singleton pattern, following VAS conventions)
ai_event_trigger_service = AIEventTriggerService()
