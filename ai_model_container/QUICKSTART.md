# Quick Start Guide - Phase 4.1

**AI Model Container - Quick Start**

Get up and running with the Phase 4.1 AI Model Container in under 5 minutes.

---

## Prerequisites

- Python 3.7+
- Unix-like operating system (Linux, macOS)
- `/tmp` directory writable

No GPU required for Phase 4.1 (mock inference only).

---

## Step 1: Verify Installation

```bash
cd /home/atgin-rnd-ubuntu/vas-kernel
ls ai_model_container/
```

Expected output:
```
ARCHITECTURE.md
container.py
CONTRACT.md
example_client.py
example_container.py
inference_handler.py
__init__.py
ipc_server.py
PHASE_4_1_SUMMARY.md
QUICKSTART.md
README.md
schema.py
```

---

## Step 2: Run Example Container

Open a terminal and run:

```bash
cd /home/atgin-rnd-ubuntu/vas-kernel
python3 -m ai_model_container.example_container
```

Expected output:
```
================================================================================
Phase 4.1 – AI Model Container Example
================================================================================

This is a MOCK container for demonstration purposes.
No real model is loaded. Inference returns stub detections.

Phase 4.2 will add real model loading and GPU inference.

================================================================================

Inference handler initialized for model 'yolov8n'
Model config: {...}
Note: Phase 4.1 uses MOCK inference (no real model loaded)
Starting model container: yolov8n
Model config: {...}
IPC server started for model 'yolov8n' at /tmp/vas_model_yolov8n.sock
Model container 'yolov8n' is ready to serve requests
Press Ctrl+C to stop
```

✅ Container is now running and ready to accept requests!

---

## Step 3: Send Test Requests

Open a **second terminal** and run:

```bash
cd /home/atgin-rnd-ubuntu/vas-kernel
python3 -m ai_model_container.example_client
```

Expected output:
```
================================================================================
Phase 4.1 – AI Model Container Client Example
================================================================================

Testing IPC with model container: yolov8n
Camera: camera_1

Sending 5 inference requests...

Request 1/5 (frame_id=1)...
  Response received in 2.34 ms
  Model: yolov8n
  Camera: camera_1
  Frame ID: 1
  Detections: 0

Request 2/5 (frame_id=2)...
  Response received in 1.87 ms
  Model: yolov8n
  Camera: camera_1
  Frame ID: 2
  Detections: 0

Request 3/5 (frame_id=3)...
  Response received in 1.92 ms
  Model: yolov8n
  Camera: camera_1
  Frame ID: 3
  Detections: 2
    [1] person: confidence=0.85, bbox=[0.1, 0.1, 0.3, 0.5]
    [2] car: confidence=0.72, bbox=[0.6, 0.5, 0.9, 0.9]

...

================================================================================
All requests completed successfully!
================================================================================

Phase 4.1 IPC contract validation: ✅ PASSED
```

✅ IPC protocol is working correctly!

---

## Step 4: Stop Container

In the **first terminal** (where container is running), press `Ctrl+C`:

Expected output:
```
^C
Received SIGINT, shutting down gracefully...
Stopping model container: yolov8n
Cleaning up model container: yolov8n
IPC server stopped for model 'yolov8n'
Cleaning up inference handler for model 'yolov8n'
Model container 'yolov8n' stopped
```

✅ Container stopped gracefully!

---

## Understanding the Output

### Mock Detections (Phase 4.1)

The example container returns **stub detections**:
- Frame 3, 6, 9, ... → "person" detection
- Frame 5, 10, 15, ... → "car" detection

This demonstrates the detection schema but does **NOT** perform real inference.

**Phase 4.2** will add real model loading and GPU inference.

---

## Manual Testing with netcat (Advanced)

You can manually test the IPC protocol using `netcat` or `socat`:

### 1. Start container:
```bash
python3 -m ai_model_container.example_container
```

