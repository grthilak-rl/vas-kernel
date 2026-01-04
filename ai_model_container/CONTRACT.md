# Phase 4.1 IPC & Inference Contract

**AUTHORITATIVE CONTRACT SPECIFICATION**

This document defines the **hard boundary contract** between Ruth AI Core (caller) and AI Model Containers (callees) for Phase 4.1.

---

## Contract Overview

### Parties

- **Ruth AI Core**: Control-plane orchestration service (caller)
- **AI Model Container**: Inference runtime (callee)

### Boundary

**Unix Domain Socket (UDS)** with length-prefixed JSON protocol.

### Guarantees

1. **Exactly-once semantics**: One request → One response
2. **Synchronous execution**: No streaming, no async continuations
3. **Stateless processing**: No state carried between requests
4. **Failure isolation**: Container failure ≠ VAS failure

---

## Container Cardinality

**CRITICAL RULE:**

- Exactly **ONE container per model type**
- Containers are **NOT per camera**
- Containers are **long-lived and pre-loaded**
- Containers **serve multiple cameras concurrently**

### Examples

✅ **CORRECT:**
- One `yolov8n` container serves cameras: `camera_1`, `camera_2`, `camera_3`
- One `pose_estimation` container serves all cameras needing pose detection

❌ **INCORRECT:**
- One `yolov8n` container per camera (violates cardinality)
- Spawning new containers per request (violates lifecycle)

---

## Concurrency Rules

Containers MUST:

- ✅ Treat each inference request independently
- ✅ Support concurrent request processing (MAY process in parallel)
- ✅ Be thread-safe (or use async I/O)

Containers MUST NOT:

- ❌ Assume ordered delivery
- ❌ Rely on request sequencing
- ❌ Share mutable state across requests
- ❌ Maintain per-camera state

**Concurrency is an implementation detail** of the container and MUST NOT leak into the IPC contract.

---

## IPC Transport

### Unix Domain Socket

- **Path:** `/tmp/vas_model_{model_id}.sock`
- **Type:** `SOCK_STREAM` (TCP-like semantics)
- **Permissions:** `0600` (owner read/write only)
- **Lifecycle:** Bound at container start, unbound at container stop

### Protocol: Length-Prefixed JSON

```
┌──────────────────┬────────────────────────┐
│ 4-byte length    │ JSON payload           │
│ (big-endian)     │ (UTF-8 encoded)        │
└──────────────────┴────────────────────────┘
```

- **Length:** Unsigned 32-bit integer, network byte order (big-endian)
- **Payload:** UTF-8 encoded JSON object
- **Max message size:** 10 MB (sanity check)

### Request Flow

```
Ruth AI Core                          Model Container
     |                                     |
     |--- connect(UDS) ------------------→ |
     |                                     |
     |--- send([length][request JSON]) --→ |
     |                                     |
     |                              [Process inference]
     |                                     |
     |← -- send([length][response JSON]) --|
     |                                     |
     |--- close() -----------------------→ |
```

**Connection model:**
- Ruth AI Core connects per request (or uses connection pool)
- Container accepts concurrent connections
- No long-lived connections required

---

## Inference Request Contract

### Schema

```json
{
  "frame_reference": "string (path)",
  "frame_metadata": {
    "frame_id": "int",
    "width": "int",
    "height": "int",
    "format": "string",
    "timestamp": "float",
    ...
  },
  "camera_id": "string",
  "model_id": "string",
  "timestamp": "float (Unix seconds)",
  "config": {
    // Optional request-level config
  }
}
```

### Mandatory Fields

| Field             | Type   | Description                               |
|-------------------|--------|-------------------------------------------|
| `frame_reference` | string | Path to frame (READ-ONLY)                 |
| `frame_metadata`  | object | Frame header (width, height, format, etc.)|
| `camera_id`       | string | Source camera identifier                  |
| `model_id`        | string | Target model identifier                   |
| `timestamp`       | float  | Request timestamp (Unix seconds)          |

### Optional Fields

| Field    | Type   | Description                           |
|----------|--------|---------------------------------------|
| `config` | object | Request-level configuration overrides |

### Frame Reference Rules

**CRITICAL:**

- `frame_reference` is a **path or handle**, NOT raw bytes
- Example: `/dev/shm/vas_frames_camera_1`
- Containers have **READ-ONLY** access
- Containers MUST NOT:
  - Mutate shared memory
  - Retain `frame_reference` beyond request scope
  - Assume frame persistence after response
  - Take ownership of frame memory

**Frame lifecycle:**
- Ruth AI Core: Allocates frame in shared memory
- Ruth AI Core: Sends `frame_reference` to container
- Container: Reads frame (READ-ONLY)
- Container: Returns response
- Ruth AI Core: Frame MAY be deallocated immediately

---

## Inference Response Contract

### Schema

```json
{
  "model_id": "string",
  "camera_id": "string",
  "frame_id": "any (int or float)",
  "detections": [
    {
      "class_id": "int",
      "class_name": "string",
      "confidence": "float (0.0 to 1.0)",
      "bbox": [x_min, y_min, x_max, y_max],
      "track_id": "int or null"
    }
  ],
  "metadata": {
    // Optional inference metadata
  },
  "error": "string or null"
}
```

