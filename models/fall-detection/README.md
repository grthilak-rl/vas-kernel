# Fall Detection Model Container

**Phase 4.4 Example**

This is an example model container demonstrating how to use the Ruth AI Model Runtime Base Image.

## Overview

This container:
- Extends `ruth-ai/model-runtime:0.1.0`
- Installs PyTorch as a model-specific dependency
- Implements a fall detection model
- Uses the `ai_model_container` package from the base image
- Does NOT reference VAS source code

## Building

```bash
# First, build the runtime base image
cd ../runtime-base-image
./build.sh

# Then build this model container
cd ../models/fall-detection
docker build -t ruth-ai/fall-detection:1.0.0 .
```

## Running

```bash
docker run \
  --name fall-detection \
  -v /dev/shm:/dev/shm \
  -v /tmp:/tmp \
  ruth-ai/fall-detection:1.0.0
```

## File Structure

```
fall-detection/
├── Dockerfile              # Extends ruth-ai/model-runtime:0.1.0
├── fall_detection_model.py # Model implementation
├── model.yaml              # Model configuration
└── README.md               # This file
```

## Key Points

### Uses Base Image

```dockerfile
FROM ruth-ai/model-runtime:0.1.0
```

The base image provides:
- `ai_model_container` package
- Python 3.9 runtime
- NumPy, OpenCV, PyYAML

### Model-Specific Dependencies Only

```dockerfile
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchvision==0.15.2
```

Only install what's specific to this model.

### Imports from Base Image

```python
from ai_model_container import (
    IPCServer,
    InferenceRequest,
    InferenceResponse,
    Detection,
    FrameReader,
    NV12Preprocessor,
)
```

No VAS source code references.

### Self-Contained

All model-specific code is in this container:
- Model weights (when available)
- Model implementation
- Configuration

## Phase 4.4 Compliance

This example demonstrates:

- [x] Extends the runtime base image
- [x] No ai_model_container vendoring
- [x] No VAS source directory references
- [x] Thin, focused Dockerfile
- [x] CPU-first (GPU optional)
- [x] Proper use of IPC infrastructure

## Customization

To create your own model container:

1. Copy this directory structure
2. Replace `fall_detection_model.py` with your model
3. Update `model.yaml` with your model config
4. Add model weights to `weights/` directory
5. Update Dockerfile dependencies
6. Build and run

## Testing

Test the container in isolation:

```bash
# Terminal 1: Start container
docker run --rm \
  -v /dev/shm:/dev/shm \
  -v /tmp:/tmp \
  ruth-ai/fall-detection:1.0.0

# Terminal 2: Send test request (using example client from VAS)
python3 -m ai_model_container.example_client
```

## Production Deployment

In production, this container is managed by Ruth AI Core:
- Ruth AI Core discovers the model
- Ruth AI Core starts/stops the container
- Ruth AI Core sends inference requests via Unix Domain Socket
- Container processes requests and returns detections

The model container:
- Does NOT interact with VAS Kernel
- Does NOT manage its own lifecycle
- Does NOT know about cameras or streams
- Only processes inference requests

## Troubleshooting

### Import errors

Ensure the base image is built:
```bash
cd ../../runtime-base-image
./build.sh
```

### Socket connection errors

Check that `/tmp` is mounted:
```bash
docker run --rm -v /tmp:/tmp ruth-ai/fall-detection:1.0.0
```

### GPU not detected

For GPU support, use `nvidia-docker`:
```bash
docker run --gpus all -v /dev/shm:/dev/shm -v /tmp:/tmp ruth-ai/fall-detection:1.0.0
```
