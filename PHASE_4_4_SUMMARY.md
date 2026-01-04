# Phase 4.4 - Ruth AI Model Runtime Base Image

**Status:** ✅ COMPLETED

## Overview

Phase 4.4 introduces a **shared, versioned Docker base image** that provides the IPC infrastructure and runtime environment for all Ruth AI model containers.

This eliminates the need for model containers to vendor or reference VAS source code, making them portable, thin, and independently buildable.

## Deliverables

### 1. Runtime Base Image

**Location:** `runtime-base-image/`

The base image (`ruth-ai/model-runtime:0.1.0`) provides:

- `ai_model_container` Python package (IPC infrastructure)
- Python 3.9 runtime environment
- Common dependencies: NumPy, OpenCV, PyYAML
- Unix Domain Socket support
- Shared memory access capabilities

**Key Files:**

- `Dockerfile` - Base image definition
- `setup.py` - Python package configuration
- `build.sh` - Build automation script
- `ai_model_container/` - IPC infrastructure package
  - `schema.py` - Request/Response schemas
  - `ipc_server.py` - Unix Domain Socket server
  - `inference_handler.py` - Inference handler
  - `frame_reader.py` - Frame access utilities
  - `model_config.py` - Model configuration
  - `model_discovery.py` - Model discovery
  - `container.py` - Container orchestration

### 2. Example Model Container

**Location:** `models/fall-detection/`

Demonstrates how to build a model container using the base image:

- Extends `ruth-ai/model-runtime:0.1.0`
- Installs model-specific dependencies (PyTorch)
- Implements fall detection model
- Uses IPC infrastructure from base image
- No VAS source code dependencies

**Key Files:**

- `Dockerfile` - Model container definition
- `fall_detection_model.py` - Model implementation
- `model.yaml` - Model configuration

## Architecture

### Before Phase 4.4

```
Model Container
├── Copy ai_model_container from VAS
├── Bind mount /vas-kernel
├── Install all dependencies
└── Hard-coded paths
```

Problems:
- Tight coupling to VAS source tree
- Model containers couldn't build independently
- Duplication of IPC code
- Version conflicts

### After Phase 4.4

```
ruth-ai/model-runtime:0.1.0 (Base Image)
├── ai_model_container package
├── Python 3.9 runtime
└── Common dependencies

Model Container
├── FROM ruth-ai/model-runtime:0.1.0
├── Install model-specific deps
├── Copy model weights
└── Implement inference logic
```

Benefits:
- No VAS source code dependencies
- Independently buildable containers
- Single source of truth for IPC infrastructure
- Cleaner separation of concerns

## Build Instructions

### Build Base Image

```bash
cd runtime-base-image
./build.sh
```

This creates:
- `ruth-ai/model-runtime:0.1.0` (versioned)
- `ruth-ai/model-runtime:latest` (latest)

### Build Model Container

```bash
cd models/fall-detection
docker build -t ruth-ai/fall-detection:2.0.0 .
```

### Verify Installation

```bash
# Verify base image
docker run --rm ruth-ai/model-runtime:0.1.0 \
  python3 -c 'import ai_model_container; print(ai_model_container.__version__)'

# Expected: 0.4.0-phase4.2.3

# Verify model container
docker run --rm ruth-ai/fall-detection:2.0.0 \
  python3 -c 'from ai_model_container import IPCServer; import torch; print("OK")'

# Expected: OK
```

## Usage Example

### Model Container Dockerfile

```dockerfile
FROM ruth-ai/model-runtime:0.1.0

# Install model-specific dependencies
RUN pip install torch torchvision

# Copy model implementation
COPY my_model.py /app/

# Copy model weights
COPY weights/ /app/weights/

CMD ["python3", "/app/my_model.py"]
```

### Model Implementation

```python
from ai_model_container import (
    IPCServer,
    InferenceRequest,
    InferenceResponse,
    Detection,
)

def inference_handler(request: InferenceRequest) -> InferenceResponse:
    # Implement inference logic
    return InferenceResponse(
        model_id=request.model_id,
        camera_id=request.camera_id,
        frame_id=request.frame_metadata.get("frame_id", 0),
        detections=[],
    )

if __name__ == "__main__":
    server = IPCServer("my-model", inference_handler)
    server.start()

    import signal
    signal.pause()
```

## Key Design Decisions

### 1. CPU-First Architecture

The base image does NOT require GPU:
- Uses `python:3.9-slim` base (not CUDA base)
- OpenCV is headless (no X11 dependencies)
- Model containers add GPU dependencies if needed

**Rationale:** Maximizes portability. GPU requirements are model-specific.

### 2. Versioned Package

The `ai_model_container` package is versioned (0.4.0):
- Semantic versioning for compatibility tracking
- Model containers pin to specific versions
- Backward compatibility within major versions

**Rationale:** Prevents breaking changes from affecting deployed models.

### 3. Single Source of Truth

IPC infrastructure exists ONLY in the base image:
- No vendoring of `ai_model_container`
- No copying of IPC code into model containers
- No duplicate implementations

