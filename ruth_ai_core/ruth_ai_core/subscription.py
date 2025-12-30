"""
Phase 3.2 – Subscription Model & Frame Binding

This module defines the Subscription data model for Ruth AI Core.

PHASE 3.2 SCOPE:
- Pure subscription state (no execution)
- Subscription identity: (camera_id, model_id)
- No frame access, no scheduling, no inference

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