### 2. Send raw request (another terminal):
```bash
python3 << 'EOF'
import json
import socket
import struct

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/vas_model_yolov8n.sock")

request = {
    "frame_reference": "/dev/shm/test_frame",
    "frame_metadata": {"frame_id": 1, "width": 1920, "height": 1080, "format": "NV12", "timestamp": 0.0},
    "camera_id": "test_camera",
    "model_id": "yolov8n",
    "timestamp": 0.0
}

# Send
json_bytes = json.dumps(request).encode("utf-8")
sock.sendall(struct.pack("!I", len(json_bytes)) + json_bytes)

# Receive
length = struct.unpack("!I", sock.recv(4))[0]
response = json.loads(sock.recv(length).decode("utf-8"))

print(json.dumps(response, indent=2))
sock.close()
EOF
```

---

## Troubleshooting

### Error: "Connection refused"

**Problem:** Container is not running.

**Solution:** Start container in terminal 1:
```bash
python3 -m ai_model_container.example_container
```

### Error: "Address already in use"

**Problem:** Previous container instance didn't clean up socket.

**Solution:** Remove stale socket:
```bash
rm /tmp/vas_model_yolov8n.sock
```

### Error: "Module not found"

**Problem:** Python can't find `ai_model_container` module.

**Solution:** Run from VAS kernel root directory:
```bash
cd /home/atgin-rnd-ubuntu/vas-kernel
python3 -m ai_model_container.example_container
```

---

## Next Steps

### Read Documentation

- [README.md](README.md) - API documentation and usage guide
- [CONTRACT.md](CONTRACT.md) - Authoritative IPC contract specification
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture diagrams
- [PHASE_4_1_SUMMARY.md](PHASE_4_1_SUMMARY.md) - Implementation summary

### Explore Code

1. **IPC Schema** ([schema.py](schema.py))
   - Request/response data structures
   - Validation rules
   - Type definitions

2. **IPC Server** ([ipc_server.py](ipc_server.py))
   - Unix Domain Socket server
   - Protocol implementation
   - Connection handling

3. **Inference Handler** ([inference_handler.py](inference_handler.py))
   - Stateless request processor
   - Mock inference logic
   - Error handling

4. **Container** ([container.py](container.py))
   - Lifecycle management
   - Signal handling
   - Graceful shutdown

### Modify Example

Try customizing the example:

1. **Change model ID:**
   - Edit `example_container.py`
   - Change `model_id="yolov8n"` to `model_id="my_model"`
   - Socket path becomes `/tmp/vas_model_my_model.sock`

2. **Add custom detection logic:**
   - Edit `inference_handler.py`
   - Modify `_run_inference()` method
   - Return different mock detections

3. **Test concurrent requests:**
   - Run example_client in multiple terminals simultaneously
   - Observe container handling concurrent connections

---

## Phase 4.2 Preview

Phase 4.2 will add **real model inference**:

```python
# Phase 4.2 example (not yet implemented)
import torch
from ultralytics import YOLO

class InferenceHandler:
    def __init__(self, model_id: str, model_config: dict):
        # Load real model into GPU
        self.model = YOLO(model_config["weights_path"])
        self.model.to(model_config["device"])  # e.g., "cuda:0"

    def __call__(self, request: InferenceRequest):
        # Read frame from shared memory (NV12 format)
        frame = read_nv12_frame(request.frame_reference)

        # Preprocess (resize, normalize)
        tensor = preprocess(frame)

        # GPU inference
        results = self.model(tensor)

        # Post-process (NMS, thresholding)
        detections = post_process(results)

        return InferenceResponse(...)
```

---

## Summary

You've successfully:

✅ Run an AI model container
✅ Sent inference requests via IPC
✅ Validated the Phase 4.1 contract
✅ Observed stateless, concurrent request handling

**Phase 4.1 is complete!** The IPC foundation is ready for Phase 4.2 model integration.

---

**Need Help?**

- Review [CONTRACT.md](CONTRACT.md) for IPC specification
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Read [README.md](README.md) for detailed API docs

---

**Last Updated:** 2025-12-30
**Phase:** 4.1 (AI Model IPC & Inference Contract)
**Status:** Complete ✅
