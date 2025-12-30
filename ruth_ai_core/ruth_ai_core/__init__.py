"""
Ruth AI Core Service

Phase 3.1 – Stream Agent Internal State Model

This package defines the core abstractions for Ruth AI Core,
an independent AI orchestration service that consumes frames
from VAS Kernel without modifying video pipelines.

PHASE 3.1 EXPORTS:
- AgentState: Lifecycle state enum
- StreamAgent: Pure state holder for one camera

PHASE 3.1 CONSTRAINTS:
- No execution logic
- No integration with VAS Kernel
- No frame processing
- No scheduling
- No networking

This is state modeling only.
"""

from .agent import StreamAgent
from .types import AgentState

__all__ = [
    "StreamAgent",
    "AgentState",
]

__version__ = "0.1.0-phase3.1"
