# Quick Start: Building Model Containers with Ruth AI Runtime Base Image

This guide shows you how to create a new AI model container using the Ruth AI Model Runtime Base Image.

## Prerequisites

- Docker installed
- Ruth AI runtime base image built (`ruth-ai/model-runtime:0.1.0`)

## Step 1: Build the Runtime Base Image

If not already built:

```bash
cd runtime-base-image
./build.sh
```

Verify:

```bash
docker images | grep ruth-ai/model-runtime
# Should show: ruth-ai/model-runtime  0.1.0  ...
```

## Step 2: Create Your Model Directory

```bash
mkdir -p models/my-model
cd models/my-model
```

## Step 3: Create Dockerfile

Create `Dockerfile`:

```dockerfile
FROM ruth-ai/model-runtime:0.1.0

# Install model-specific dependencies
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchvision==0.15.2

# Create directories
RUN mkdir -p /app/weights /app/config

# Copy model implementation
COPY my_model.py /app/

# Copy model configuration
COPY model.yaml /app/config/

# Copy model weights (if available)
# COPY weights/ /app/weights/

WORKDIR /app

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s = socket.socket(socket.AF_UNIX); s.connect('/tmp/vas_model_my-model.sock'); s.close()" || exit 1

# Start model container
CMD ["python3", "/app/my_model.py"]
```

## Step 4: Create Model Implementation

Create `my_model.py`:

```python
#!/usr/bin/env python3
"""
My Model Container
Uses Ruth AI Model Runtime Base Image
"""

import signal
import sys

# Import from base image (already installed)
from ai_model_container import (
    IPCServer,
    InferenceRequest,
    InferenceResponse,
    Detection,
    FrameReader,
    NV12Preprocessor,
)

# Model-specific imports
import torch


def inference_handler(request: InferenceRequest) -> InferenceResponse:
    """
    Process inference request.

    This function:
    1. Reads frame from shared memory
    2. Preprocesses frame
    3. Runs model inference
    4. Returns detections
    """
    try:
        # Read frame from shared memory
        frame_reader = FrameReader(request.frame_reference)
        frame_header, frame_data = frame_reader.read_frame(
            request.frame_metadata.get("frame_id", 0)
        )

        # Preprocess NV12 to RGB
        preprocessor = NV12Preprocessor()
        frame_rgb = preprocessor.nv12_to_rgb(
            frame_data,
            frame_header.width,
            frame_header.height,
        )

        # Run your model inference here
        # detections = your_model.infer(frame_rgb)

        # Example detection
        detections = [
            Detection(
                class_id=0,
                class_name="object",
                confidence=0.9,
                bbox=[0.1, 0.1, 0.5, 0.5],
            )
        ]

        return InferenceResponse(
            model_id=request.model_id,
            camera_id=request.camera_id,
            frame_id=request.frame_metadata.get("frame_id", 0),
            detections=detections,
            error=None,
        )

    except Exception as e:
        return InferenceResponse(
            model_id=request.model_id,
            camera_id=request.camera_id,
            frame_id=request.frame_metadata.get("frame_id", 0),
            detections=[],
            error=str(e),
        )


def main():
    model_id = "my-model"

    print(f"Starting {model_id} container...")

    # Create IPC server
    server = IPCServer(model_id=model_id, inference_handler=inference_handler)
    server.start()

    print(f"Model container ready: /tmp/vas_model_{model_id}.sock")

    # Graceful shutdown
    def shutdown(sig, frame):
        print("\nStopping...")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Keep running
    signal.pause()


if __name__ == "__main__":
    main()
```

## Step 5: Create Model Configuration

Create `model.yaml`:

```yaml
model_id: my-model
model_name: My Model
model_version: 1.0.0

description: My AI model description

supported_tasks:
  - object_detection

input_format: NV12

expected_resolution: [640, 480]

resource_requirements:
  gpu_required: false
  gpu_memory_mb: 2048
  cpu_fallback_allowed: true

model_type: pytorch

model_weights: /app/weights/model.pt

confidence_threshold: 0.5

output_schema:
  type: object_detection
  format: bbox
  classes: 80
```

## Step 6: Build Your Model Container

```bash
docker build -t ruth-ai/my-model:1.0.0 .
```

## Step 7: Test Your Model Container

```bash
# Verify imports work
docker run --rm ruth-ai/my-model:1.0.0 \
  python3 -c 'from ai_model_container import IPCServer; print("OK")'

# Run container (basic test)
docker run --rm \
  -v /dev/shm:/dev/shm \
  -v /tmp:/tmp \
  ruth-ai/my-model:1.0.0
```

## Common Patterns

### GPU Support

For GPU-enabled models:

```dockerfile
# Use CUDA base if needed
FROM ruth-ai/model-runtime:0.1.0

# Install PyTorch with CUDA
RUN pip install --no-cache-dir \
    torch==2.0.1+cu118 \
    torchvision==0.15.2+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118
```

Run with:

```bash
docker run --gpus all \
  -v /dev/shm:/dev/shm \
  -v /tmp:/tmp \
  ruth-ai/my-model:1.0.0
```

### Loading Model Weights

```python
import torch

class MyModel:
    def __init__(self, weights_path):
        self.model = torch.load(weights_path)
        self.model.eval()

        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def infer(self, frame_rgb):
        # Preprocess
        tensor = self.preprocess(frame_rgb)
        tensor = tensor.to(self.device)

        # Inference
        with torch.no_grad():
            output = self.model(tensor)

        # Postprocess
        return self.postprocess(output)
```

### Error Handling

Always return an `InferenceResponse`, even on error:

```python
def inference_handler(request: InferenceRequest) -> InferenceResponse:
    try:
        # ... inference logic ...
        return InferenceResponse(...)
    except Exception as e:
        # Return error response
        return InferenceResponse(
            model_id=request.model_id,
            camera_id=request.camera_id,
            frame_id=request.frame_metadata.get("frame_id", 0),
            detections=[],
            error=f"Inference failed: {str(e)}",
        )
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'ai_model_container'"

Build the base image first:
```bash
cd runtime-base-image
./build.sh
```

### "Cannot connect to socket"

Make sure `/tmp` is mounted:
```bash
docker run -v /tmp:/tmp ...
```

### GPU not detected

Use `--gpus all` flag:
```bash
docker run --gpus all ...
```

### Import errors for model libraries

Add them to your Dockerfile:
```dockerfile
RUN pip install --no-cache-dir your-library
```

## Best Practices

1. **Pin dependency versions** for reproducibility
2. **Keep Dockerfiles minimal** - only install what you need
3. **Handle errors gracefully** - always return InferenceResponse
4. **Test locally first** before deploying
5. **Document your model** in model.yaml
6. **Use health checks** for production deployment

## Next Steps

- Read [Runtime Base Image README](README.md) for details
- See [Fall Detection Example](../models/fall-detection/) for a complete example
- Review [IPC Contract](../ai_model_container/CONTRACT.md) for protocol details

## Support

For issues:
1. Check Phase 4.4 summary: `/PHASE_4_4_SUMMARY.md`
2. Review example: `/models/fall-detection/`
3. Check logs: `docker logs <container-name>`
