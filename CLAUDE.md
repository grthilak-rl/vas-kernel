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
Phase 6.3 – Frontend UX Controls & Filters: ACTIVE

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
PHASE 6.3 – FRONTEND UX CONTROLS & FILTERS (ACTIVE)
===============================

Phase 6.3 introduces **user-controlled visualization controls** for AI overlays.

Phase 6.3 IS:
• UI toggles to enable / disable AI overlays
• Confidence threshold filtering (client-side only)
• Per-model overlay visibility toggles (visual only)
• Overlay styling controls (opacity, color, label visibility)
• Local UI state or persisted user preferences
• Purely frontend-side behavior

Phase 6.3 IS NOT:
• AI model selection for cameras
• AI inference control or triggering
• Backend API changes
• Ruth AI Core interactions
• Camera ↔ model subscription changes
• Overlay rendering logic (Phase 6.2)
• Data fetching logic (Phase 6.1)

Controls MUST:
• Be optional and user-driven
• Default to overlays OFF
• Never affect AI execution or persistence
• Never block video playback
• Apply filters client-side only

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
• Backend API breaking changes
• AI model selection UI
• Model subscription management
• Backend-side filtering or aggregation
• Metrics, alerts, observability (until Phase 7)
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