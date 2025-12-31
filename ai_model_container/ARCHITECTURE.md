# Phase 4.1 Architecture

**AI Model Container IPC Architecture**

This document provides architectural diagrams and explanations for the Phase 4.1 implementation.

---

## System Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                          VAS KERNEL                               │
│                                                                   │
│  RTSP → FFmpeg → Decoded Frames → Recording                       │
│              ↓                     MediaSoup → WebRTC             │
│              ↓                                                    │
│         Frame Ring Buffer (Phase 1)                               │
│              ↓                                                    │
│         Shared Memory Export (Phase 2)                            │
│              ↓                                                    │
│         /dev/shm/vas_frames_camera_X                              │
└───────────────────────────────────────────────────────────────────┘
                        ↓
                        ↓ (Frame reference passed via IPC)
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                       RUTH AI CORE (Phase 3)                      │
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │ StreamAgent  │   │ StreamAgent  │   │ StreamAgent  │           │
│  │  camera_1    │   │  camera_2    │   │  camera_3    │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                   │
│                            ↓                                      │
│                    Subscription Manager                           │
│                    FPS Gating Logic                               │
│                            ↓                                      │
│                 ┌─────────────────────┐                           │
│                 │ IPC Client (Future) │                           │
│                 └─────────────────────┘                           │
└───────────────────────────────────────────────────────────────────┘
                        ↓
                        ↓ (Unix Domain Socket IPC)
                        ↓
┌───────────────────────────────────────────────────────────────────┐
│                 AI MODEL CONTAINERS (Phase 4.1)                   │
│                                                                   │
│  ┌───────────────────────┐   ┌───────────────────────┐            │
│  │  YOLOv8 Container     │   │ Pose Estimation       │            │
│  │                       │   │ Container             │            │
│  │  ┌─────────────────┐  │   │ ┌─────────────────┐   │            │
│  │  │ IPC Server      │  │   │ │ IPC Server      │   │            │
│  │  │ UDS: yolov8n    │  │   │ │ UDS: pose_est   │   │            │
│  │  └─────────────────┘  │   │ └─────────────────┘   │            │
│  │          ↓            │   │         ↓             │            │
│  │  ┌─────────────────┐  │   │ ┌─────────────────┐   │            │
│  │  │ Inference       │  │   │ │ Inference       │   │            │
│  │  │ Handler         │  │   │ │ Handler         │   │            │
│  │  │ (Stateless)     │  │   │ │ (Stateless)     │   │            │
│  │  └─────────────────┘  │   │ └─────────────────┘   │            │
│  │          ↓            │   │         ↓             │            │
│  │  ┌─────────────────┐  │   │ ┌─────────────────┐   │            │
│  │  │ Model (Phase4.2)│  │   │ │ Model (Phase4.2)│   │            │
│  │  │ GPU Memory      │  │   │ │ GPU Memory      │   │            │
│  │  └─────────────────┘  │   │ └─────────────────┘   │            │
│  └───────────────────────┘   └───────────────────────┘            │
│                                                                   │
│  Serves: camera_1, camera_2,  Serves: camera_1, camera_3          │
│          camera_3                                                 │
└───────────────────────────────────────────────────────────────────┘
```

---

## IPC Protocol Flow

```
Ruth AI Core                           YOLOv8 Container
     │                                       │
     │ 1. Connect to UDS                     │
     │────────────────────────────────────→  │
     │   /tmp/vas_model_yolov8n.sock         │
     │                                       │
     │ 2. Send Request                       │
     │    [4-byte length][JSON]              │
     │────────────────────────────────────→  │
     │                                       │
     │                              3. Deserialize Request
     │                              ┌─────────────────────┐
     │                              │ InferenceRequest    │
     │                              │ - frame_reference   │
     │                              │ - frame_metadata    │
     │                              │ - camera_id         │
     │                              │ - model_id          │
     │                              │ - timestamp         │
     │                              └─────────────────────┘
     │                                        │
     │                              4. Validate frame reference
     │                                 (READ-ONLY check)
     │                                        │
     │                              5. Read frame from shared memory
     │                                 /dev/shm/vas_frames_camera_1
     │                                        │
     │                              6. Run inference (GPU)
     │                                 [Phase 4.1: Mock]
     │                                        │
     │                              7. Build Response
     │                              ┌─────────────────────┐
     │                              │ InferenceResponse   │
     │                              │ - model_id          │
     │                              │ - camera_id         │
     │                              │ - frame_id          │
     │                              │ - detections[]      │
     │                              │ - metadata          │
     │                              │ - error             │
     │                              └─────────────────────┘
     │                                        │
     │ 8. Receive Response                    │
     │    [4-byte length][JSON]               │
     │  ←──────────────────────────────────── │
     │                                        │
     │ 9. Close Connection                    │
     │  ────────────────────────────────────→ │
     │                                        │
     ∨                                        ∨
