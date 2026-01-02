"""
Phase 3.1 – Stream Agent Internal State Model
Phase 3.2 – Subscription Model & Frame Binding
Phase 3.3 – FPS Scheduling & Frame Selection
Phase 3.4 – Failure & Restart Semantics
Phase 7 – Observability & Operational Controls

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

PHASE 3.3 SCOPE:
- FPS gating decision logic (pure computation)
- Per-subscription frame selection (ALLOW or SKIP)
- No frame access, no dispatch execution, no loops

PHASE 3.4 SCOPE:
- Defensive guards for failure isolation
- Fail-closed behavior for invalid states
- Explicit failure boundaries (no recovery, no retries)

PHASE 7 SCOPE:
- Read-only metrics collection (non-blocking, best-effort)
- Per-subscription FPS and drop counters
- Metrics exposed via get_metrics() (read-only)
- No inference flow modification
- Silent failure on metrics errors

FAILURE SEMANTICS (PHASE 3.4):
- Inactive subscription → frames silently skipped
- Invalid subscription config → fail-closed (skip)
- Frame source missing → StreamAgent idles (no error)
- StreamAgent STOPPED → no dispatch decisions allowed
- Ruth AI Core failure → MUST NOT affect VAS (isolated)

FAILURE SEMANTICS (PHASE 7):
- Metrics are best-effort and lossy
- Metrics errors must be silently ignored
- Missing metrics are acceptable
- Never affect dispatch decisions or inference

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

    PHASE 3.3 ADDITIONS:
    - FPS gating decision logic (should_dispatch)
    - Per-subscription frame selection

    PHASE 3.4 ADDITIONS:
    - Defensive guards for STOPPED state
    - Explicit failure isolation semantics
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
        #
        # Phase 3.4: If frame_source_path is None, StreamAgent idles gracefully.
        # Missing frame source is NOT an error - it simply means no frames available.
        # This preserves failure isolation: frame export failure affects only Ruth AI.
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

    def should_dispatch(
        self,
        subscription: Subscription,
        frame_id: int,
        frame_timestamp: datetime
    ) -> bool:
        """
        Phase 3.3: FPS gating decision logic.
        Phase 7: Non-blocking metrics collection (drop counter).

        Determines whether a frame should be dispatched to a subscription
        based on the subscription's desired_fps constraint.

        This is PURE DECISION LOGIC ONLY:
        - No frame access
        - No frame dispatch
        - No side effects (except best-effort metrics)
        - No state mutation (except best-effort counters)

        FPS ENFORCEMENT RULES:
        - desired_fps is a MAXIMUM (cap, not target)
        - Frames may be skipped freely
        - No catch-up behavior
        - No token buckets
        - No queues

        DECISION ALGORITHM:
        1. If subscription is inactive → SKIP
        2. If desired_fps not configured → ALLOW (unlimited)
        3. If this is the first frame → ALLOW
        4. If sufficient time has elapsed since last dispatch → ALLOW
        5. Otherwise → SKIP

        PHASE 3.4 FAILURE SEMANTICS:
        - If StreamAgent is STOPPED → SKIP (fail-closed)
        - If subscription is inactive → SKIP (fail-closed)
        - If invalid FPS config → SKIP (fail-closed)
        - No recovery, no retries, no logging

        PHASE 7 METRICS:
        - If decision is SKIP → increment drop counter (best-effort)
        - Metrics errors are silently ignored
        - Metrics MUST NOT affect dispatch logic

        Args:
            subscription: The subscription to evaluate
            frame_id: Current frame identifier (monotonic)
            frame_timestamp: Current frame timestamp

        Returns:
            True if frame should be dispatched (ALLOW)
            False if frame should be skipped (SKIP)

        Note:
            This method does NOT update subscription state.
            Caller must call record_dispatch() if dispatch succeeds.
        """
        # Phase 3.4: Defensive guard - STOPPED agents cannot make dispatch decisions
        # This enforces failure isolation: once stopped, agent is inert
        if self.state == AgentState.STOPPED:
            # Phase 7: Track drop (best-effort, silent failure)
            subscription._increment_drop_count()
            return False

        # Fail-closed: inactive subscriptions never receive frames
        if not subscription.active:
            # Phase 7: Track drop (best-effort, silent failure)
            subscription._increment_drop_count()
            return False

        # Get desired_fps from config (default: None = unlimited)
        desired_fps = subscription.config.get("desired_fps")

        # If no FPS limit configured, allow all frames
        if desired_fps is None:
            return True

        # Validate desired_fps (fail-closed on invalid config)
        if not isinstance(desired_fps, (int, float)) or desired_fps <= 0:
            # Phase 7: Track drop (best-effort, silent failure)
            subscription._increment_drop_count()
            return False

        # First frame for this subscription → always allow
        if subscription.last_dispatch_timestamp is None:
            return True

        # Calculate minimum interval between frames (in seconds)
        # desired_fps = frames per second
        # min_interval = 1 / desired_fps
        min_interval_seconds = 1.0 / float(desired_fps)

        # Calculate time elapsed since last dispatch
        elapsed = (frame_timestamp - subscription.last_dispatch_timestamp).total_seconds()

        # Allow dispatch if sufficient time has elapsed
        # Use >= to handle edge cases with exact timing
        should_allow = elapsed >= min_interval_seconds

        # Phase 7: Track drop if frame is skipped (best-effort, silent failure)
        if not should_allow:
            subscription._increment_drop_count()

        return should_allow

    def record_dispatch(
        self,
        subscription: Subscription,
        frame_id: int,
        frame_timestamp: datetime
    ) -> None:
        """
        Phase 3.3: Record that a frame was dispatched to a subscription.
        Phase 7: Non-blocking metrics collection (dispatch counter).

        This method updates the subscription's dispatch state after a
        successful dispatch decision.

        IMPORTANT:
        - This is a STATE UPDATE ONLY
        - No frame access
        - No actual dispatch execution
        - Caller is responsible for actual dispatch (Phase 3.4+)

        PHASE 3.4 FAILURE SEMANTICS:
        - If StreamAgent is STOPPED → silently ignore (no-op)
        - If subscription is inactive → silently ignore (no-op)
        - No exceptions raised, no recovery, no logging

        PHASE 7 METRICS:
        - Increment dispatch counter (best-effort)
        - Metrics errors are silently ignored
        - Metrics MUST NOT affect state updates

        Args:
            subscription: The subscription that received the frame
            frame_id: The dispatched frame identifier
            frame_timestamp: The dispatched frame timestamp
        """
        # Phase 3.4: Defensive guard - STOPPED agents do not update state
        # Fail-closed: silently ignore state updates for stopped agents
        if self.state == AgentState.STOPPED:
            return

        # Phase 3.4: Defensive guard - inactive subscriptions do not update state
        # Fail-closed: silently ignore state updates for inactive subscriptions
        if not subscription.active:
            return

        # Update subscription dispatch state
        subscription.last_dispatched_frame_id = frame_id
        subscription.last_dispatch_timestamp = frame_timestamp

        # Phase 7: Track successful dispatch (best-effort, silent failure)
        subscription._increment_dispatch_count()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Phase 7: Get read-only observability metrics for this StreamAgent.

        Returns per-subscription metrics and agent-level state.

        Returns:
            Dictionary containing:
            - camera_id: The camera identifier
            - state: Current agent state (CREATED, RUNNING, STOPPED)
            - subscriptions: List of per-subscription metrics
            - subscription_count: Total number of subscriptions

        CRITICAL: This is read-only and best-effort.
        Missing or stale metrics are acceptable.
        Errors must be silently handled.
        """
        try:
            subscription_metrics = []
            for model_id, subscription in self._subscriptions.items():
                try:
                    # Get per-subscription metrics (best-effort)
                    sub_metrics = subscription.get_metrics()
                    sub_metrics["model_id"] = model_id
                    sub_metrics["camera_id"] = self.camera_id
                    sub_metrics["active"] = subscription.active
                    subscription_metrics.append(sub_metrics)
                except Exception:
                    # Phase 7: Silent failure for individual subscription metrics
                    pass

            return {
                "camera_id": self.camera_id,
                "state": self.state.value,
                "subscription_count": self.subscription_count,
                "subscriptions": subscription_metrics,
            }
        except Exception:
            # Phase 7: Silent failure - return minimal metrics on error
            return {
                "camera_id": self.camera_id,
                "state": "unknown",
                "subscription_count": 0,
                "subscriptions": [],
            }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"StreamAgent(camera_id={self.camera_id!r}, "
            f"state={self.state.value}, "
            f"subscriptions={self.subscription_count}, "
            f"frame_source={self.frame_source_path!r})"
        )
