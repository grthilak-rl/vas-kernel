"""
Phase 4.1 – AI Model IPC & Inference Contract (FROZEN)
Phase 4.2.1 – Real Model Loading & GPU Initialization (COMPLETED)
Phase 4.2.2 – Frame Access, Preprocessing & Real Inference Execution (COMPLETED)
Phase 4.2.3 – Model Onboarding & Discovery (ACTIVE)

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

PHASE 4.2.3 DELIVERABLES (ACTIVE):
- model.yaml parser and validator (model_config.py)
- Filesystem-based model discovery (model_discovery.py)
- GPU requirement enforcement
- Startup-time model availability determination

WHAT THIS IS:
- AI model inference runtime (with real models and frames)
- IPC transport and protocol implementation
- Stateless request/response handling
- GPU-accelerated or CPU-fallback inference
- Real frame consumer and detector
- Model onboarding and discovery system

WHAT THIS IS NOT:
- Health monitoring
- Runtime configuration updates
- Hot-reload mechanism
- Integration with Ruth AI Core (Phase 4.2.4+)

SUCCESS CRITERIA (ALL MET):
- ✅ IPC contract is explicit and enforced
- ✅ Containers are stateless per request
- ✅ One container serves many cameras
- ✅ No coupling to VAS internals exists
- ✅ No scheduling or orchestration logic leaks into containers
- ✅ Real models loaded and executed
- ✅ Real frames accessed (READ-ONLY) and processed
- ✅ Failures remain isolated
- ✅ model.yaml is single source of truth
- ✅ GPU requirements enforced at startup
"""

from .schema import InferenceRequest, InferenceResponse, Detection
from .ipc_server import IPCServer
from .inference_handler import InferenceHandler
from .frame_reader import FrameReader, NV12Preprocessor
from .model_config import ModelConfig
from .model_discovery import ModelDiscovery
from .container import ModelContainer

__all__ = [
    "InferenceRequest",
    "InferenceResponse",
    "Detection",
    "IPCServer",
    "InferenceHandler",
    "FrameReader",
    "NV12Preprocessor",
    "ModelConfig",
    "ModelDiscovery",
    "ModelContainer",
]

__version__ = "0.4.0-phase4.2.3"
