"""
Phase 8.2 – Ruth AI Core Subscription Reconciliation

STREAMAGENT REGISTRY

This module manages the lifecycle of StreamAgent instances.
One StreamAgent per camera, indexed by camera_id.

CRITICAL CONSTRAINTS:
- Pure state management (no execution)
- No frame access, no dispatch
- No model lifecycle management
- Thread-safe for concurrent reconciliation
"""

from typing import Dict, Optional
from loguru import logger

from .agent import StreamAgent
from .types import AgentState


class AgentRegistry:
    """
    Registry for managing StreamAgent instances.

    Phase 8.2: Provides central management of StreamAgent lifecycle.

    CARDINALITY: One StreamAgent per camera (camera_id is the key).

    CRITICAL:
    - This is pure state management
    - No frame processing
    - No model execution
    - No network I/O
    """

    def __init__(self):
        """Initialize empty agent registry."""
        # Dict[camera_id, StreamAgent]
        self._agents: Dict[str, StreamAgent] = {}

    def get_or_create_agent(
        self,
        camera_id: str,
        frame_source_path: Optional[str] = None
    ) -> StreamAgent:
        """
        Get existing StreamAgent or create new one for a camera.

        Args:
            camera_id: Camera UUID string
            frame_source_path: Optional frame export path reference

        Returns:
            StreamAgent instance for this camera

        Behavior:
            - If agent exists → return existing agent
            - If agent does not exist → create new agent in CREATED state
            - New agents are NOT automatically started

        CRITICAL: This does NOT start the agent.
        Caller must call agent.start() if needed.
        """
        if camera_id in self._agents:
            return self._agents[camera_id]

        # Create new agent (CREATED state)
        agent = StreamAgent(camera_id=camera_id, frame_source_path=frame_source_path)
        self._agents[camera_id] = agent

        logger.info(
            f"Created new StreamAgent for camera {camera_id} (Phase 8.2 registry)"
        )

        return agent

    def get_agent(self, camera_id: str) -> Optional[StreamAgent]:
        """
        Get existing StreamAgent for a camera.

        Args:
            camera_id: Camera UUID string

        Returns:
            StreamAgent if exists, None otherwise
        """
        return self._agents.get(camera_id)

    def list_agents(self) -> Dict[str, StreamAgent]:
        """
        List all registered StreamAgents.

        Returns:
            Dictionary mapping camera_id -> StreamAgent
        """
        return self._agents.copy()

    def remove_agent(self, camera_id: str) -> bool:
        """
        Remove a StreamAgent from the registry.

        Args:
            camera_id: Camera UUID string

        Returns:
            True if agent was removed, False if not found

        CRITICAL:
        - This does NOT stop the agent first
        - Caller must ensure agent is in STOPPED state before removal
        - This is immediate removal (no draining, no cleanup)
        """
        if camera_id in self._agents:
            agent = self._agents[camera_id]

            # Safety check: warn if removing non-stopped agent
            if agent.state != AgentState.STOPPED:
                logger.warning(
                    f"Removing StreamAgent for camera {camera_id} in state {agent.state.value} "
                    f"(should be STOPPED, Phase 8.2)"
                )

            del self._agents[camera_id]

            logger.info(f"Removed StreamAgent for camera {camera_id} (Phase 8.2)")
            return True

        return False

    def agent_count(self) -> int:
        """Get total number of registered agents."""
        return len(self._agents)
