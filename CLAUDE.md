You are implementing **VAS Kernel Phases** incrementally.

VAS is a **frozen reference implementation**.  
All existing behavior is correct and non-negotiable.

The **current ACTIVE phase MUST be explicitly stated in the prompt**.  
Only the ACTIVE phase may be implemented.

If unsure, **STOP and ASK**.

===============================
ABSOLUTE RULES (DO NOT VIOLATE)
===============================

- Do NOT use emojis in the code
- Do NOT modify MediaSoup behavior or lifecycle
- Do NOT modify FFmpeg invocation, flags, or control flow
- Do NOT modify RTSP ingest or reconnect logic
- Do NOT refactor existing architecture
- Do NOT rename services, files, or modules
- Do NOT change existing backend APIs unless explicitly instructed
- Do NOT introduce new frameworks, transports, or protocols
- Do NOT introduce HTTP / WebSocket / gRPC frame streaming
- Do NOT block, delay, or back-pressure video decode

If unsure, **STOP and ASK**.

===============================
PHASE STATUS (AUTHORITATIVE)
===============================

Phase 1 – Frame Ring Buffer: **COMPLETED**  
Phase 2 – Frame Export Interface: **COMPLETED**  
Phase 3.1 – Stream Agent Internal State Model: **COMPLETED**  
Phase 3.2 – Subscription Model & Frame Binding: **COMPLETED**  
Phase 3.3 – FPS Scheduling & Frame Selection: **COMPLETED**  
Phase 3.4 – Failure & Restart Semantics: **COMPLETED**  
Phase 4.1 – AI Model IPC & Inference Contract: **ACTIVE**

Only phases marked **ACTIVE** may be implemented.  
All other phases are frozen and must not be modified.

===============================
FEATURE FLAGS (MANDATORY)
===============================

All Phase 1 and Phase 2 logic MUST be guarded by:

AI_FRAME_EXPORT_ENABLED=false

When false:
- No frame buffers allocated
- No shared memory created
- No frame copies
- Zero overhead

===============================
ARCHITECTURE (NON-NEGOTIABLE)
===============================

Frame tap point is ONLY at the FFmpeg **decode boundary**:

RTSP → FFmpeg decode → RAW FRAME
                         ├── Recording (existing)
                         ├── MediaSoup Producer (existing)
                         └── Kernel Frame Path (Phase 1 / Phase 2)

Do NOT tap frames:
- after MediaSoup
- after recording
- inside AI code
- inside WebRTC code

===============================
PHASE 1 – FRAME RING BUFFER (COMPLETED)
===============================

Phase 1 exposed decoded video frames in a **read-only, non-blocking, bounded** manner so AI systems can observe frames **without impacting**:

- RTSP ingestion
- MediaSoup streaming
- recording
- multi-viewer behavior

Phase 1 behavior MUST remain unchanged.

===============================
PHASE 2 – FRAME EXPORT INTERFACE (COMPLETED)
===============================

Phase 2 exposes raw frames via **local shared memory only**.

Scope is STRICTLY limited to:
- frame.data (raw NV12 bytes)
- frame.meta (binary metadata header)
- write-only export from VAS
- pull-based, best-effort semantics
- local-host only visibility

===============================
PHASE 3 – RUTH AI CORE SERVICE (COMPLETED)
===============================

Phase 3 introduced **Ruth AI Core**, a control-plane orchestration service.

Phase 3 delivered:
- Stream Agent abstraction
- Subscription model
- FPS gating decision logic
- Failure isolation semantics

Phase 3 is now **FROZEN**.

===============================
PHASE 4 – AI MODEL RUNTIME (OVERVIEW)
===============================

Phase 4 introduces **AI Model Containers** as independent, long-lived runtimes.

PHASE 4 IS:
- Model inference runtime
- GPU-resident, long-lived containers
- Stateless per inference request
- Shared across multiple cameras

PHASE 4 IS NOT:
- Video pipeline
- Decoder
- RTSP / WebRTC controller
- Camera-specific container lifecycle
- Model orchestration logic (handled by Ruth AI Core)

===============================
PHASE 4.1 – IPC & INFERENCE CONTRACT (ACTIVE)
===============================

Phase 4.1 defines the **hard boundary contract** between:
- Ruth AI Core (caller)
- AI Model Containers (callees)

This phase is **DESIGN + INTERFACE IMPLEMENTATION ONLY**.

----------------
CONTAINER CARDINALITY
----------------

- Exactly **one container per model type**
- Containers are NOT per camera
- Containers are long-lived and pre-loaded
- Containers serve multiple cameras concurrently

----------------
CONCURRENCY RULES
----------------

- Containers MUST treat each inference request independently
- Containers MAY process requests concurrently
- Containers MUST NOT assume ordered delivery
- Containers MUST NOT rely on request sequencing
- Containers MUST NOT share mutable state across requests

Concurrency is an implementation detail of the container and must not
leak into the IPC contract.

----------------
IPC REQUIREMENTS (MANDATORY)
----------------

Each AI model container MUST:

- Expose exactly **one Unix Domain Socket (UDS) endpoint**
- Accept inference requests via this endpoint
- Return inference results synchronously
- Remain stateless per request
- Perform NO frame storage or buffering

----------------
INFERENCE REQUEST CONTRACT
----------------

Requests MUST include:
- frame reference (path or handle, not raw bytes)
- frame metadata
- camera_id
- model_id
- timestamp

Containers MUST NOT:
- Decode video
- Track per-camera state
- Maintain temporal context
- Perform FPS enforcement

----------------
INFERENCE RESPONSE CONTRACT
----------------

Responses MUST include:
- model_id
- camera_id
- frame_id or timestamp
- detections (model-defined schema)
- optional confidence scores

----------------
FRAME MEMORY RULES
----------------

- Frame references are READ-ONLY
- Containers MUST NOT mutate shared memory
- Containers MUST NOT retain frame references beyond request scope
- Containers MUST assume frames may disappear immediately after response

Containers have NO ownership of frame memory.

----------------
REQUEST LIFECYCLE RULES
----------------

- Exactly ONE request produces exactly ONE response
- No streaming responses
- No partial results
- No callbacks or async continuations
- No out-of-band signaling

Inference is strictly synchronous at the IPC boundary.

----------------
FORBIDDEN BEHAVIOR
----------------

Model containers MUST NOT:

- Access RTSP streams
- Access MediaSoup
- Read shared memory directly unless instructed
- Retry failed inference
- Queue frames
- Spawn per-camera workers
- Control GPU scheduling beyond their process

----------------
WHAT TO IMPLEMENT (PHASE 4.1 ONLY)
----------------

- IPC interface definition
- Request/response schema
- Container-side server skeleton
- Strict stateless inference handler
- Clear documentation of contract

----------------
WHAT NOT TO IMPLEMENT
----------------

- Model onboarding (Phase 4.2)
- GPU scheduling logic
- Model lifecycle management
- Container discovery
- Health checks or heartbeats
- Frontend integration
- Persistence

If unsure, **STOP and ASK**.

===============================
SUCCESS CRITERIA
===============================

Phase 4.1 is complete ONLY IF:
- IPC contract is explicit and enforced
- Containers are stateless per request
- One container serves many cameras
- No coupling to VAS internals exists
- No scheduling or orchestration logic leaks into containers

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diffs
- Fully reversible changes
- Well-commented where correctness is critical
- No behavior changes outside the ACTIVE phase

If any change risks violating these constraints, **STOP and ASK** before proceeding.