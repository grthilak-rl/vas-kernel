"""
Phase 3.2 – Subscription Model & Frame Binding
Phase 7 – Observability & Operational Controls

This module defines the Subscription data model for Ruth AI Core.

PHASE 3.2 SCOPE:
- Pure subscription state (no execution)
- Subscription identity: (camera_id, model_id)
- No frame access, no scheduling, no inference

PHASE 7 SCOPE:
- Read-only metrics tracking (non-blocking, best-effort)
- Per-subscription dispatch and drop counters
- Metrics never affect dispatch logic
- Silent failure on metrics errors

WHAT THIS IS NOT:
- Not an execution context
- Not a worker or thread
- Not connected to models yet
- Not processing frames
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Subscription:
    """
    Represents one AI model's subscription to a camera stream.

    A subscription is pure state that declares:
    "Model X wants frames from Camera Y"

    IDENTITY: (camera_id, model_id) uniquely identifies a subscription

    PHASE 3.2 CONSTRAINTS:
    - No frame access
    - No scheduling logic
    - No model execution
    - No network calls
    - No side effects

    Future phases will use this state to:
    - Enforce FPS limits (Phase 3.3)
    - Dispatch frames to models (Phase 3.4)
    - Collect inference results (Phase 3.5)
    """

    # Subscription identity
    model_id: str

    # Optional configuration placeholder
    # Phase 3.3 will use this for desired_fps
    # Phase 3.4+ may add model endpoint references
    config: Dict[str, Any] = field(default_factory=dict)

    # Lifecycle metadata (inert for Phase 3.2)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Scheduling state placeholders (inert for Phase 3.2)
    # Phase 3.3 will populate these fields
    last_dispatched_frame_id: Optional[int] = None
    last_dispatch_timestamp: Optional[datetime] = None

    # Subscription status (active by default)
    active: bool = True

    # Phase 7: Observability metrics (best-effort, non-blocking)
    # These counters track dispatch decisions for operational visibility.
    # IMPORTANT: Metrics MUST NOT affect dispatch logic or inference flow.
    # All metric updates must be wrapped in try/except and silently fail.
    _dispatch_count: int = field(default=0, init=False, repr=False)
    _drop_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        """Validate subscription on creation."""
        if not self.model_id or not isinstance(self.model_id, str):
            raise ValueError("model_id must be a non-empty string")

        if not isinstance(self.config, dict):
            raise ValueError("config must be a dictionary")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Subscription(model_id={self.model_id!r}, "
            f"active={self.active}, "
            f"config={self.config})"
        )

    def __eq__(self, other) -> bool:
        """Equality based on model_id only (unique per camera)."""
        if not isinstance(other, Subscription):
            return False
        return self.model_id == other.model_id

    def __hash__(self) -> int:
        """Hash based on model_id for set/dict usage."""
        return hash(self.model_id)

    # Phase 7: Observability metric accessors
    # These methods provide read-only access to metrics for operational visibility.

    def _increment_dispatch_count(self) -> None:
        """
        Phase 7: Increment dispatch counter (best-effort, non-blocking).

        This is called by StreamAgent.record_dispatch() after a successful
        dispatch decision.

        CRITICAL: This MUST NOT raise exceptions or affect dispatch logic.
        All errors must be silently ignored.
        """
        try:
            self._dispatch_count += 1
        except Exception:
            # Phase 7: Silent failure - metrics errors must not propagate
            pass

    def _increment_drop_count(self) -> None:
        """
        Phase 7: Increment drop counter (best-effort, non-blocking).

        This is called by StreamAgent when should_dispatch() returns False
        (frame skipped).

        CRITICAL: This MUST NOT raise exceptions or affect dispatch logic.
        All errors must be silently ignored.
        """
        try:
            self._drop_count += 1
        except Exception:
            # Phase 7: Silent failure - metrics errors must not propagate
            pass

    def get_metrics(self) -> Dict[str, Any]:
        """
        Phase 7: Get read-only metrics for this subscription.

        Returns:
            Dictionary containing:
            - dispatch_count: Total frames dispatched
            - drop_count: Total frames dropped (skipped)
            - last_dispatch_time: Timestamp of last successful dispatch (or None)
            - last_dispatched_frame_id: Frame ID of last dispatch (or None)

        CRITICAL: This is read-only and best-effort.
        Missing or stale metrics are acceptable.
        Errors must be silently handled.
        """
        try:
            return {
                "dispatch_count": self._dispatch_count,
                "drop_count": self._drop_count,
                "last_dispatch_time": self.last_dispatch_timestamp.isoformat() if self.last_dispatch_timestamp else None,
                "last_dispatched_frame_id": self.last_dispatched_frame_id,
            }
        except Exception:
            # Phase 7: Silent failure - return empty metrics on error
            return {
                "dispatch_count": 0,
                "drop_count": 0,
                "last_dispatch_time": None,
                "last_dispatched_frame_id": None,
            }
