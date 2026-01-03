"""
Phase 8.2 – Ruth AI Core Subscription Reconciliation

RECONCILIATION SERVICE MANAGER

This module integrates Ruth AI Core reconciliation into the VAS backend lifecycle.

CRITICAL:
- Starts reconciliation service during backend startup
- Stops reconciliation service during backend shutdown
- Provides global access to reconciliation stats (read-only)
"""

import os
from loguru import logger

# Phase 8.2: Import Ruth AI Core reconciliation components
try:
    from ruth_ai_core import (
        AssignmentClient,
        AgentRegistry,
        ReconciliationEngine,
        ReconciliationService,
    )
    RUTH_AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Ruth AI Core not available, reconciliation disabled: {e}")
    RUTH_AI_AVAILABLE = False


class ReconciliationServiceManager:
    """
    Manager for Ruth AI Core reconciliation service.

    Phase 8.2: Integrates reconciliation into backend lifecycle.

    LIFECYCLE:
    1. Initialize during backend startup
    2. Start reconciliation loop
    3. Stop during backend shutdown
    """

    def __init__(self):
        """Initialize reconciliation service manager."""
        self.reconciliation_service = None
        self.agent_registry = None
        self.assignment_client = None
        self.reconciliation_engine = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize reconciliation components.

        Called during backend startup (lifespan context manager).

        Returns:
            True if initialized successfully, False otherwise

        CRITICAL: Initialization failure must NOT crash the backend.
        This is best-effort only.
        """
        if not RUTH_AI_AVAILABLE:
            logger.warning(
                "Ruth AI Core not available, reconciliation disabled (Phase 8.2)"
            )
            return False

        try:
            # Get backend URL from environment
            # Default: localhost:8080 (same host)
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")

            # Get reconciliation interval from environment (default: 30 seconds)
            try:
                interval_seconds = float(os.getenv("RECONCILIATION_INTERVAL_SECONDS", "30.0"))
            except ValueError:
                logger.warning(
                    "Invalid RECONCILIATION_INTERVAL_SECONDS, using default 30.0"
                )
                interval_seconds = 30.0

            # Initialize components
            logger.info(
                f"Initializing Ruth AI Core reconciliation (Phase 8.2): "
                f"backend_url={backend_url} interval={interval_seconds}s"
            )

            # Create assignment client
            self.assignment_client = AssignmentClient(backend_url=backend_url)

            # Create agent registry
            self.agent_registry = AgentRegistry()

            # Create reconciliation engine
            self.reconciliation_engine = ReconciliationEngine(
                agent_registry=self.agent_registry,
                assignment_client=self.assignment_client
            )

            # Create reconciliation service
            self.reconciliation_service = ReconciliationService(
                reconciliation_engine=self.reconciliation_engine,
                interval_seconds=interval_seconds
            )

            self._initialized = True

            logger.info(
                "Ruth AI Core reconciliation initialized successfully (Phase 8.2)"
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize Ruth AI Core reconciliation (Phase 8.2): {e}"
            )
            self._initialized = False
            return False

    def start(self) -> bool:
        """
        Start the reconciliation service.

        Called after initialize() during backend startup.

        Returns:
            True if started successfully, False otherwise

        CRITICAL: Start failure must NOT crash the backend.
        This is best-effort only.
        """
        if not self._initialized:
            logger.warning(
                "Reconciliation service not initialized, cannot start (Phase 8.2)"
            )
            return False

        try:
            if self.reconciliation_service is None:
                logger.error(
                    "Reconciliation service is None, cannot start (Phase 8.2)"
                )
                return False

            self.reconciliation_service.start()

            logger.info(
                "Ruth AI Core reconciliation service started (Phase 8.2)"
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to start Ruth AI Core reconciliation service (Phase 8.2): {e}"
            )
            return False

    async def stop(self) -> None:
        """
        Stop the reconciliation service.

        Called during backend shutdown (lifespan context manager).

        CRITICAL: Stop must be graceful and not hang.
        Timeout is acceptable.
        """
        if not self._initialized or self.reconciliation_service is None:
            logger.info(
                "Reconciliation service not running, nothing to stop (Phase 8.2)"
            )
            return

        try:
            logger.info(
                "Stopping Ruth AI Core reconciliation service (Phase 8.2)"
            )

            # Signal stop
            self.reconciliation_service.stop()

            # Wait for shutdown (with timeout)
            import asyncio
            try:
                await asyncio.wait_for(
                    self.reconciliation_service.wait_stopped(),
                    timeout=10.0
                )
                logger.info(
                    "Ruth AI Core reconciliation service stopped gracefully (Phase 8.2)"
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Ruth AI Core reconciliation service stop timed out (Phase 8.2)"
                )

        except Exception as e:
            logger.error(
                f"Error stopping Ruth AI Core reconciliation service (Phase 8.2): {e}"
            )

    def is_running(self) -> bool:
        """Check if reconciliation service is running."""
        if not self._initialized or self.reconciliation_service is None:
            return False

        return self.reconciliation_service.is_running

    def get_agent_registry(self):
        """
        Get the agent registry (for observability/debugging).

        Returns:
            AgentRegistry instance or None if not initialized
        """
        return self.agent_registry


# Global singleton instance
reconciliation_manager = ReconciliationServiceManager()
