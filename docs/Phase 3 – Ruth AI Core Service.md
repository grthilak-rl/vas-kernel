# Phase 3 – Ruth AI Core Service

## Design-Only Canonical Specification

---

## 1. Phase Objective

Phase 3 introduces **AI orchestration as a separate, independent service** (Ruth AI Core) that consumes frames from VAS **without controlling or modifying video pipelines**.

VAS remains the **video kernel**.
Ruth AI Core is a **control-plane service only**.

---

## 2. System Position

```
RTSP → VAS → Frame Ring Buffer
                ↓
         Frame Export Interface (Phase 2)
                ↓
        Ruth AI Core Service (Phase 3)
                ↓
        AI Model Containers (Phase 4)
```

---

## 3. What Phase 3 Is / Is Not

### Phase 3 IS:

* AI orchestration layer
* Camera ↔ model routing controller
* FPS enforcement point
* Metadata event producer

### Phase 3 IS NOT:

* Video pipeline
* Decoder
* MediaSoup participant
* RTSP / WebRTC controller
* Model runtime

---

## 4. Phase 3.1 – Stream Agent Internal State Model

### 4.1 Purpose

A **Stream Agent** is the minimal orchestration unit responsible for coordinating AI models for **one camera**.

---

### 4.2 Cardinality & Identity

* Exactly **one Stream Agent per camera**
* `stream_agent_id == camera_id`
* Created when first model subscribes
* Destroyed when no models remain

---

### 4.3 Internal State

```
StreamAgentState
├── camera_id
├── frame_source
├── subscriptions[]
├── scheduling_state
├── health_state
└── stats (optional, non-authoritative)
```

---

### 4.4 Frame Source Handle

* Read-only access to Phase 2 frame export
* No ownership of memory
* Best-effort semantics
* Frame skips are acceptable

---

### 4.5 Subscription Entry

```
Subscription
├── model_id
├── desired_fps
├── last_dispatched_frame_id
├── last_dispatch_timestamp
├── active
└── model_endpoint_ref
```

---

### 4.6 Forbidden State

Stream Agents must NEVER store:

* Raw frames
* Frame buffers
* Persistent state
* Cross-camera data

---

## 5. Phase 3.2 – Subscription Lifecycle

### 5.1 Creation

* Non-blocking
* No stream restarts
* No validation during creation

### 5.2 Removal

* Immediate
* No draining
* In-flight results may be dropped

### 5.3 Identity

Subscriptions are uniquely identified by:

```
(camera_id, model_id)
```

---

## 6. Phase 3.3 – FPS Scheduling Semantics

### 6.1 Scheduling Scope

* Scheduling is **per subscription**
* No global camera scheduling

### 6.2 FPS Meaning

`desired_fps` = maximum allowed frame dispatch rate

Not guaranteed, best-effort only.

---

### 6.3 Decision Rule

A frame MAY be dispatched if sufficient time has elapsed since the last dispatch.

Otherwise, it is skipped.

---

### 6.4 Forbidden Scheduling Mechanisms

* Queues
* Buffers
* Token buckets
* Feedback loops
* Backpressure

---

## 7. Phase 3.4 – Failure & Restart Semantics

### 7.1 Failure Domains

* VAS
* Frame Export Interface
* Ruth AI Core
* AI Model Containers

Each fails independently.

---

### 7.2 Failure Rules

* Ruth AI crash does not affect VAS
* Stream Agent crash affects only one camera
* Model failure affects only its subscription
* Frame export loss causes idle behavior

---

### 7.3 Forbidden Recovery Behavior

The system must NOT:

* Retry inference
* Restart models
* Buffer frames
* Coordinate restarts

---
    
## 8. Phase Boundary Lock

Phase 3 ends at **orchestration and routing only**.

No inference engines
No persistence
No UI

Anything beyond this belongs to Phase 4.

---

End of Phase 3 Canonical Design