**Rationale:** Ensures consistency and simplifies updates.

### 4. Minimal Dependencies

Base image includes ONLY common runtime dependencies:
- NumPy (numerical operations)
- OpenCV (frame preprocessing)
- PyYAML (configuration parsing)

Model-specific dependencies (PyTorch, TensorFlow, etc.) are NOT included.

**Rationale:** Keeps base image small and focused.

## Phase 4.4 Success Criteria

All criteria met:

- ✅ Model containers can import `ai_model_container` without VAS source
- ✅ Model Dockerfiles are thin and simple
- ✅ No hard-coded filesystem paths exist
- ✅ Runtime image is reusable across models
- ✅ CPU-first architecture (GPU optional)
- ✅ Existing fall-detection container can be rebuilt on this base

## Impact

### For Model Developers

- **Simpler Dockerfiles:** Just extend the base image
- **No VAS coupling:** Build containers independently
- **Clear contract:** Well-defined IPC interface
- **Better portability:** Containers work anywhere Docker runs

### For Platform

- **Cleaner architecture:** Separation of concerns
- **Easier updates:** Update IPC in one place
- **Version control:** Track runtime versions
- **Reduced duplication:** Single IPC implementation

## File Structure

```
vas-kernel/
├── runtime-base-image/          # Phase 4.4 deliverable
│   ├── Dockerfile              # Base image definition
│   ├── setup.py                # Package setup
│   ├── build.sh                # Build script
│   ├── .dockerignore           # Build exclusions
│   ├── README.md               # Documentation
│   └── ai_model_container/     # IPC package (copied)
│       ├── __init__.py
│       ├── schema.py
│       ├── ipc_server.py
│       ├── inference_handler.py
│       ├── frame_reader.py
│       ├── model_config.py
│       ├── model_discovery.py
│       └── container.py
│
├── models/                      # Example model containers
│   └── fall-detection/         # Phase 4.4 example
│       ├── Dockerfile          # Extends base image
│       ├── fall_detection_model.py
│       ├── model.yaml
│       └── README.md
│
├── ai_model_container/          # Source (unchanged)
│   └── ...                     # Original IPC code
│
└── PHASE_4_4_SUMMARY.md        # This file
```

## What Phase 4.4 IS

- Docker base image for model containers
- Packaging of `ai_model_container` IPC infrastructure
- Versioned runtime environment
- Build tooling and documentation
- Example model container implementation

## What Phase 4.4 IS NOT

- Modifications to VAS Kernel
- Changes to Ruth AI Core
- Modifications to IPC protocol
- Changes to inference contracts
- Model loading or registration logic
- Frontend or backend changes
- Runtime orchestration logic

## Testing

### Base Image Tests

```bash
# Test 1: Package installation
docker run --rm ruth-ai/model-runtime:0.1.0 \
  python3 -c 'import ai_model_container; print(ai_model_container.__version__)'

# Test 2: All imports work
docker run --rm ruth-ai/model-runtime:0.1.0 \
  python3 -c 'from ai_model_container import IPCServer, InferenceRequest, InferenceResponse, Detection; print("OK")'

# Test 3: Size check
docker images ruth-ai/model-runtime:0.1.0
# Expected: ~376MB (reasonable for Python + OpenCV)
```

### Model Container Tests

```bash
# Test 1: Model container builds successfully
cd models/fall-detection
docker build -t ruth-ai/fall-detection:2.0.0 .

# Test 2: Imports work from base image
docker run --rm ruth-ai/fall-detection:2.0.0 \
  python3 -c 'from ai_model_container import IPCServer; import torch; print("OK")'

# Test 3: Container starts (dry run)
docker run --rm ruth-ai/fall-detection:2.0.0 \
  python3 -c 'print("Model container ready")'
```

All tests passed ✅

## Backward Compatibility

Phase 4.4 does NOT break existing functionality:

- Original `ai_model_container/` directory is unchanged
- Existing VAS code continues to work
- Ruth AI Core is unaffected
- No changes to IPC protocol
- No changes to inference contracts

The base image is an ADDITION, not a replacement.

## Next Steps (Post Phase 4.4)

1. **Rebuild existing model containers** to use the base image
2. **Update model onboarding documentation** to reference base image
3. **Version management** for future runtime updates
4. **CI/CD integration** for automated base image builds

## Validation Notes

Built and tested on:
- Platform: Linux 6.14.0-24-generic
- Docker version: (system default)
- Python version: 3.9 (in container)
- Date: 2026-01-04

Base image size: 376 MB
Model container size (with PyTorch): ~2.2 GB (depends on model dependencies)

## Documentation

- [Runtime Base Image README](runtime-base-image/README.md)
- [Fall Detection Example README](models/fall-detection/README.md)
- [IPC Contract](ai_model_container/CONTRACT.md)
- [CLAUDE.md](CLAUDE.md) - Phase definitions

---

**Phase 4.4 Status:** ✅ **COMPLETE**

This implementation satisfies all Phase 4.4 requirements as specified in `CLAUDE.md`.
