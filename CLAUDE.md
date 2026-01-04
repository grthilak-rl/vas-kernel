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
Phase 4.3 – Ruth AI Core Integration & Routing: COMPLETED
Phase 4.4 – Ruth AI Model Runtime Base Image: COMPLETED

Phase 5.1 – AI Event Schema + Persistence: COMPLETED
Phase 5.2 – Snapshot / Clip Triggers: COMPLETED
Phase 5.3 – Read-only Backend APIs: COMPLETED
Phase 5.4 – AI Model Registry & Discovery APIs: ACTIVE

Phase 6.1 – Frontend Overlay Data Wiring: COMPLETED
Phase 6.2 – Frontend Overlay Rendering: COMPLETED
Phase 6.3 – Frontend UX Controls & Filters: COMPLETED

Phase 7 – Observability & Operational Controls: COMPLETED

Phase 8.1 – Backend Model Assignment APIs: COMPLETED
Phase 8.2 – Ruth AI Core Subscription Reconciliation: COMPLETED
Phase 8.3 – Frontend Model Selection UI: COMPLETED

Only phases marked ACTIVE may be implemented.
All other phases are FROZEN and must not be modified.

===============================
PHASE 5.4 – AI MODEL REGISTRY & DISCOVERY APIS (ACTIVE)
===============================

Phase 5.4 introduces a **persistent, backend-managed registry**
of all AI models available to the system.

Phase 5.4 IS:
• Backend persistence of AI model metadata
• Canonical source of truth for “which models exist”
• Read-only discovery APIs for frontend and Ruth AI Core
• Validation layer for model assignments
• Environment-level model availability (not per-camera, not per-project)
• Explicit enable / disable control for models

Phase 5.4 IS NOT:
• Model execution or inference
• Container lifecycle management
• Filesystem-based model discovery
• Docker introspection
• Assignment logic (Phase 8.1)
• Subscription reconciliation (Phase 8.2)
• Frontend UI rendering
• Business analytics or reporting

Registry MUST:
• Treat models as declarative metadata
• Remain independent of runtime state
• Be safe to modify without impacting live inference
• Fail closed (unknown model = invalid assignment)

===============================
FAILURE & ISOLATION (GLOBAL)
===============================

Inherited rules apply unchanged:
• VAS failure → outside AI scope
• AI Core failure → VAS unaffected
• Model container failure → isolated
• GPU failure → container-local
• Bad frame → request fails, no retry

The system MUST NOT:
• Retry inference automatically
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
• Backend API changes (unless explicitly allowed)
• Reconciliation or execution logic (unless explicitly allowed)
• Model onboarding or loading logic (unless explicitly allowed)
• Model container lifecycle control (unless explicitly allowed)
• Observability or metrics changes (unless explicitly allowed)
• Alerting or notification systems
• Business analytics or violation reports
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