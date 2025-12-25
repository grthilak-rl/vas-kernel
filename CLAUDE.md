You are implementing **VAS Kernel Phases** incrementally.

VAS is a **frozen reference implementation**.  
All existing behavior is correct and non-negotiable.

Current active phase will be explicitly stated in the prompt.
If unsure, STOP and ASK.

===============================
ABSOLUTE RULES (DO NOT VIOLATE)
===============================

- Do NOT use emojis in the code
- Do NOT modify MediaSoup behavior or lifecycle
- Do NOT modify FFmpeg invocation or control flow
- Do NOT modify RTSP reconnect logic
- Do NOT refactor existing architecture
- Do NOT rename services, files, or modules
- Do NOT change backend APIs
- Do NOT introduce new frameworks, transports, or protocols
- Do NOT introduce HTTP / WebSocket / gRPC frame streaming
- Do NOT introduce AI inference or GPU work
- Do NOT add frontend changes
- Do NOT block, delay, or back-pressure video decode

If unsure, STOP and ASK.

===============================
PHASE STATUS
===============================

Phase 1 – Frame Ring Buffer: **COMPLETED**  
Phase 2 – Frame Export Interface: **ACTIVE**

Only the ACTIVE phase may be implemented.

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
                         └── Kernel Frame Path (Phase 1/2)

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
PHASE 2 – FRAME EXPORT INTERFACE (ACTIVE)
===============================

Phase 2 exposes raw frames via **local shared memory only**.

Scope is STRICTLY limited to:
- frame.data (raw NV12 bytes)
- frame.meta (binary metadata header)
- write-only export from VAS
- pull-based, best-effort semantics
- local-host only visibility

===============================
WHAT TO IMPLEMENT (PHASE-DEPENDENT)
===============================

Phase 1 (COMPLETED):
- Frame ring buffer data structure
- Buffer lifecycle tied to camera stream start/stop
- Non-blocking frame copy at decode boundary

Phase 2 (ACTIVE):
- Shared memory frame export
- frame.data + frame.meta layout
- Best-effort write semantics
- Feature-flag guarded activation

===============================
WHAT NOT TO IMPLEMENT (GLOBAL)
===============================

- AI models or inference
- Model identifiers or subscriptions
- FPS scheduling
- GPU work
- Frontend overlays
- Network APIs
- Multi-host support
- Persistence
- Any Phase 3+ behavior

===============================
MEMORY & CONCURRENCY
===============================

- Pre-allocated buffers only
- No dynamic allocation in decode hot path
- VAS owns memory; readers borrow it
- Single writer (decode)
- Zero or more readers (best-effort)
- Reader slowness must never affect writer

===============================
SUCCESS CRITERIA
===============================

Phase 1 remains valid ONLY IF:
- VAS behaves exactly as before with AI disabled
- Decode path never blocks
- Multi-viewer streaming still works

Phase 2 is complete ONLY IF:
- Frames are visible via shared memory when enabled
- No performance impact when unused
- No AI or scheduling logic introduced
- VAS remains sole writer
- Failure of readers does not affect VAS

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diff
- Fully reversible
- Well-commented where correctness is critical
- No behavior changes outside the active phase

If any change risks violating these constraints, STOP and ASK before proceeding.