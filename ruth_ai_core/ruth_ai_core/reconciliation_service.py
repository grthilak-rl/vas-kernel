"""
Phase 8.2 – Ruth AI Core Subscription Reconciliation

RECONCILIATION SERVICE

This module provides a long-running service that periodically reconciles
StreamAgent subscriptions against backend assignment intent.

EXECUTION MODEL:
- Background asyncio task
- Periodic polling (default: every 30 seconds)
- Best-effort execution (failures don't stop the loop)
- Graceful shutdown support
"""

import asyncio
from typing import Optional
from loguru import logger

from .reconciliation import ReconciliationEngine


class ReconciliationService:
    """
    Periodic reconciliation service for Ruth AI Core.

    Phase 8.2: Runs reconciliation loop in background task.

    LIFECYCLE:
    1. Create service with reconciliation engine
    2. Call start() to begin periodic reconciliation
    3. Call stop() for graceful shutdown
    4. await wait_stopped() to wait for shutdown completion

    CRITICAL:
    - Must NOT block video pipelines
    - Must NOT block inference execution
    - Failures must be logged but not crash the service
    - Service must be restartable
    """

    def __init__(
        self,
        reconciliation_engine: ReconciliationEngine,
        interval_seconds: float = 30.0
    ):
        """
        Initialize reconciliation service.

        Args:
            reconciliation_engine: Reconciliation engine instance
            interval_seconds: Reconciliation interval in seconds (default: 30.0)
        """
        self.reconciliation_engine = reconciliation_engine
        self.interval_seconds = interval_seconds

        # Service state
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        """
        Start the periodic reconciliation loop.

        Creates a background asyncio task that runs reconciliation
        at the configured interval.

        Raises:
            RuntimeError: If service is already running
        """
        if self._running:
            raise RuntimeError("ReconciliationService is already running")

        logger.info(
            f"Starting ReconciliationService with interval={self.interval_seconds}s "
            f"(Phase 8.2)"
        )

        self._running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._reconciliation_loop())

    def stop(self) -> None:
        """
        Stop the periodic reconciliation loop.

        Signals the background task to stop gracefully.
        Does NOT wait for task completion.

        To wait for shutdown completion, call await wait_stopped() after stop().
        """
        if not self._running:
            logger.warning("ReconciliationService is not running, ignoring stop()")
            return

        logger.info("Stopping ReconciliationService (Phase 8.2)")
        self._running = False
        self._stop_event.set()

    async def wait_stopped(self) -> None:
        """
        Wait for the reconciliation loop to stop completely.

        Call this after stop() to ensure clean shutdown.

        Returns:
            When the background task has exited
        """
        if self._task is not None:
            try:
                await self._task
            except asyncio.CancelledError:
                pass

            self._task = None

        logger.info("ReconciliationService stopped (Phase 8.2)")

    async def _reconciliation_loop(self) -> None:
        """
        Background reconciliation loop.

        Runs periodically until stopped.

        CRITICAL:
        - This MUST NOT crash on errors
        - Each iteration is independent (stateless)
        - Failures are logged and the loop continues
        """
        logger.info("ReconciliationService loop started (Phase 8.2)")

        try:
            while self._running:
                try:
                    # Run reconciliation cycle
                    stats = await self.reconciliation_engine.reconcile_all()

                    logger.debug(
                        f"Reconciliation cycle stats (Phase 8.2): {stats}"
                    )

                except Exception as e:
                    # Reconciliation failed, but loop must continue
                    logger.error(
                        f"Reconciliation cycle failed (Phase 8.2), will retry: {e}"
                    )

                # Wait for next cycle or stop signal
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.interval_seconds
                    )
                    # Stop event was set, exit loop
                    break

                except asyncio.TimeoutError:
                    # Timeout reached, continue to next cycle
                    pass

        except asyncio.CancelledError:
            logger.info("ReconciliationService loop cancelled (Phase 8.2)")
            raise

        except Exception as e:
            # Unexpected error (should not happen)
            logger.error(
                f"ReconciliationService loop crashed unexpectedly (Phase 8.2): {e}"
            )

        finally:
            self._running = False
            logger.info("ReconciliationService loop exited (Phase 8.2)")

    @property
    def is_running(self) -> bool:
        """Check if the service is currently running."""
        return self._running
