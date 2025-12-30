"""
Phase 3.1 – Stream Agent Internal State Model

This module defines the StreamAgent abstraction.

PHASE 3.1 SCOPE:
- StreamAgent is a pure state holder
- One agent per camera (stream_agent_id == camera_id)
- No execution logic, no side effects
- No frame access, no scheduling, no routing

WHAT THIS IS NOT:
- Not a thread or process
- Not a background worker
- Not an event loop
- Not integrated with VAS Kernel yet
"""

from datetime import datetime
from typing import List, Optional

from .types import AgentState


class StreamAgent:
    """
    Logical orchestration unit for one camera stream.

    A StreamAgent represents the AI-side coordination state for a single camera.
    It exists purely to hold state and does not execute any logic.

    CARDINALITY: Exactly one StreamAgent per camera.
    IDENTITY: stream_agent_id == camera_id

    LIFECYCLE:
    - Created in CREATED state
    - Transitioned to RUNNING via start()
    - Transitioned to STOPPED via stop()

    CONSTRAINTS:
    - No frame storage
    - No frame processing
    - No scheduling logic
    - No model execution
    - No I/O or network calls
    - No side effects

    This is Phase 3.1 only. Subscriptions are placeholders.
    Frame routing and FPS scheduling belong to later phases.
    """

    def __init__(self, camera_id: str):
        """
        Initialize a StreamAgent for the given camera.

        Args:
            camera_id: Unique identifier for the camera stream.
                      stream_agent_id == camera_id by design.

        State after construction:
            - state = CREATED
            - subscriptions = empty list (placeholder)
            - created_at = current timestamp
        """
        # Core identity: stream_agent_id == camera_id
        self.camera_id: str = camera_id

        # Lifecycle state
        self.state: AgentState = AgentState.CREATED

        # Subscription placeholder (empty for Phase 3.1)
        # Phase 3.2 will define subscription structure
        self.subscriptions: List = []

        # Inert metadata (no logic attached)
        self.created_at: datetime = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None

        # Optional counters for future phases (inert for now)
        self._frame_counter: int = 0
        self._dispatch_counter: int = 0

    def start(self) -> None:
        """
        Transition agent from CREATED to RUNNING.

        This method does NOT:
        - Start threads
        - Open connections
        - Allocate resources
        - Pull frames
        - Execute any background logic

        It only changes internal state.

        Raises:
            RuntimeError: If agent is not in CREATED state
        """
        if self.state != AgentState.CREATED:
            raise RuntimeError(
                f"Cannot start agent in state {self.state.value}. "
                f"Expected {AgentState.CREATED.value}."
            )

        self.state = AgentState.RUNNING
        self.started_at = datetime.utcnow()

    def stop(self) -> None:
        """
        Transition agent from RUNNING to STOPPED.

        This method does NOT:
        - Wait for in-flight work
        - Drain queues (there are no queues)
        - Clean up resources (there are no resources)
        - Notify external systems

        It only changes internal state.

        Raises:
            RuntimeError: If agent is not in RUNNING state
        """
        if self.state != AgentState.RUNNING:
            raise RuntimeError(
                f"Cannot stop agent in state {self.state.value}. "
                f"Expected {AgentState.RUNNING.value}."
            )

        self.state = AgentState.STOPPED
        self.stopped_at = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StreamAgent(camera_id={self.camera_id!r}, "
            f"state={self.state.value}, "
            f"subscriptions={len(self.subscriptions)})"
        )
