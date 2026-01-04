# Ruth AI Model Runtime Base Image

**Phase 4.4 Implementation**

This directory contains the base Docker image for all Ruth AI model containers.

## Overview

The runtime base image provides:

- `ai_model_container` package (IPC infrastructure)
- Python 3.9 runtime environment
- Common dependencies (NumPy, OpenCV, PyYAML)
- Unix Domain Socket support
- Shared memory access

## Directory Structure

```
runtime-base-image/
├── Dockerfile           # Base image definition
├── setup.py            # Python package setup
├── build.sh            # Build script
├── .dockerignore       # Build exclusions
├── ai_model_container/ # IPC infrastructure package
│   ├── __init__.py
│   ├── schema.py       # Request/Response schemas
│   ├── ipc_server.py   # Unix Domain Socket server
│   ├── inference_handler.py
│   ├── frame_reader.py # Frame access utilities
│   ├── model_config.py
│   ├── model_discovery.py
│   └── container.py
└── README.md           # This file
```

## Building the Base Image

```bash
# Build with default version (0.1.0)
./build.sh

# Build with specific version
./build.sh 0.2.0
```

This creates two tags:
- `ruth-ai/model-runtime:0.1.0` (versioned)
- `ruth-ai/model-runtime:latest` (latest)

## Using the Base Image

### In a Model Container Dockerfile

```dockerfile
FROM ruth-ai/model-runtime:0.1.0

# Install model-specific dependencies
RUN pip install torch torchvision

# Copy model weights
COPY weights/ /app/weights/

# Copy model implementation
COPY my_model.py /app/

# Set entrypoint
CMD ["python3", "/app/my_model.py"]
```

### Available Python Imports

```python
from ai_model_container import (
    IPCServer,
    InferenceRequest,
    InferenceResponse,
    Detection,
    InferenceHandler,
    FrameReader,
    NV12Preprocessor,
    ModelConfig,
    ModelDiscovery,
    ModelContainer,
)
```

## What Model Containers MUST Do

1. **Extend this base image**
   ```dockerfile
   FROM ruth-ai/model-runtime:0.1.0
   ```

2. **Install model-specific dependencies**
   - PyTorch, ONNX, TensorFlow, etc.
   - Model-specific libraries

3. **Copy model weights**
   - Model files (.pt, .onnx, etc.)
   - Configuration files

4. **Define entrypoint**
   - Python script that starts the IPC server
   - Loads model and handles inference

## What Model Containers MUST NOT Do

1. **Do NOT vendor ai_model_container**
   - Package is provided by base image
   - Do not copy or bundle separately

2. **Do NOT reference VAS source directories**
   - No `/vas-kernel` paths
   - No bind mounts to VAS source

3. **Do NOT modify IPC contracts**
   - Use schemas as-is
   - Do not alter request/response formats

## Example Model Container

See `models/fall-detection/Dockerfile` for a complete example.

### Minimal Example

```dockerfile
# Dockerfile
FROM ruth-ai/model-runtime:0.1.0

RUN pip install torch torchvision

COPY model.py /app/
COPY weights/ /app/weights/

CMD ["python3", "/app/model.py"]
```

```python
# model.py
from ai_model_container import IPCServer, InferenceRequest, InferenceResponse

def inference_handler(request: InferenceRequest) -> InferenceResponse:
    # Load frame, run inference, return detections
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
    signal.pause()  # Keep running
```

## Runtime Requirements

### Mount Points (at runtime)

- `/dev/shm` - Shared memory for frame access
- `/tmp` - Unix Domain Sockets

### Docker Run Example

```bash
docker run \
  --name my-model \
  -v /dev/shm:/dev/shm \
  -v /tmp:/tmp \
  ruth-ai/my-model:latest
```

## Versioning

The runtime base image follows semantic versioning:

- **0.1.0** - Initial Phase 4.4 implementation
- **0.x.x** - Pre-1.0 development versions
- **1.0.0** - Stable release (future)

Model containers should pin to a specific version:

```dockerfile
FROM ruth-ai/model-runtime:0.1.0  # Good - explicit version
```

Not:

```dockerfile
FROM ruth-ai/model-runtime:latest  # Bad - unpredictable
```

## Verification

Verify the base image is built correctly:

```bash
# Check package installation
docker run --rm ruth-ai/model-runtime:0.1.0 \
  python3 -c 'import ai_model_container; print(ai_model_container.__version__)'

# Expected output: 0.4.0-phase4.2.3 (or similar)

# Check available imports
docker run --rm ruth-ai/model-runtime:0.1.0 \
  python3 -c 'from ai_model_container import IPCServer, InferenceRequest, InferenceResponse; print("OK")'

# Expected output: OK
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'ai_model_container'"

- Ensure you're using the base image: `FROM ruth-ai/model-runtime:0.1.0`
- Build the base image first: `./build.sh`

### "Cannot connect to Docker daemon"

- Ensure Docker is running
- Check Docker permissions: `docker ps`

### Build failures

- Check Dockerfile syntax
- Verify all files exist in `ai_model_container/`
- Review build logs for specific errors

## Phase 4.4 Success Criteria

This implementation satisfies Phase 4.4 if:

- [x] Model containers can import `ai_model_container` without VAS source
- [x] Model Dockerfiles are thin and simple
- [x] No hard-coded filesystem paths exist
- [x] Runtime image is reusable across models
- [x] CPU-first architecture (GPU optional)

## What This Is NOT

- Model loading logic (model-specific)
- GPU orchestration (container-local)
- Model discovery (Ruth AI Core responsibility)
- Frontend or backend changes

## Support

For issues or questions:
1. Review Phase 4.4 requirements in `/CLAUDE.md`
2. Check contract specification in `/ai_model_container/CONTRACT.md`
3. Review example implementations in `/models/`
