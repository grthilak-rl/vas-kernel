"""
Phase 4.1 – AI Model IPC & Inference Contract
AI MODEL CONTAINER PACKAGE

This package implements the container-side IPC server skeleton for AI model containers.

PHASE 4.1 DELIVERABLES:
- IPC schema definition (schema.py)
- Unix Domain Socket server (ipc_server.py)
- Stateless inference handler skeleton (inference_handler.py)
- Container orchestration (container.py)

WHAT THIS IS:
- AI model inference runtime (skeleton)
- IPC transport and protocol implementation
- Stateless request/response handling
- Hard boundary contract enforcement

WHAT THIS IS NOT:
- Model onboarding system (Phase 4.2)
- GPU scheduling logic (Phase 4.2)
- Container discovery (Phase 4.2)
- Health monitoring (Phase 4.2)
- Integration with Ruth AI Core (Phase 4.2)

PHASE 4.1 SUCCESS CRITERIA:
- IPC contract is explicit and enforced
- Containers are stateless per request
- One container serves many cameras
- No coupling to VAS internals exists
- No scheduling or orchestration logic leaks into containers
"""

from .schema import InferenceRequest, InferenceResponse, Detection
from .ipc_server import IPCServer
from .inference_handler import InferenceHandler

__all__ = [
    "InferenceRequest",
    "InferenceResponse",
    "Detection",
    "IPCServer",
    "InferenceHandler",
]

__version__ = "0.1.0-phase4.1"