### Mandatory Fields

| Field        | Type   | Description                           |
|--------------|--------|---------------------------------------|
| `model_id`   | string | Echo from request (for correlation)   |
| `camera_id`  | string | Echo from request (for correlation)   |
| `frame_id`   | any    | Frame identifier (for correlation)    |
| `detections` | array  | List of Detection objects (may be empty) |

### Optional Fields

| Field      | Type   | Description                              |
|------------|--------|------------------------------------------|
| `metadata` | object | Inference metadata (timing, GPU ID, etc.)|
| `error`    | string | Error message if inference failed        |

### Detection Schema (Example)

**NOTE:** Detection schema is **model-defined**. This is an example for object detection models.

| Field        | Type   | Description                              |
|--------------|--------|------------------------------------------|
| `class_id`   | int    | Integer class identifier (0-indexed)     |
| `class_name` | string | Human-readable class name                |
| `confidence` | float  | Confidence score (0.0 to 1.0)            |
| `bbox`       | array  | Bounding box [x_min, y_min, x_max, y_max] (normalized 0-1) |
| `track_id`   | int?   | Optional tracking ID (multi-object tracking) |

**Other model types** (classification, segmentation, pose) may define different schemas.

### Response Semantics

- **Empty detections:** Valid response (no objects detected)
- **Error set:** Inference failed, `detections` SHOULD be empty
- **No error:** Inference succeeded, `detections` contains results

---

## Request Lifecycle Rules

### Synchronous Contract

- Exactly **ONE request** produces exactly **ONE response**
- No streaming responses
- No partial results
- No callbacks or async continuations
- No out-of-band signaling

**Inference is strictly synchronous at the IPC boundary.**

### Failure Semantics

| Scenario                     | Container Behavior                          |
|------------------------------|---------------------------------------------|
| Invalid request JSON         | Return error response                       |
| Frame reference inaccessible | Return error response                       |
| Inference exception          | Catch exception, return error response      |
| Socket error                 | Close connection (caller retries)           |

**Containers MUST NOT:**
- Retry failed inference internally
- Queue failed requests
- Assume caller will retry

**Retry policy is the caller's responsibility.**

---

## Forbidden Behavior

Containers MUST NOT:

| Category           | Forbidden Action                              |
|--------------------|-----------------------------------------------|
| **Video Pipeline** | Access RTSP streams                           |
|                    | Access MediaSoup                              |
|                    | Decode video (frames are already decoded)     |
| **State**          | Track per-camera state                        |
|                    | Maintain temporal context                     |
|                    | Store frame history                           |
| **Scheduling**     | Perform FPS enforcement (Ruth AI Core's job)  |
|                    | Queue frames                                  |
|                    | Retry failed inference                        |
| **Concurrency**    | Spawn per-camera workers                      |
|                    | Assume ordered request delivery               |
| **Memory**         | Mutate shared memory                          |
|                    | Retain frame references beyond request scope  |
|                    | Control GPU scheduling beyond their process   |

---

## Phase 4.1 Implementation Checklist

### IPC Server ✅

- [x] Unix Domain Socket server
- [x] Length-prefixed JSON protocol
- [x] Concurrent connection handling
- [x] Request deserialization
- [x] Response serialization
- [x] Graceful shutdown

### Inference Handler ✅

- [x] Stateless request processor
- [x] Thread-safe implementation
- [x] Frame reference validation
- [x] Error handling and responses
- [x] Mock inference output (Phase 4.1)

### Container Orchestration ✅

- [x] Lifecycle management (start/stop)
- [x] Signal handling (SIGTERM/SIGINT)
- [x] Cleanup on shutdown
- [x] Logging and diagnostics

### Documentation ✅

- [x] Contract specification (this file)
- [x] API documentation (README.md)
- [x] Code comments
- [x] Example implementation
- [x] Test client

---

## Success Criteria

Phase 4.1 is complete ONLY IF:

- ✅ IPC contract is **explicit and enforced**
- ✅ Containers are **stateless per request**
- ✅ **One container serves many cameras**
- ✅ **No coupling to VAS internals** exists
- ✅ **No scheduling or orchestration logic** leaks into containers

---

## What's Next: Phase 4.2

Phase 4.2 will add:

- Real model loading (PyTorch, ONNX, TensorRT)
- GPU inference execution
- Model onboarding workflow
- Container discovery mechanism
- Integration with Ruth AI Core
- Health monitoring and heartbeats
- Performance optimization

**Phase 4.1 provides the foundation.** Phase 4.2 builds the execution.

---

## Validation

To validate Phase 4.1 implementation:

```bash
# Terminal 1: Start container
python3 -m ai_model_container.example_container

# Terminal 2: Send test requests
python3 -m ai_model_container.example_client
```

Expected output:
- Container accepts connections on `/tmp/vas_model_yolov8n.sock`
- Client sends 5 inference requests
- Container returns mock detections (Phase 4.1: stub data)
- All requests complete successfully

---

**Phase 4.1 Status:** ✅ **COMPLETE**

This implementation satisfies all Phase 4.1 requirements as specified in `CLAUDE.md`.