```

---

## Container Internal Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     Model Container Process                   │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                     IPC Server                           │ │
│  │                                                          │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │          Main Accept Loop (Thread)                  │ │ │
│  │  │                                                     │ │ │
│  │  │  while running:                                     │ │ │
│  │  │    client_sock = server_sock.accept()               │ │ │
│  │  │    spawn_handler_thread(client_sock)                │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                          │                               │ │
│  │                          ↓                               │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │     Handler Thread 1     │     Handler Thread 2     │ │ │
│  │  │  (camera_1 request)      │  (camera_2 request)      │ │ │
│  │  │                          │                          │ │ │
│  │  │  1. Read request         │  1. Read request         │ │ │
│  │  │  2. Deserialize          │  2. Deserialize          │ │ │
│  │  │  3. Call handler()       │  3. Call handler()       │ │ │
│  │  │  4. Serialize response   │  4. Serialize response   │ │ │
│  │  │  5. Write response       │  5. Write response       │ │ │
│  │  │  6. Close socket         │  6. Close socket         │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                          │              │                │ │
│  └──────────────────────────┼──────────────┼────────────────┘ │
│                             ↓              ↓                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Inference Handler (STATELESS)              │  │
│  │                                                         │  │
│  │  def __call__(request: InferenceRequest):               │  │
│  │    # NO MUTABLE STATE                                   │  │
│  │    # NO PER-CAMERA TRACKING                             │  │
│  │    # NO TEMPORAL CONTEXT                                │  │
│  │                                                         │  │ 
│  │    validate_frame_reference(request.frame_reference)    │  │
│  │    detections = run_inference(request)                  │  │ 
│  │    return InferenceResponse(...)                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                             ↓                                 │
│  ┌─────────────────────────────────────────────────────────┐  │ 
│  │                    Model (Phase 4.2)                    │  │
│  │                                                         │  │
│  │  - Loaded ONCE at container startup                     │  │
│  │  - Resident in GPU memory                               │  │
│  │  - Shared across all cameras                            │  │
│  │  - Thread-safe inference calls                          │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Concurrency Model

### One Container Serves Many Cameras

```
Camera 1 ──┐
           │
Camera 2 ──┼──→ [YOLOv8 Container] ──→ Concurrent Inference
           │        (ONE process)
Camera 3 ──┘
```

**NOT:**
```
Camera 1 ──→ [YOLOv8 Container 1]  ❌ Wrong! Multiple containers
Camera 2 ──→ [YOLOv8 Container 2]  ❌ for same model
Camera 3 ──→ [YOLOv8 Container 3]  ❌
```

### Stateless Request Processing

```
Request 1 (camera_1, frame_42)  ──→ Handler ──→ Response 1
Request 2 (camera_2, frame_13)  ──→ Handler ──→ Response 2
Request 3 (camera_1, frame_43)  ──→ Handler ──→ Response 3
                                     ↑
                                     │
                              NO STATE SHARING
                              Each request independent
```

### Thread Safety

```
┌─────────────────────────────────────────────────────────┐
│               Inference Handler (Shared)                │
│                                                         │
│  Immutable State:                                       │
│  ✅ model_id (read-only)                                │
│  ✅ model_config (read-only)                            │
│  ✅ _model (thread-safe inference)                      │
│                                                         │
│  NO Mutable State:                                      │
│  ❌ No per-camera counters                              │
│  ❌ No frame history                                    │
│  ❌ No temporal buffers                                 │
│  ❌ No shared accumulators                              │
└─────────────────────────────────────────────────────────┘
         ↑              ↑              ↑
         │              │              │
    Thread 1       Thread 2       Thread 3
   (camera_1)     (camera_2)     (camera_3)
```

---

## Frame Memory Access Pattern

```
┌───────────────────────────────────────────────────────────┐
│             VAS Kernel (Frame Producer)                   │
│                                                           │
│  Decoded Frame → Ring Buffer → Shared Memory              │
│                                /dev/shm/vas_frames_X      │
│                                      │                    │
│                                      │ WRITE (exclusive)  │
│                                      ↓                    │
│                          ┌─────────────────────┐          │
│                          │   Frame Memory      │          │
│                          │   (Shared Memory)   │          │
│                          └─────────────────────┘          │
│                                      ↑                    │
│                                      │ READ (shared)      │
└──────────────────────────────────────┼────────────────────┘
                                       │
                   ┌───────────────────┴──────────────────┐
                   │                                      │
    ┌──────────────┴─────────────┐       ┌────────────────┴───────────┐
    │  AI Container 1            │       │  AI Container 2            │
    │  (YOLOv8)                  │       │  (Pose Estimation)         │
    │                            │       │                            │
    │  READ-ONLY access          │       │  READ-ONLY access          │
    │  - No mutations            │       │  - No mutations            │
    │  - No retention            │       │  - No retention            │
    │  - Frame copied if needed  │       │  - Frame copied if needed  │
    └────────────────────────────┘       └────────────────────────────┘
