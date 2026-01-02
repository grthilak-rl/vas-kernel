You are implementing VAS Kernel & AI Platform Phases incrementally.

VAS is a frozen reference implementation.
All existing behavior is correct and non-negotiable.

The current ACTIVE phase MUST be explicitly stated in the prompt.
Only the ACTIVE phase may be implemented.

If unsure, STOP and ASK.

===============================
ABSOLUTE RULES (DO NOT VIOLATE)
===============================
• Do NOT use emojis in code
• Do NOT modify MediaSoup behavior or lifecycle
• Do NOT modify FFmpeg invocation, flags, or control flow
• Do NOT modify RTSP ingest or reconnect logic
• Do NOT refactor existing architecture
• Do NOT rename services, files, or modules
• Do NOT change existing backend APIs unless explicitly instructed
• Do NOT introduce new frameworks, transports, or protocols
• Do NOT introduce HTTP / WebSocket / gRPC frame streaming
• Do NOT block, delay, or back-pressure video decode

If unsure, STOP and ASK.

===============================
PHASE STATUS (AUTHORITATIVE)
===============================

Phase 1 – Frame Ring Buffer: COMPLETED
Phase 2 – Frame Export Interface: COMPLETED

Phase 3.1 – Stream Agent Internal State Model: COMPLETED
Phase 3.2 – Subscription Model & Frame Binding: COMPLETED
Phase 3.3 – FPS Scheduling & Frame Selection: COMPLETED
Phase 3.4 – Failure & Restart Semantics: COMPLETED

Phase 4.1 – AI Model IPC & Inference Contract: COMPLETED
Phase 4.2 – AI Model Runtime & Onboarding: COMPLETED

Phase 5.1 – AI Event Schema + Persistence: COMPLETED
Phase 5.2 – Snapshot / Clip Triggers: COMPLETED
Phase 5.3 – Read-only Backend APIs: COMPLETED

Phase 6.1 – Frontend Overlay Data Wiring: COMPLETED
Phase 6.2 – Frontend Overlay Rendering: COMPLETED
Phase 6.3 – Frontend UX Controls & Filters: COMPLETED

Phase 7 – Observability & Operational Controls: COMPLETED

Phase 8.1 – Backend Model Assignment APIs: ACTIVE

Only phases marked ACTIVE may be implemented.
All other phases are FROZEN and must not be modified.

===============================
FEATURE FLAGS (MANDATORY)
===============================

All Phase 1 and Phase 2 logic MUST be guarded by:

AI_FRAME_EXPORT_ENABLED=false

When false:
• No frame buffers allocated
• No shared memory created
• No frame copies
• Zero overhead

===============================
ARCHITECTURE (NON-NEGOTIABLE)
===============================

Frame tap point is ONLY at the FFmpeg decode boundary:

RTSP → FFmpeg decode → RAW FRAME
                         ├── Recording (existing)
                         ├── MediaSoup Producer (existing)
                         └── Kernel Frame Path (Phase 1 / Phase 2)

Do NOT tap frames:
• after MediaSoup
• after recording
• inside AI code
• inside WebRTC code

===============================
PHASE 8.1 – BACKEND MODEL ASSIGNMENT APIS (ACTIVE)
===============================

Phase 8.1 introduces **authoritative backend APIs** to record
camera ↔ AI model assignment intent.

Phase 8.1 IS:
• Backend control-plane APIs for assigning models to cameras
• Persistent storage of camera ↔ model intent
• Support for multiple models per camera
• Read/write APIs limited strictly to assignment state
• No execution or reconciliation logic
• No Ruth AI Core behavior changes

Phase 8.1 IS NOT:
• AI inference execution
• StreamAgent reconciliation (Phase 8.2)
• Model container lifecycle control
• Frontend UI (Phase 8.3)
• Overlay behavior (Phase 6)
• Snapshot / clip logic
• Observability changes (Phase 7)

Assignment APIs MUST:
• Be explicit and user-driven
• Persist intent durably
• Be idempotent and deterministic
• Never start, stop, or affect running inference
• Never communicate directly with model containers
• Never block or affect video or AI pipelines

===============================
FAILURE & ISOLATION (GLOBAL)
===============================

Inherited from Phase 3.4 and applies globally:
• VAS failure → outside AI scope
• AI Core failure → VAS unaffected
• Model container failure → isolated
• GPU failure → container-local
• Bad frame → request fails, no retry

The system MUST NOT:
• Retry inference
• Buffer frames
• Coordinate restarts
• Perform recovery logic
• Emit alerts automatically

Failures are fail-closed and lossy by design.

===============================
WHAT NOT TO IMPLEMENT (GLOBAL)
===============================
• Modifying existing VAS video paths
• AI inference inside VAS
• Network frame streaming
• Backend API breaking changes outside Phase 8.1
• StreamAgent reconciliation logic
• Model container lifecycle control
• Frontend UI or UX changes
• Automatic execution or enforcement
• Metrics, alerts, or observability changes
• Multi-host GPU orchestration

===============================
OUTPUT EXPECTATION
===============================
• Minimal, surgical diffs
• Fully reversible changes
• Well-commented where correctness is critical
• No behavior changes outside the ACTIVE phase

If any change risks violating these constraints,
STOP and ASK before proceeding.