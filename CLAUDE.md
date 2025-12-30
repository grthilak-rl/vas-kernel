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
Phase 3.3 – FPS Scheduling & Frame Selection: **ACTIVE**

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
- Per-model FPS enforcement
- Frame routing to model runtimes
- Metadata event generation

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
- Select frames per subscription
- Enforce per-model FPS limits
- Dispatch frames to models (future phases)

Stream Agent MUST NEVER:
- Store frames
- Buffer frames
- Control video pipelines

===============================
PHASE 3.3 – FPS SCHEDULING & FRAME SELECTION (ACTIVE)
===============================

Phase 3.3 introduces **decision-only frame gating**.

GOAL:
- Decide whether a frame SHOULD be dispatched to a subscription
- Enforce FPS as a **maximum**, never a target
- Allow unlimited frame drops

This phase ends at **dispatch eligibility decision**.

----------------
WHAT TO IMPLEMENT
----------------

- Per-subscription FPS gating logic
- Frame eligibility checks using:
  - last_dispatched_timestamp OR
  - last_dispatched_frame_id
- Stateless or minimal per-subscription bookkeeping
- Pure decision logic (allow / skip)

----------------
WHAT NOT TO IMPLEMENT
----------------

- Frame reads
- Shared memory access
- Timers, sleeps, or scheduling loops
- Queues or buffers
- Background threads or async workers
- Frame dispatch
- Model execution
- Error retries or recovery
- Persistence

----------------
FPS ENFORCEMENT RULES
----------------

- FPS is a MAXIMUM, not a guarantee
- Frames may be skipped freely
- No catch-up behavior
- No token buckets
- No fairness logic
- No time-based sleeps

----------------
FRAME SELECTION RULES
----------------

- Each subscription is evaluated independently
- A frame allowed for one model may be skipped for another
- Decisions are instantaneous and non-blocking
- Dropping frames is expected and correct

----------------
FAILURE & ISOLATION RULES
----------------

- Scheduler failure affects only that subscription
- Stream Agent failure affects only that camera
- Ruth AI Core failure does NOT affect VAS
- No retries, restarts, or recovery coordination

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

Phase 3.3 is complete ONLY IF:
- FPS gating exists as pure decision logic
- Frames are skipped without side effects
- No scheduling loops or timers exist
- No frame access occurs
- No dispatch or execution occurs

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diffs
- Fully reversible changes
- Well-commented where correctness is critical
- No behavior changes outside the ACTIVE phase

If any change risks violating these constraints, **STOP and ASK** before proceeding.