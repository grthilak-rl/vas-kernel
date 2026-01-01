"""AI Event service for persisting AI inference results.

Phase 5.1: Backend AI Integration (AI Event Schema + Persistence)
Phase 5.2: Snapshot / Clip Triggers (added trigger invocation)
Phase 5.3: Read-only Backend APIs (added query methods)

This service provides write-only, insert-only persistence for AI inference events.
Failures are silent (best-effort semantics) and do NOT affect VAS, Ruth AI Core, or model containers.

Phase 5.2 Addition:
- Triggers snapshot/clip capture AFTER successful persistence
- Fire-and-forget (non-blocking)
- Trigger failures do NOT affect persistence

Phase 5.3 Addition:
- Read-only query methods for AI events
- Filtering by camera, model, time range
- Pagination support
- Safe defaults (bounded limits)
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.ai_event import AIEvent
from app.schemas.ai_event import AIEventCreate


class AIEventService:
    """Service for persisting AI inference events.

    Phase 5.1 Constraints:
    - Write-only, insert-only persistence
    - Best-effort semantics (failures are silent)
    - No coupling to inference execution
    - No retries, no recovery, no alerts
    - Must NOT affect VAS, Ruth AI Core, or model containers

    Phase 5.2 Addition:
    - Triggers snapshot/clip capture after successful persistence
    - Fire-and-forget (non-blocking, doesn't affect persistence)
    """

    def __init__(self):
        """Initialize AI event service."""
        # Lazy import to avoid circular dependency
        # AIEventTriggerService imports this module
        self._trigger_service = None
        logger.info("AIEventService initialized (Phase 5.1+5.2: persistence + triggers)")

    async def persist_event(
        self,
        event_data: AIEventCreate,
        db: AsyncSession
    ) -> Optional[AIEvent]:
        """Persist an AI inference event to the database.

        This method implements best-effort persistence:
        - Successful persistence returns the created AIEvent
        - Failures are logged and return None (silent drop)
        - No exceptions are raised to caller
        - No retries are attempted

        Args:
            event_data: AI event data to persist
            db: Database session

        Returns:
            AIEvent if successful, None if failed (silent drop)

        Phase 5.1 Guarantees:
        - Failure does NOT affect caller
        - No blocking, no retries, no recovery
        - Events may be dropped silently
        """
        try:
            # Create ORM model from Pydantic schema
            ai_event = AIEvent(
                camera_id=event_data.camera_id,
                model_id=event_data.model_id,
                timestamp=event_data.timestamp,
                frame_id=event_data.frame_id,
                detections=event_data.detections,
                confidence=event_data.confidence,
                event_metadata=event_data.event_metadata or {}
            )

            # Persist to database (insert-only)
            db.add(ai_event)
            await db.commit()
            await db.refresh(ai_event)

            logger.debug(
                f"AI event persisted: camera={event_data.camera_id}, "
                f"model={event_data.model_id}, ts={event_data.timestamp}"
            )

            # Phase 5.2: Trigger snapshot/clip capture (fire-and-forget)
            # This is non-blocking and failures do NOT affect persistence
            self._invoke_triggers(ai_event.id)

            return ai_event

        except Exception as e:
            # Best-effort semantics: log and drop silently
            # Rollback to prevent session contamination
            try:
                await db.rollback()
            except Exception:
                pass  # Even rollback failures are silent

            logger.warning(
                f"AI event persistence failed (silent drop): "
                f"camera={event_data.camera_id}, model={event_data.model_id}, "
                f"error={type(e).__name__}: {str(e)}"
            )

            return None

    async def persist_event_dict(
        self,
        camera_id: UUID,
        model_id: str,
        timestamp: datetime,
        detections: Dict[str, Any],
        frame_id: Optional[int] = None,
        confidence: Optional[float] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
        db: AsyncSession = None
    ) -> Optional[AIEvent]:
        """Convenience method to persist an event from raw parameters.

        This method provides a simpler interface for cases where AIEventCreate
        schema is not already constructed.

        Args:
            camera_id: Camera/device UUID
            model_id: Model identifier
            timestamp: Event timestamp
            detections: Model-specific detection payload
            frame_id: Optional frame ID
            confidence: Optional confidence score (0.0-1.0)
            event_metadata: Optional metadata dict
            db: Database session

        Returns:
            AIEvent if successful, None if failed (silent drop)

        Phase 5.1 Note:
        - Same best-effort semantics as persist_event()
        - Validation failures result in silent drop
        """
        try:
            event_data = AIEventCreate(
                camera_id=camera_id,
                model_id=model_id,
                timestamp=timestamp,
                detections=detections,
                frame_id=frame_id,
                confidence=confidence,
                event_metadata=event_metadata
            )

            return await self.persist_event(event_data, db)

        except Exception as e:
            # Validation or construction failure - silent drop
            logger.warning(
                f"AI event construction failed (silent drop): "
                f"camera={camera_id}, model={model_id}, "
                f"error={type(e).__name__}: {str(e)}"
            )
            return None

    def _invoke_triggers(self, event_id: UUID) -> None:
        """Invoke snapshot/clip triggers for a persisted AI event (Phase 5.2).

        This method uses lazy import to avoid circular dependencies and
        delegates to AIEventTriggerService in a fire-and-forget manner.

        Args:
            event_id: UUID of the persisted AI event

        Phase 5.2 Guarantees:
        - Non-blocking (returns immediately)
        - Trigger failures do NOT affect persistence
        - Lazy initialization of trigger service
        """
        try:
            # Lazy import on first use (avoids circular dependency)
            if self._trigger_service is None:
                from app.services.ai_event_trigger_service import ai_event_trigger_service
                self._trigger_service = ai_event_trigger_service

            # Invoke triggers (fire-and-forget)
            self._trigger_service.trigger_on_event(event_id)

        except Exception as e:
            # Even trigger invocation failures are silent (best-effort)
            logger.warning(
                f"Failed to invoke AI event triggers for {event_id} (silent drop): "
                f"{type(e).__name__}: {str(e)}"
            )

    # Phase 5.3: Read-only query methods

    async def get_event(
        self,
        event_id: UUID,
        db: AsyncSession
    ) -> Optional[AIEvent]:
        """Get a single AI event by ID (Phase 5.3).

        Args:
            event_id: AI event UUID
            db: Database session

        Returns:
            AIEvent if found, None otherwise

        Phase 5.3 Constraints:
        - Read-only operation
        - No side effects
        """
        try:
            query = select(AIEvent).where(AIEvent.id == event_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get AI event {event_id}: {e}")
            return None

    async def list_events(
        self,
        db: AsyncSession,
        camera_id: Optional[UUID] = None,
        model_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AIEvent]:
        """List AI events with optional filtering and pagination (Phase 5.3).

        Args:
            db: Database session
            camera_id: Optional filter by camera
            model_id: Optional filter by model
            start_time: Optional filter by start time (inclusive)
            end_time: Optional filter by end time (inclusive)
            limit: Maximum number of results (default 100, max 1000)
            offset: Number of results to skip (default 0)

        Returns:
            List of AIEvent objects (may be empty)

        Phase 5.3 Constraints:
        - Read-only operation
        - Safe defaults (limit capped at 1000)
        - Ordered by timestamp DESC (newest first)
        - No aggregations or analytics
        """
        try:
            # Cap limit for safety
            limit = min(limit, 1000)

            # Build filter conditions
            conditions = []

            if camera_id is not None:
                conditions.append(AIEvent.camera_id == camera_id)

            if model_id is not None:
                conditions.append(AIEvent.model_id == model_id)

            if start_time is not None:
                conditions.append(AIEvent.timestamp >= start_time)

            if end_time is not None:
                conditions.append(AIEvent.timestamp <= end_time)

            # Build query
            query = select(AIEvent)

            if conditions:
                query = query.where(and_(*conditions))

            # Order by timestamp DESC (newest first)
            query = query.order_by(AIEvent.timestamp.desc())

            # Apply pagination
            query = query.limit(limit).offset(offset)

            # Execute
            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to list AI events: {e}")
            return []

    async def count_events(
        self,
        db: AsyncSession,
        camera_id: Optional[UUID] = None,
        model_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """Count AI events matching filters (Phase 5.3).

        Args:
            db: Database session
            camera_id: Optional filter by camera
            model_id: Optional filter by model
            start_time: Optional filter by start time (inclusive)
            end_time: Optional filter by end time (inclusive)

        Returns:
            Count of matching events (0 if error or no matches)

        Phase 5.3 Constraints:
        - Read-only operation
        - No side effects
        """
        try:
            # Build filter conditions
            conditions = []

            if camera_id is not None:
                conditions.append(AIEvent.camera_id == camera_id)

            if model_id is not None:
                conditions.append(AIEvent.model_id == model_id)

            if start_time is not None:
                conditions.append(AIEvent.timestamp >= start_time)

            if end_time is not None:
                conditions.append(AIEvent.timestamp <= end_time)

            # Build query
            query = select(func.count()).select_from(AIEvent)

            if conditions:
                query = query.where(and_(*conditions))

            # Execute
            result = await db.execute(query)
            return result.scalar_one()

        except Exception as e:
            logger.error(f"Failed to count AI events: {e}")
            return 0
