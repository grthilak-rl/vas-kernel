"""
Phase 4.1 – AI Model IPC & Inference Contract (FROZEN)
Phase 4.2.1 – Real Model Loading & GPU Initialization (COMPLETED)
Phase 4.2.2 – Frame Access, Preprocessing & Real Inference Execution (COMPLETED)

AI MODEL CONTAINER PACKAGE

This package implements AI model containers with real inference capabilities.

PHASE 4.1 DELIVERABLES (FROZEN):
- IPC schema definition (schema.py)
- Unix Domain Socket server (ipc_server.py)
- Stateless inference handler (inference_handler.py)
- Container orchestration (container.py)

PHASE 4.2.1 DELIVERABLES (COMPLETED):
- Real model loading (PyTorch, ONNX)
- GPU detection and initialization
- CPU fallback support
- Thread-safe model inference

PHASE 4.2.2 DELIVERABLES (COMPLETED):
- READ-ONLY shared memory frame access (frame_reader.py)
- NV12 format preprocessing
- Real model inference on actual frames
- Model-specific post-processing

WHAT THIS IS:
- AI model inference runtime (with real models and frames)
- IPC transport and protocol implementation
- Stateless request/response handling
- GPU-accelerated or CPU-fallback inference
- Real frame consumer and detector

WHAT THIS IS NOT:
- Model onboarding system (Phase 4.2.3+)
- Container discovery (Phase 4.2.3+)
- Health monitoring (Phase 4.2.3+)
- Integration with Ruth AI Core (Phase 4.2.3+)

SUCCESS CRITERIA (ALL MET):
- ✅ IPC contract is explicit and enforced
- ✅ Containers are stateless per request
- ✅ One container serves many cameras
- ✅ No coupling to VAS internals exists
- ✅ No scheduling or orchestration logic leaks into containers
- ✅ Real models loaded and executed
- ✅ Real frames accessed (READ-ONLY) and processed
- ✅ Failures remain isolated
"""

from .schema import InferenceRequest, InferenceResponse, Detection
from .ipc_server import IPCServer
from .inference_handler import InferenceHandler
from .frame_reader import FrameReader, NV12Preprocessor

__all__ = [
    "InferenceRequest",
    "InferenceResponse",
    "Detection",
    "IPCServer",
    "InferenceHandler",
    "FrameReader",
    "NV12Preprocessor",
]

__version__ = "0.3.0-phase4.2.2"
