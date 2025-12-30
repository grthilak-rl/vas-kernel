"""
Phase 3.1 – Stream Agent Internal State Model
Phase 3.2 – Subscription Model & Frame Binding

This module defines the StreamAgent abstraction.

PHASE 3.1 SCOPE:
- StreamAgent is a pure state holder
- One agent per camera (stream_agent_id == camera_id)
- No execution logic, no side effects
- No frame access, no scheduling, no routing

PHASE 3.2 SCOPE:
- Subscription management (add/remove/list)
- Logical frame source binding (camera_id reference only)
- No frame reads, no scheduling, no execution

WHAT THIS IS NOT:
- Not a thread or process
- Not a background worker
- Not an event loop
- Not integrated with VAS Kernel yet
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .subscription import Subscription
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
    - No scheduling logic (Phase 3.3)
    - No model execution
    - No I/O or network calls
    - No side effects

    PHASE 3.2 ADDITIONS:
    - Subscription management (pure state only)
    - Logical frame source binding (reference only)
    """

    def __init__(self, camera_id: str, frame_source_path: Optional[str] = None):
        """
        Initialize a StreamAgent for the given camera.

        Args:
            camera_id: Unique identifier for the camera stream.
                      stream_agent_id == camera_id by design.
            frame_source_path: Optional logical path to frame export source.
                              This is a reference only - NO frame access occurs.
                              Example: "/dev/shm/vas_frames_camera_1" (Phase 2 export path)

        State after construction:
            - state = CREATED
            - subscriptions = empty dict
            - created_at = current timestamp
            - frame_source_path = logical reference (if provided)
        """
        # Core identity: stream_agent_id == camera_id
        self.camera_id: str = camera_id

        # Lifecycle state
        self.state: AgentState = AgentState.CREATED

        # Phase 3.2: Logical frame source binding
        # This is a REFERENCE ONLY - no file access, no memory mapping
        # Future phases will use this to know where frames come from
        self.frame_source_path: Optional[str] = frame_source_path

        # Phase 3.2: Subscription storage
        # Dict[model_id, Subscription] for O(1) lookup
        self._subscriptions: Dict[str, Subscription] = {}

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

    def add_subscription(self, model_id: str, config: Optional[Dict[str, Any]] = None) -> Subscription:
        """
        Add a model subscription to this camera stream.

        Phase 3.2: Pure state management only.
        This method does NOT:
        - Start model execution
        - Allocate resources
        - Open connections
        - Begin frame dispatch

        Args:
            model_id: Unique identifier for the AI model
            config: Optional configuration dict (e.g., desired_fps for Phase 3.3)

        Returns:
            The created Subscription object

        Raises:
            ValueError: If model_id is empty or subscription already exists
        """
        if not model_id:
            raise ValueError("model_id must be non-empty")

        if model_id in self._subscriptions:
            raise ValueError(
                f"Subscription for model_id={model_id!r} already exists on camera {self.camera_id!r}"
            )

        # Create subscription (pure state, no side effects)
        subscription = Subscription(
            model_id=model_id,
            config=config or {}
        )

        # Store in subscriptions dict
        self._subscriptions[model_id] = subscription

        return subscription

    def remove_subscription(self, model_id: str) -> None:
        """
        Remove a model subscription from this camera stream.

        Phase 3.2: Immediate removal, no draining.
        This method does NOT:
        - Wait for in-flight work
        - Stop model execution (models managed externally)
        - Clean up resources (there are none in Phase 3.2)

        Args:
            model_id: Unique identifier for the AI model

        Raises:
            KeyError: If subscription does not exist
        """
        if model_id not in self._subscriptions:
            raise KeyError(
                f"No subscription for model_id={model_id!r} on camera {self.camera_id!r}"
            )

        # Remove subscription (immediate, no draining)
        del self._subscriptions[model_id]

    def list_subscriptions(self) -> List[Subscription]:
        """
        List all active subscriptions for this camera.

        Returns:
            List of Subscription objects (read-only view)
        """
        return list(self._subscriptions.values())

    def get_subscription(self, model_id: str) -> Optional[Subscription]:
        """
        Get a specific subscription by model_id.

        Args:
            model_id: Unique identifier for the AI model

        Returns:
            Subscription object if found, None otherwise
        """
        return self._subscriptions.get(model_id)

    @property
    def subscription_count(self) -> int:
        """Number of active subscriptions."""
        return len(self._subscriptions)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StreamAgent(camera_id={self.camera_id!r}, "
            f"state={self.state.value}, "
            f"subscriptions={self.subscription_count}, "
            f"frame_source={self.frame_source_path!r})"
        )
