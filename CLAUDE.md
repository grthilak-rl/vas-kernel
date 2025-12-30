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
Phase 3.4 – Failure & Restart Semantics: **ACTIVE**

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
- Handle failure isolation semantics
- Dispatch frames to models (Phase 4+)

Stream Agent MUST NEVER:
- Store frames
- Buffer frames
- Control video pipelines

===============================
PHASE 3.4 – FAILURE & RESTART SEMANTICS (ACTIVE)
===============================

Phase 3.4 defines **strict failure isolation rules only**.

GOAL:
- Explicitly define what happens when components fail
- Ensure failures NEVER cascade across boundaries
- Encode failure behavior as **design invariants**, not recovery logic

This phase introduces **NO execution, NO retries, NO recovery**.

----------------
FAILURE DOMAINS
----------------

Failures are isolated by domain:

- VAS Kernel
- Frame Export Interface
- Ruth AI Core (global)
- Stream Agent (per camera)
- Subscription / Model (per model)

Each domain MUST fail independently.

----------------
FAILURE RULES (MANDATORY)
----------------

- VAS failure → outside Phase 3 scope
- Frame export loss → Stream Agent idles silently
- Ruth AI Core crash → VAS is completely unaffected
- Stream Agent crash → affects only that camera
- Model failure → affects only that subscription

----------------
FORBIDDEN FAILURE BEHAVIOR
----------------

The system MUST NOT:

- Retry inference
- Restart models
- Buffer frames for recovery
- Coordinate restarts across components
- Attempt graceful draining
- Persist failure state
- Emit alerts or notifications
- Perform health-based control decisions

----------------
ALLOWED BEHAVIOR
----------------

- Silent frame drops
- Stateless idling
- Lossy behavior
- Best-effort continuation

If something fails, it is simply **skipped**.

----------------
WHAT TO IMPLEMENT
----------------

- Explicit failure semantics documentation
- Defensive coding (fail-closed decisions)
- No-op behavior on failure paths
- Clear separation of failure domains

----------------
WHAT NOT TO IMPLEMENT
----------------

- Recovery logic
- Supervisors
- Watchdogs
- Health checks
- Circuit breakers
- Backoff logic
- Metrics or alerts
- Persistence

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

Phase 3.4 is complete ONLY IF:
- Failure behavior is explicitly defined
- Failures do not cascade
- No retries or recovery logic exists
- Ruth AI Core failure never impacts VAS
- Stream Agent failure scope is limited to one camera

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diffs
- Fully reversible changes
- Well-commented where correctness is critical
- No behavior changes outside the ACTIVE phase

If any change risks violating these constraints, **STOP and ASK** before proceeding.