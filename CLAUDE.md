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
Phase 4.1 – AI Model IPC & Inference Contract: **COMPLETED**  
Phase 4.2 – AI Model Runtime & Onboarding: **ACTIVE**

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
- GPU-backed, long-lived containers
- Stateless per inference request
- Shared across multiple cameras

PHASE 4 IS NOT:
- Video pipeline
- Decoder
- RTSP / WebRTC controller
- Camera-specific container lifecycle
- Model orchestration logic (handled by Ruth AI Core)

===============================
PHASE 4.2 – AI MODEL RUNTIME & ONBOARDING (ACTIVE)
===============================

Phase 4.2 introduces **real AI model execution** while preserving all guarantees from Phases 1–4.1.

This phase answers ONE question only:

**How are GPU-backed AI models safely loaded, executed, and operated as long-lived containers without impacting VAS or Ruth AI Core stability?**

The Phase 4.1 IPC contract is **LOCKED** and MUST NOT be changed.

----------------
WHAT PHASE 4.2 IS
----------------

- GPU-backed AI inference runtime
- Long-lived containers (one per model type)
- Real model loading (PyTorch / ONNX / TensorRT)
- Stateless per-request inference execution
- Concurrent inference across multiple cameras
- Strict adherence to Phase 4.1 IPC contract

----------------
WHAT PHASE 4.2 IS NOT
----------------

- Video decoding
- Frame scheduling or FPS enforcement
- Camera-aware logic
- Model orchestration (handled by Ruth AI Core)
- UI-facing logic
- Persistence layer
- Alerts, metrics, or monitoring

----------------
CONTAINER LIFECYCLE MODEL
----------------

Cardinality:
- Exactly **one container per model type**
- Containers are long-lived
- Containers are pre-started, not on-demand

Startup sequence:
1. Container starts
2. Model weights loaded into memory
3. GPU context initialized (if available)
4. IPC server starts listening
5. Container becomes READY

Model loading happens **once at startup**.

----------------
MODEL EXECUTION MODEL
----------------

For each inference request:
1. Validate IPC request
2. Read frame from shared memory (READ-ONLY)
3. Preprocess frame
4. Run inference (GPU or CPU fallback)
5. Post-process results
6. Return response

Each request is independent.

----------------
GPU USAGE RULES
----------------

- GPU memory allocated once at startup
- No per-request GPU initialization
- No GPU memory growth over time
- Models MUST tolerate dropped frames
- Inference latency variability is acceptable
- No global GPU scheduler introduced

----------------
GPU ABSENCE SEMANTICS (LOCKED)
----------------

If NO GPU is available at container startup:

- Container MUST still start
- Container MUST load model in CPU mode OR stub mode
- IPC server MUST still accept requests
- Requests MUST return valid error responses or degraded results
- Container MUST NOT crash or block

GPU absence:
- Does NOT affect VAS
- Does NOT affect Ruth AI Core
- Does NOT prevent model discovery
- Is NOT treated as a fatal error

----------------
CONCURRENCY MODEL
----------------

- Containers MAY process multiple requests concurrently
- Threading or async model is container-internal
- No shared mutable state between requests
- Model inference MUST be thread-safe or internally protected
- Concurrency is opaque to Ruth AI Core

----------------
FAILURE SEMANTICS (INHERITED)
----------------

Phase 4.2 strictly inherits Phase 3.4 failure semantics:

- Model crash → only that model unavailable
- Container crash → no effect on VAS
- GPU failure → container fails, others unaffected
- Bad frame → request fails, no retries

No recovery logic is added in this phase.

----------------
MODEL ONBOARDING (DEVELOPER EXPERIENCE)
----------------

A standard model template repository defines:
- Directory structure
- Entry points
- IPC wiring
- Inference handler skeleton

Junior AI engineers work **only** inside the template.

----------------
MODEL.YAML (SINGLE SOURCE OF TRUTH)
----------------

Each model includes a `model.yaml` defining:
- model_id
- model_name
- model_version
- supported_tasks
- input_format (e.g., NV12)
- expected_resolution
- resource_requirements (GPU memory hints)
- output_schema

No VAS or Ruth AI Core code changes are required.

----------------
MODEL DISCOVERY
----------------

- Models discovered via filesystem scan
- Example path:

/opt/ruth-ai/models/
  ├── yolov8/
  │   ├── model.yaml
  │   ├── container_image
  │   └── weights/
  └── pose_estimation/

Discovery is **startup-time only** in Phase 4.2.

----------------
SECURITY & ISOLATION
----------------

- Containers run as non-root
- Minimal filesystem access
- Read-only access to shared memory
- No network exposure beyond IPC

----------------
PHASE BOUNDARIES
----------------

Phase 4.2 ends at **successful inference execution**.

Explicitly excluded:
- Model hot-reload
- Canary deployments
- Metrics & monitoring
- Auto-scaling
- Multi-host GPU sharing

These belong to later phases.

===============================
SUCCESS CRITERIA
===============================

Phase 4.2 is complete ONLY IF:
- Real models run using Phase 4.1 IPC
- GPU memory remains stable over time
- Multiple cameras share one model container
- Model onboarding requires no VAS changes
- Failures remain isolated
- GPU absence is handled gracefully

===============================
OUTPUT EXPECTATION
===============================

- Minimal, surgical diffs
- Fully reversible changes
- Well-commented where correctness is critical
- No behavior changes outside the ACTIVE phase

If any change risks violating these constraints, **STOP and ASK** before proceeding.