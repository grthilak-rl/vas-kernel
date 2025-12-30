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
Phase 3.2 – Subscription Model & Frame Binding: **ACTIVE**

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
PHASE 3 – RUTH AI CORE SERVICE (DESIGN OVERVIEW)
===============================

Phase 3 introduces **Ruth AI Core**, a control-plane orchestration service.

PHASE 3 IS:
- Camera ↔ model orchestration
- Per-model FPS enforcement (future)
- Frame routing to model containers (future)
- Metadata event generation (future)

PHASE 3 IS NOT:
- Video pipeline
- Decoder
- MediaSoup participant
- RTSP / WebRTC controller
- AI model runtime
- GPU scheduler

===============================
PHASE 3 CORE ABSTRACTION: STREAM AGENT
===============================

- Exactly **one Stream Agent per camera**
- stream_agent_id == camera_id
- Logical entity (NOT a worker, thread, or process)

Stream Agent responsibilities (cumulative across Phase 3):
- Maintain model subscriptions
- Bind to frame export (read-only)
- Enforce per-model FPS limits (Phase 3.3+)
- Dispatch frames to models (Phase 3.3+)

Stream Agent MUST NEVER:
- Store frames
- Buffer frames
- Control video pipelines

===============================
PHASE 3.2 – SUBSCRIPTION MODEL & FRAME BINDING (ACTIVE)
===============================

Phase 3.2 introduces **subscription state only**.

GOAL:
- Represent which models are attached to which camera
- Bind Stream Agent to a frame source (read-only)
- Prepare for future scheduling without implementing it

----------------
WHAT TO IMPLEMENT
----------------

- Subscription data model
- Add/remove subscription operations (pure state mutation)
- Logical frame source reference (identifier/path only)

----------------
WHAT NOT TO IMPLEMENT
----------------

- Frame reads
- FPS enforcement
- Scheduling loops
- Timers or sleeps
- Background threads or async tasks
- IPC or shared memory access
- Model execution
- Error retries or recovery
- Persistence

----------------
SUBSCRIPTION RULES
----------------

- Subscription identity: (camera_id, model_id)
- Multiple models per camera allowed
- Add/remove is immediate and non-blocking
- No draining or graceful shutdown
- In-flight work (future phases) may be dropped

----------------
FRAME SOURCE BINDING RULES
----------------

- Stream Agent may store identifiers or paths only
- MUST NOT open, read, or watch shared memory
- MUST NOT react to frame availability

If unsure, **STOP and ASK**.

===============================
WHAT NOT TO IMPLEMENT (GLOBAL)
===============================

- AI inference engines
- Model containers (Phase 4)
- Model lifecycle management
- GPU work
- Persistent storage
- Frontend overlays
- Alerts or notifications
- Network APIs
- Multi-host support

===============================
SUCCESS CRITERIA
===============================

Phase 1 remains valid ONLY IF:
- VAS behaves exactly as before with AI disabled
- Decode path never blocks
- Multi-viewer streaming still works

Phase 2 remains valid ONLY IF:
- Frames visible via shared memory when enabled
- No performance impact when unused
- VAS remains sole writer
- Reader failure does not affect VAS

Phase 3.2 is complete ONLY IF:
- Subscriptions are represented as pure state
- No frame access occurs
- No scheduling logic exists
- No execution side effects occur

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diffs
- Fully reversible changes
- Well-commented where correctness is critical
- No behavior changes outside the ACTIVE phase

If any change risks violating these constraints, **STOP and ASK** before proceeding.