Phase 2 – Frame Export Interface
Internal Engineering Design Document

1. Purpose of Phase 2
Phase 2 introduces a safe, minimal, and strictly bounded interface that allows external processes on the same host to access decoded video frames produced by VAS.
This phase exists to answer one question only:
How can another local process read frames from VAS without affecting video ingestion, streaming, or recording?
Phase 2 does not introduce AI logic, model awareness, scheduling, or inference.

2. Position in the Overall Architecture
Before Phase 2 (Phase 1 Completed)
RTSP Camera
   ↓
FFmpeg Decode
   ↓
Frame Ring Buffer (in-memory, per camera)

Frames exist, but are internal-only.
After Phase 2
RTSP → FFmpeg → Frame Ring Buffer
                        ↓
                Frame Export Interface (NEW)
                        ↓
             External Local Consumers (future)

Phase 2 introduces read-only visibility, not control.

3. Core Design Principles
Pull-based only
External consumers must pull frames. VAS never pushes.
Read-only access
Exported frames cannot be modified or acknowledged.
Local-host only
No network transport. No HTTP. No WebSockets.
Zero impact when unused
If no consumer is attached, behavior is identical to Phase 1.
Failure isolation
A broken reader must not affect VAS.

4. What Phase 2 Explicitly Does NOT Do
❌ No AI models
❌ No model identifiers
❌ No FPS scheduling
❌ No subscriptions
❌ No persistence
❌ No GPU interaction
❌ No remote access
These belong to later phases.

5. Export Mechanism Overview
Phase 2 exposes frames using shared memory + metadata, not serialized transport.
Why Shared Memory
Zero-copy semantics
Predictable latency
No encoding overhead
Local-process safety

6. Shared Memory Layout
6.1 Base Path
/dev/shm/vas/

6.2 Per-Camera Structure
/dev/shm/vas/
  └── <camera_id>/
      ├── frame.meta
      └── frame.data

frame.data: raw frame bytes (NV12)
frame.meta: metadata describing the frame

7. Frame Metadata Contract
frame.meta contains:
frame_id (monotonic uint64)
timestamp_ns (monotonic)
width
height
pixel_format (NV12)
stride
data_size
Metadata is updated after frame data is written.

8. Frame Write Semantics (VAS Side)
VAS writes raw bytes into frame.data
VAS updates frame.meta
Write is atomic at metadata level
No locks exposed to consumers
If a consumer reads during a write:
It may get an old or new frame
Corruption is prevented by ordering

9. Frame Read Semantics (Consumer Side)
External consumers:
Poll frame.meta
Detect new frame_id
Read frame.data by reference
Skip frames freely
No acknowledgements are required.

10. Notification Strategy
Phase 2 uses polling only.
Reasons:
Simplicity
Predictability
Avoids signaling complexity
Optional optimizations (future, not required):
inotify on frame.meta

11. Failure & Isolation Guarantees
If a consumer:
Crashes
Stops reading
Reads too slowly
Then:
Frames continue updating
Memory usage remains bounded
VAS behavior is unchanged
VAS never waits for readers.

12. Lifecycle Rules
Camera Start
Shared memory files created
Export enabled only if feature flag is on
Camera Stop
Shared memory files removed
Readers naturally fail on next access

13. Feature Flag Control
Phase 2 is guarded by:
AI_FRAME_EXPORT_ENABLED=false (default)

When disabled:
No shared memory created
No extra work performed

14. Phase 2 Success Criteria
Phase 2 is complete when:
Frames are readable by an external local process
No performance impact when unused
No AI or model logic introduced
VAS remains the sole writer
Failure of consumers does not affect VAS

15. Format, Versioning, and Failure Semantics (Minimal)
This section defines non-negotiable constraints for the Phase 2 frame export interface. These rules exist to prevent implicit coupling, hidden assumptions, and future regressions.
15.1 Frame Metadata Format
frame.meta is a fixed-size binary header
Header begins with a version field
Field order and offsets are fixed per version
Metadata is written after frame data
Metadata write is the only synchronization mechanism
Readers must treat metadata as authoritative only after a full read.
15.2 Versioning Rules
Metadata header includes a version field
New versions may append fields only
Existing fields must never change meaning
Readers must ignore fields they do not understand
No migration or backward-compatibility guarantees are provided beyond this rule.
15.3 Failure Semantics
The system is best-effort by design.
If any of the following occur:
VAS crashes mid-write
Reader reads during a write
Shared memory files disappear
Then:
Readers may see stale or partial data
Readers must retry or skip frames
VAS never blocks, retries, or waits
No locks, acknowledgements, or recovery logic are permitted at this phase.

16. Phase Boundary Guarantee
Phase 2 ends at raw frame visibility.
Anything involving:
models
scheduling
inference
subscriptions
belongs strictly to Phase 3.

End of Phase 2 Design Document


