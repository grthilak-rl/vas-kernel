You are implementing **Phase 1 – Frame Ring Buffer** for VAS.

VAS is a **frozen reference implementation**. You MUST treat all existing behavior as correct and non-negotiable.

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
PHASE 1 GOAL
===============================

Expose **decoded video frames** from VAS in a **read-only, non-blocking, bounded** way so AI systems can observe frames **without impacting**:

- RTSP ingestion
- MediaSoup streaming
- recording
- multi-viewer behavior

VAS must behave IDENTICALLY when Phase 1 is disabled.

===============================
FEATURE FLAG (MANDATORY)
===============================

All Phase 1 logic MUST be guarded by:

AI_FRAME_EXPORT_ENABLED=false

When false:
- No frame buffers allocated
- No frame copies
- Zero overhead

===============================
ARCHITECTURE (NON-NEGOTIABLE)
===============================

Frame tap point is ONLY at the FFmpeg **decode boundary**:

RTSP → FFmpeg decode → RAW FRAME
                         ├── Recording (existing)
                         ├── MediaSoup Producer (existing)
                         └── Frame Ring Buffer (NEW)

Do NOT tap frames:
- after MediaSoup
- after recording
- inside AI code
- inside WebRTC code

===============================
FRAME BUFFER DESIGN
===============================

- One ring buffer PER CAMERA
- Fixed size (configurable)
- Overwrite-safe
- Non-blocking writer
- No locks in decode path

Frame loss is acceptable. Video disruption is not.

===============================
FRAME DATA MODEL
===============================

Each frame entry MUST include:

frame_id        (monotonic per camera)
timestamp       (PTS or monotonic clock)
camera_id
width
height
pixel_format
stride
raw pixel buffer (by reference)

No encoding. No serialization.

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
WHAT TO IMPLEMENT (ONLY THIS)
===============================

- Frame ring buffer data structure
- Buffer lifecycle tied to camera stream start/stop
- Non-blocking frame copy at decode boundary
- Feature-flag guarded activation
- Minimal test-only frame reader (optional)

===============================
WHAT NOT TO IMPLEMENT
===============================

- AI models or inference
- Scheduling logic
- GPU work
- Frontend overlays
- Network APIs
- Multi-host support

===============================
SUCCESS CRITERIA
===============================

Phase 1 is complete ONLY IF:

- VAS behaves exactly as before with AI disabled
- With AI enabled:
  - memory usage is bounded
  - decode path never blocks
- Multi-viewer streaming still works
- Frame drops under load do not affect video

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diff
- Fully reversible
- Well-commented where correctness is critical
- No behavior changes outside Phase 1

If any change risks violating these constraints, STOP and ASK before proceeding.