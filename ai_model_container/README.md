# AI Model Container - Phase 4.1

**Phase 4.1 – AI Model IPC & Inference Contract**

This package implements the container-side IPC server skeleton for AI model containers according to the Phase 4.1 specification in `CLAUDE.md`.

## Overview

AI Model Containers are **independent, long-lived runtimes** that execute inference requests from Ruth AI Core.

### Critical Design Principles

1. **One Container Per Model Type**
   - NOT one per camera
   - Long-lived, pre-loaded containers
   - Serve multiple cameras concurrently

2. **Stateless Per Request**
   - No state carried between requests
   - No per-camera tracking
   - No temporal context
   - No frame buffering

3. **Hard IPC Boundary**
   - Unix Domain Socket transport
   - Length-prefixed JSON protocol
   - Synchronous request/response
   - No streaming, no callbacks

4. **Failure Isolation**
   - Container failure affects only this model
   - No coupling to VAS internals
   - No retry logic (caller's responsibility)
   - Clean error responses

## Architecture

```
Ruth AI Core (caller)
       |
       | Unix Domain Socket
       | /tmp/vas_model_{model_id}.sock
       |
       v
AI Model Container (callee)
   ├── IPC Server (ipc_server.py)
   │   └── Length-prefixed JSON protocol
   ├── Inference Handler (inference_handler.py)
   │   └── Stateless request processor
   └── Container Orchestration (container.py)
       └── Lifecycle management
```

## IPC Contract

### Request Schema

```python
InferenceRequest(
    frame_reference: str,        # Path to shared memory (READ-ONLY)
    frame_metadata: dict,         # Width, height, format, timestamp
    camera_id: str,               # Source camera identifier
    model_id: str,                # Target model identifier
    timestamp: float,             # Request timestamp (Unix seconds)
    config: Optional[dict] = None # Optional request-level config
)
```

### Response Schema

```python
InferenceResponse(
    model_id: str,                # Echo from request
    camera_id: str,               # Echo from request
    frame_id: Any,                # Frame identifier (for correlation)
    detections: List[Detection],  # Detection results (may be empty)
    metadata: Optional[dict],     # Optional inference metadata
    error: Optional[str]          # Error message if inference failed
)
```

### Detection Schema (Example)

```python
Detection(
    class_id: int,                # Integer class identifier
    class_name: str,              # Human-readable class name
    confidence: float,            # Confidence score (0.0 to 1.0)
    bbox: List[float],            # [x_min, y_min, x_max, y_max] (normalized 0-1)
    track_id: Optional[int]       # Optional tracking ID
)
```

## Protocol

**Transport:** Unix Domain Socket (UDS)

**Socket Path:** `/tmp/vas_model_{model_id}.sock`

**Message Format:** Length-prefixed JSON

```
[4-byte big-endian length][JSON payload]
```

**Request Flow:**
1. Ruth AI Core connects to UDS
2. Ruth AI Core sends InferenceRequest (length + JSON)
3. Container processes request synchronously
4. Container sends InferenceResponse (length + JSON)
5. Connection closes

## Frame Memory Rules

**CRITICAL:** Containers have **READ-ONLY** access to frames.

- `frame_reference` points to shared memory (e.g., `/dev/shm/vas_frames_camera_1`)
- Containers MUST NOT mutate shared memory
- Containers MUST NOT retain `frame_reference` beyond request scope
- Containers MUST assume frames may disappear after response
- Containers have NO ownership of frame memory

## Concurrency Model

**Container-Level:**
- One IPC server accepts concurrent connections
- Each connection handled in separate thread (Phase 4.1)
- Alternative: async I/O (implementation detail)

**Request-Level:**
- Each request is independent (stateless)
- No shared mutable state between requests
- Containers MUST treat requests independently
- Containers MUST NOT assume ordered delivery

## Usage Example

### Container Implementation

```python
from ai_model_container import ModelContainer

# Create container for YOLOv8 model
container = ModelContainer(
    model_id="yolov8n",
    model_config={
        "device": "cuda:0",
        "confidence_threshold": 0.5,
        "nms_iou_threshold": 0.45
    }
)

# Start container (blocks until stopped)
container.start()
```

### Client Usage (Ruth AI Core)

```python
import json
import socket
import struct

def send_inference_request(model_id: str, request: dict) -> dict:
    """Send inference request to model container via UDS."""

    # Connect to container's UDS
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(f"/tmp/vas_model_{model_id}.sock")

    try:
        # Serialize request to JSON
        json_bytes = json.dumps(request).encode("utf-8")

        # Send length prefix + JSON
        length = struct.pack("!I", len(json_bytes))
        sock.sendall(length + json_bytes)

        # Read response length prefix
        length_bytes = sock.recv(4)
        response_length = struct.unpack("!I", length_bytes)[0]

        # Read response JSON
        response_bytes = sock.recv(response_length)
        response = json.loads(response_bytes.decode("utf-8"))

        return response

    finally:
        sock.close()
```

## Phase 4.1 Scope

### What IS Implemented

- ✅ IPC schema definition (`schema.py`)
- ✅ Unix Domain Socket server (`ipc_server.py`)
- ✅ Stateless inference handler skeleton (`inference_handler.py`)
- ✅ Container orchestration (`container.py`)
- ✅ Mock inference output (stub detections)
- ✅ Request/response validation
- ✅ Error handling and responses
- ✅ Graceful shutdown

### What IS NOT Implemented (Phase 4.2+)

- ❌ Real model loading
- ❌ GPU inference execution
- ❌ Model onboarding
- ❌ Container discovery
- ❌ Health monitoring
- ❌ Integration with Ruth AI Core
- ❌ Performance optimization
- ❌ Multi-GPU support

## Forbidden Behavior

Containers MUST NOT:

- ❌ Access RTSP streams
- ❌ Access MediaSoup
- ❌ Decode video (frames are already decoded)
- ❌ Track per-camera state
- ❌ Maintain temporal context
- ❌ Perform FPS enforcement (Ruth AI Core's job)
- ❌ Retry failed inference
- ❌ Queue frames
- ❌ Spawn per-camera workers
- ❌ Control GPU scheduling beyond their process
- ❌ Mutate shared memory
- ❌ Retain frame references beyond request scope

## Success Criteria (Phase 4.1)

Phase 4.1 is complete ONLY IF:

- ✅ IPC contract is explicit and enforced
- ✅ Containers are stateless per request
- ✅ One container serves many cameras
- ✅ No coupling to VAS internals exists
- ✅ No scheduling or orchestration logic leaks into containers

## Files

```
ai_model_container/
├── __init__.py              # Package exports
├── schema.py                # IPC request/response schema
├── ipc_server.py            # Unix Domain Socket server
├── inference_handler.py     # Stateless inference handler
├── container.py             # Container lifecycle management
├── README.md                # This file
└── example_container.py     # Runnable example
```

## Running the Example

```bash
# Run example container
cd /home/atgin-rnd-ubuntu/vas-kernel
python3 -m ai_model_container.example_container
```

The example container will:
1. Start IPC server on `/tmp/vas_model_yolov8n.sock`
2. Accept inference requests
3. Return mock detections
4. Run until Ctrl+C

## Next Steps (Phase 4.2)

Phase 4.2 will add:
- Real model loading (PyTorch, ONNX, TensorRT)
- GPU inference execution
- Model-specific post-processing
- Container discovery mechanism
- Integration with Ruth AI Core
- Performance benchmarking

---

**Phase 4.1 Status:** ✅ COMPLETE

This implementation satisfies all Phase 4.1 requirements as specified in `CLAUDE.md`.