```

**Key Rules:**
1. VAS Kernel has EXCLUSIVE WRITE access
2. Containers have SHARED READ-ONLY access
3. Containers MUST NOT mutate shared memory
4. Containers MUST NOT retain frame references
5. Containers MAY copy frame to private memory if needed

---

## Failure Isolation

```
┌─────────────────────────────────────────────────────────────┐
│                     VAS Kernel                              │
│  (RTSP, FFmpeg, MediaSoup, Recording)                       │
│                                                             │
│  Status: ✅ Running                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ (Isolated boundary)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   Ruth AI Core                              │
│  (StreamAgent, Subscription, FPS Gating)                    │
│                                                             │
│  Status: ✅ Running                                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ (IPC boundary)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              AI Model Containers                            │
│                                                             │
│  ┌────────────────┐  ┌──────────────────┐                   │
│  │ YOLOv8         │  │ Pose Est         │                   │
│  │ Status: ✅     │  │ Status: ❌ CRASH │                   │
│  └────────────────┘  └──────────────────┘                   │
│                                                             │
│  Failure Impact: Pose estimation unavailable                │
│  Other containers: Unaffected ✅                            │
└─────────────────────────────────────────────────────────────┘

Result:
- VAS Kernel: ✅ Still recording, streaming normally
- Ruth AI Core: ✅ Still managing other models
- YOLOv8: ✅ Still processing requests
- Pose Estimation: ❌ Unavailable (isolated failure)
```

---

## Data Flow Example

### Request: Detect objects in frame 42 from camera_1

```
1. Ruth AI Core prepares request:
   ┌─────────────────────────────────────┐
   │ InferenceRequest                    │
   │ ─────────────────────────────────── │
   │ frame_reference:                    │
   │   "/dev/shm/vas_frames_camera_1"    │
   │ frame_metadata:                     │
   │   frame_id: 42                      │
   │   width: 1920                       │
   │   height: 1080                      │
   │   format: "NV12"                    │
   │ camera_id: "camera_1"               │
   │ model_id: "yolov8n"                 │
   │ timestamp: 1735598400.123           │
   └─────────────────────────────────────┘

2. Serialize to JSON and send via UDS:
   [4-byte length: 312][JSON payload: {...}]

3. YOLOv8 container receives and deserializes

4. Handler validates frame reference:
   - Check path exists: /dev/shm/vas_frames_camera_1
   - Check read permissions: READ-ONLY ✅
   - Do NOT mutate memory ✅

5. Handler runs inference (Phase 4.1: mock):
   - Phase 4.2: Read NV12 frame from shared memory
   - Phase 4.2: Preprocess (resize, normalize)
   - Phase 4.2: GPU inference
   - Phase 4.2: Post-process (NMS, thresholding)
   - Phase 4.1: Return mock detections

6. Handler builds response:
   ┌─────────────────────────────────────┐
   │ InferenceResponse                   │
   │ ─────────────────────────────────── │
   │ model_id: "yolov8n"                 │
   │ camera_id: "camera_1"               │
   │ frame_id: 42                        │
   │ detections: [                       │
   │   {                                 │
   │     class_id: 0,                    │
   │     class_name: "person",           │
   │     confidence: 0.85,               │
   │     bbox: [0.1, 0.1, 0.3, 0.5]      │
   │   }                                 │
   │ ]                                   │
   │ metadata: {                         │
   │   inference_time_ms: 42.3           │
   │ }                                   │
   │ error: null                         │
   └─────────────────────────────────────┘

7. Serialize response to JSON and send:
   [4-byte length: 278][JSON payload: {...}]

8. Ruth AI Core receives and processes response
```

---

## Phase 4.1 Scope Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 4.1 SCOPE                          │
│                                                             │
│  ✅ IPC Schema (InferenceRequest/Response)                  │
│  ✅ Unix Domain Socket Server                               │
│  ✅ Length-prefixed JSON Protocol                           │
│  ✅ Stateless Inference Handler Skeleton                    │
│  ✅ Container Lifecycle Management                          │
│  ✅ Mock Inference (Stub Detections)                        │
│  ✅ Error Handling                                          │
│  ✅ Documentation                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ (Phase boundary)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  PHASE 4.2+ SCOPE                           │
│                                                             │
│  ❌ Real Model Loading (PyTorch, ONNX, TensorRT)            │
│  ❌ GPU Inference Execution                                 │
│  ❌ Model Onboarding Workflow                               │
│  ❌ Container Discovery                                     │
│  ❌ Integration with Ruth AI Core                           │
│  ❌ Health Monitoring                                       │
│  ❌ Performance Optimization                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

Phase 4.1 establishes:

1. **Clean IPC boundary** between Ruth AI Core and Model Containers
2. **Stateless architecture** with no per-camera coupling
3. **Concurrent processing** model (one container serves many cameras)
4. **Failure isolation** (container crashes don't affect VAS)
5. **Production-ready protocol** (length-prefixed JSON over UDS)

This architecture enables Phase 4.2 to add real model inference while maintaining the contract guarantees established in Phase 4.1.

---

**Last Updated:** 2025-12-30
**Phase:** 4.1 (AI Model IPC & Inference Contract)
**Status:** Complete
