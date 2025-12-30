"""
Ruth AI Core Service

Phase 3.1 – Stream Agent Internal State Model
Phase 3.2 – Subscription Model & Frame Binding

This package defines the core abstractions for Ruth AI Core,
an independent AI orchestration service that consumes frames
from VAS Kernel without modifying video pipelines.

PHASE 3.1 EXPORTS:
- AgentState: Lifecycle state enum
- StreamAgent: Pure state holder for one camera

PHASE 3.2 EXPORTS:
- Subscription: Subscription data model

PHASE 3.2 CONSTRAINTS:
- No execution logic
- No integration with VAS Kernel
- No frame processing
- No scheduling
- No networking

This is state modeling only.
"""

from .agent import StreamAgent
from .subscription import Subscription
from .types import AgentState

__all__ = [
    "StreamAgent",
    "AgentState",
    "Subscription",
]

__version__ = "0.2.0-phase3.2"
