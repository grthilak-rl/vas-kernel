"""
Ruth AI Core Service

Phase 3.1 – Stream Agent Internal State Model
Phase 3.2 – Subscription Model & Frame Binding
Phase 3.3 – FPS Scheduling & Frame Selection
Phase 3.4 – Failure & Restart Semantics
Phase 8.2 – Ruth AI Core Subscription Reconciliation

This package defines the core abstractions for Ruth AI Core,
an independent AI orchestration service that consumes frames
from VAS Kernel without modifying video pipelines.

PHASE 3.1 EXPORTS:
- AgentState: Lifecycle state enum
- StreamAgent: Pure state holder for one camera

PHASE 3.2 EXPORTS:
- Subscription: Subscription data model

PHASE 3.3 EXPORTS:
- StreamAgent.should_dispatch: FPS gating decision logic
- StreamAgent.record_dispatch: Dispatch state update

PHASE 3.4 ADDITIONS:
- Defensive guards for STOPPED state
- Fail-closed behavior for invalid states
- Explicit failure isolation (no recovery, no retries)

PHASE 8.2 EXPORTS:
- AssignmentClient: Backend API client for fetching assignment intent
- AgentRegistry: StreamAgent lifecycle management
- ReconciliationEngine: Subscription reconciliation logic
- ReconciliationService: Periodic reconciliation service

FAILURE ISOLATION (PHASE 3.4):
- StreamAgent failure affects only that camera
- Subscription failure affects only that model
- Ruth AI Core failure does NOT affect VAS Kernel
- No recovery, no retries, no escalation

CONSTRAINTS:
- Pure decision logic only
- No execution
- No integration with VAS Kernel
- No frame processing
- No frame dispatch
- No networking

This is decision logic only, not execution.
"""

from .agent import StreamAgent
from .subscription import Subscription
from .types import AgentState
from .assignment_client import AssignmentClient
from .agent_registry import AgentRegistry
from .reconciliation import ReconciliationEngine
from .reconciliation_service import ReconciliationService

__all__ = [
    "StreamAgent",
    "AgentState",
    "Subscription",
    "AssignmentClient",
    "AgentRegistry",
    "ReconciliationEngine",
    "ReconciliationService",
]

__version__ = "0.4.0-phase8.2"
