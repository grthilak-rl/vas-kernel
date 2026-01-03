"""
Phase 8.2 – Ruth AI Core Subscription Reconciliation

RECONCILIATION ENGINE

This module implements subscription reconciliation logic that bridges
backend assignment INTENT (Phase 8.1) to StreamAgent EXECUTION (Phase 3.x).

RECONCILIATION SEMANTICS:
- Desired state = backend assignments (Phase 8.1 APIs)
- Current state = StreamAgent subscriptions (Phase 3.2)
- Reconciliation = align current → desired (best-effort)

CRITICAL CONSTRAINTS:
- Best-effort execution (failures are acceptable)
- No retries, no rollback, no transactions
- Partial reconciliation is acceptable
- Must NOT block video pipelines
- Must NOT block inference execution
- Must converge eventually
"""

from typing import Dict, List, Set, Any, Optional
from loguru import logger

from .agent import StreamAgent
from .agent_registry import AgentRegistry
from .assignment_client import AssignmentClient


class ReconciliationEngine:
    """
    Subscription reconciliation engine for Ruth AI Core.

    Phase 8.2: Reconciles backend assignment intent with StreamAgent subscriptions.

    RECONCILIATION ALGORITHM:
    1. Fetch desired assignments from backend (Phase 8.1 APIs)
    2. For each camera with assignments:
       a. Get or create StreamAgent
       b. Compare desired vs current subscriptions
       c. Add missing subscriptions
       d. Remove obsolete subscriptions
       e. Update existing subscriptions if config changed
    3. Handle failures gracefully (partial reconciliation OK)

    FAILURE SEMANTICS:
    - Backend unavailable → skip reconciliation (retry next cycle)
    - Camera not found → log warning, continue with other cameras
    - Subscription add fails → log error, continue with other subscriptions
    - Subscription remove fails → log error, continue
    - Partial reconciliation is acceptable
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        assignment_client: AssignmentClient
    ):
        """
        Initialize reconciliation engine.

        Args:
            agent_registry: StreamAgent registry
            assignment_client: Backend assignment API client
        """
        self.agent_registry = agent_registry
        self.assignment_client = assignment_client

    async def reconcile_all(self) -> Dict[str, Any]:
        """
        Reconcile all camera subscriptions against backend assignment intent.

        This is the main reconciliation entry point, called periodically.

        Returns:
            Reconciliation summary with statistics:
            - cameras_processed: Number of cameras reconciled
            - subscriptions_added: Number of subscriptions created
            - subscriptions_removed: Number of subscriptions deleted
            - subscriptions_updated: Number of subscriptions modified
            - errors: Number of errors encountered

        CRITICAL:
        - This MUST NOT raise exceptions
        - All errors must be caught and logged
        - Partial reconciliation is acceptable
        - Missing backend is acceptable (returns empty stats)
        """
        try:
            # Initialize statistics
            stats = {
                "cameras_processed": 0,
                "subscriptions_added": 0,
                "subscriptions_removed": 0,
                "subscriptions_updated": 0,
                "errors": 0,
            }

            # Fetch desired assignments from backend
            logger.info("Starting reconciliation cycle (Phase 8.2)")
            desired_assignments = await self.assignment_client.fetch_all_assignments()

            if not desired_assignments:
                logger.info(
                    "No enabled assignments from backend, reconciliation complete "
                    "(Phase 8.2)"
                )
                return stats

            # Group assignments by camera_id
            # Dict[camera_id, List[assignment]]
            assignments_by_camera: Dict[str, List[Dict[str, Any]]] = {}

            for assignment in desired_assignments:
                camera_id = assignment.get("camera_id")
                if not camera_id:
                    logger.warning(
                        f"Assignment missing camera_id, skipping (Phase 8.2): {assignment}"
                    )
                    stats["errors"] += 1
                    continue

                # Convert UUID to string if needed
                camera_id_str = str(camera_id)

                if camera_id_str not in assignments_by_camera:
                    assignments_by_camera[camera_id_str] = []

                assignments_by_camera[camera_id_str].append(assignment)

            # Reconcile each camera
            for camera_id, camera_assignments in assignments_by_camera.items():
                try:
                    camera_stats = await self._reconcile_camera(
                        camera_id, camera_assignments
                    )

                    # Aggregate statistics
                    stats["cameras_processed"] += 1
                    stats["subscriptions_added"] += camera_stats.get("added", 0)
                    stats["subscriptions_removed"] += camera_stats.get("removed", 0)
                    stats["subscriptions_updated"] += camera_stats.get("updated", 0)
                    stats["errors"] += camera_stats.get("errors", 0)

                except Exception as e:
                    # Camera reconciliation failed entirely
                    logger.error(
                        f"Failed to reconcile camera {camera_id} (Phase 8.2): {e}"
                    )
                    stats["errors"] += 1

            logger.info(
                f"Reconciliation cycle complete (Phase 8.2): "
                f"{stats['cameras_processed']} cameras, "
                f"+{stats['subscriptions_added']} "
                f"-{stats['subscriptions_removed']} "
                f"~{stats['subscriptions_updated']} subscriptions, "
                f"{stats['errors']} errors"
            )

            return stats

        except Exception as e:
            # Top-level failure (should not happen if we catch everything)
            logger.error(f"Unexpected reconciliation failure (Phase 8.2): {e}")
            return {
                "cameras_processed": 0,
                "subscriptions_added": 0,
                "subscriptions_removed": 0,
                "subscriptions_updated": 0,
                "errors": 1,
            }

    async def _reconcile_camera(
        self,
        camera_id: str,
        desired_assignments: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Reconcile subscriptions for a single camera.

        Args:
            camera_id: Camera UUID string
            desired_assignments: List of desired assignments for this camera

        Returns:
            Statistics dictionary:
            - added: Number of subscriptions created
            - removed: Number of subscriptions deleted
            - updated: Number of subscriptions modified
            - errors: Number of errors

        CRITICAL: This MUST NOT raise exceptions.
        All errors must be caught and logged.
        """
        stats = {"added": 0, "removed": 0, "updated": 0, "errors": 0}

        try:
            # Get or create StreamAgent for this camera
            agent = self.agent_registry.get_or_create_agent(camera_id)

            # Start agent if not already running
            # Phase 8.2: Agents are started on-demand during reconciliation
            if agent.state.value == "CREATED":
                try:
                    agent.start()
                    logger.info(f"Started StreamAgent for camera {camera_id} (Phase 8.2)")
                except Exception as e:
                    logger.error(
                        f"Failed to start StreamAgent for camera {camera_id} (Phase 8.2): {e}"
                    )
                    stats["errors"] += 1
                    return stats

            # Get current subscriptions
            current_subscriptions = agent.list_subscriptions()
            current_model_ids = {sub.model_id for sub in current_subscriptions}

            # Get desired model IDs
            desired_model_ids = set()
            desired_configs: Dict[str, Dict[str, Any]] = {}

            for assignment in desired_assignments:
                model_id = assignment.get("model_id")
                if not model_id:
                    logger.warning(
                        f"Assignment missing model_id for camera {camera_id}, skipping (Phase 8.2)"
                    )
                    stats["errors"] += 1
                    continue

                desired_model_ids.add(model_id)

                # Build subscription config from assignment
                config = self._build_subscription_config(assignment)
                desired_configs[model_id] = config

            # Determine reconciliation actions
            models_to_add = desired_model_ids - current_model_ids
            models_to_remove = current_model_ids - desired_model_ids
            models_to_check_update = desired_model_ids & current_model_ids

            # Add missing subscriptions
            for model_id in models_to_add:
                try:
                    config = desired_configs.get(model_id, {})
                    agent.add_subscription(model_id, config)

                    logger.info(
                        f"Added subscription: camera={camera_id} model={model_id} "
                        f"config={config} (Phase 8.2)"
                    )
                    stats["added"] += 1

                except Exception as e:
                    logger.error(
                        f"Failed to add subscription: camera={camera_id} model={model_id} "
                        f"(Phase 8.2): {e}"
                    )
                    stats["errors"] += 1

            # Remove obsolete subscriptions
            for model_id in models_to_remove:
                try:
                    agent.remove_subscription(model_id)

                    logger.info(
                        f"Removed subscription: camera={camera_id} model={model_id} "
                        f"(Phase 8.2)"
                    )
                    stats["removed"] += 1

                except Exception as e:
                    logger.error(
                        f"Failed to remove subscription: camera={camera_id} model={model_id} "
                        f"(Phase 8.2): {e}"
                    )
                    stats["errors"] += 1

            # Update existing subscriptions if config changed
            for model_id in models_to_check_update:
                try:
                    subscription = agent.get_subscription(model_id)
                    if subscription is None:
                        continue

                    desired_config = desired_configs.get(model_id, {})
                    current_config = subscription.config

                    # Check if config changed
                    if self._config_changed(current_config, desired_config):
                        # Phase 8.2: Config update requires remove + add
                        # Subscription.config is not mutable after creation
                        agent.remove_subscription(model_id)
                        agent.add_subscription(model_id, desired_config)

                        logger.info(
                            f"Updated subscription: camera={camera_id} model={model_id} "
                            f"old_config={current_config} new_config={desired_config} (Phase 8.2)"
                        )
                        stats["updated"] += 1

                except Exception as e:
                    logger.error(
                        f"Failed to update subscription: camera={camera_id} model={model_id} "
                        f"(Phase 8.2): {e}"
                    )
                    stats["errors"] += 1

            return stats

        except Exception as e:
            logger.error(
                f"Unexpected error reconciling camera {camera_id} (Phase 8.2): {e}"
            )
            stats["errors"] += 1
            return stats

    def _build_subscription_config(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build StreamAgent subscription config from backend assignment.

        Args:
            assignment: Assignment dict from backend API

        Returns:
            Subscription config dict for StreamAgent.add_subscription()

        Phase 8.2 mapping:
        - assignment.desired_fps → config["desired_fps"]
        - assignment.priority → config["priority"]
        - assignment.parameters → config["parameters"]
        """
        config: Dict[str, Any] = {}

        # Map desired_fps (Phase 3.3 FPS scheduling)
        if assignment.get("desired_fps") is not None:
            config["desired_fps"] = assignment["desired_fps"]

        # Map priority (future use)
        if assignment.get("priority") is not None:
            config["priority"] = assignment["priority"]

        # Map model-specific parameters (opaque passthrough)
        if assignment.get("parameters") is not None:
            config["parameters"] = assignment["parameters"]

        return config

    def _config_changed(
        self,
        current_config: Dict[str, Any],
        desired_config: Dict[str, Any]
    ) -> bool:
        """
        Check if subscription config has changed.

        Args:
            current_config: Current subscription config
            desired_config: Desired subscription config

        Returns:
            True if configs differ, False otherwise

        Phase 8.2: Simple dict equality check.
        This may produce false positives (e.g., dict ordering),
        but that's acceptable for best-effort reconciliation.
        """
        return current_config != desired_config
