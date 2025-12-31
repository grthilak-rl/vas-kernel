"""
Phase 4.1 – AI Model IPC & Inference Contract
REQUEST / RESPONSE SCHEMA

This module defines the hard boundary contract between:
- Ruth AI Core (caller)
- AI Model Containers (callees)

PHASE 4.1 SCOPE:
- IPC schema definition
- Type safety for request/response
- No execution logic
- No model loading
- No GPU code

CRITICAL CONSTRAINTS:
- Containers are stateless per request
- One container serves many cameras
- No temporal context across requests
- No frame storage or buffering
- Strictly synchronous request/response
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class InferenceRequest:
    """
    Single inference request sent to an AI model container.

    LIFECYCLE:
    - Exactly ONE request produces exactly ONE response
    - No streaming responses
    - No partial results
    - No callbacks or async continuations

    CONCURRENCY:
    - Containers MUST treat each request independently
    - Containers MAY process requests concurrently
    - Containers MUST NOT assume ordered delivery
    - Containers MUST NOT rely on request sequencing

    FRAME MEMORY RULES:
    - frame_reference is READ-ONLY
    - Containers MUST NOT mutate shared memory
    - Containers MUST NOT retain frame_reference beyond request scope
    - Containers MUST assume frames may disappear immediately after response
    - Containers have NO ownership of frame memory

    REQUEST CONTRACT (MANDATORY FIELDS):
    - frame_reference: Path or handle to frame (NOT raw bytes)
    - frame_metadata: Frame header (width, height, format, timestamp)
    - camera_id: Source camera identifier
    - model_id: Target model identifier
    - timestamp: Request timestamp (for tracking, not inference)

    FORBIDDEN BEHAVIOR:
    - Do NOT decode video (frame is already decoded)
    - Do NOT track per-camera state
    - Do NOT maintain temporal context
    - Do NOT perform FPS enforcement
    - Do NOT retry failed inference
    - Do NOT queue frames
    """

    # Frame access (READ-ONLY reference, not raw bytes)
    frame_reference: str  # Path to shared memory or file (e.g., "/dev/shm/vas_frames_camera_1")

    # Frame metadata (binary header from Phase 2)
    frame_metadata: Dict[str, Any]  # Contains: width, height, format, pts, etc.

    # Request identity
    camera_id: str  # Source camera identifier
    model_id: str   # Target model identifier

    # Temporal tracking (for correlation, not inference logic)
    timestamp: float  # Unix timestamp (seconds since epoch)

    # Optional request-level configuration
    # Example: {"confidence_threshold": 0.7, "nms_iou": 0.5}
    # Containers MAY ignore this if not applicable
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate request on construction."""
        if not self.frame_reference or not isinstance(self.frame_reference, str):
            raise ValueError("frame_reference must be a non-empty string path")

        if not self.frame_metadata or not isinstance(self.frame_metadata, dict):
            raise ValueError("frame_metadata must be a non-empty dictionary")

        if not self.camera_id or not isinstance(self.camera_id, str):
            raise ValueError("camera_id must be a non-empty string")

        if not self.model_id or not isinstance(self.model_id, str):
            raise ValueError("model_id must be a non-empty string")

        if not isinstance(self.timestamp, (int, float)) or self.timestamp <= 0:
            raise ValueError("timestamp must be a positive number")


@dataclass
class Detection:
    """
    Single detection result from inference.

    This is a model-defined schema example.
    Actual detection schema depends on the model type.

    OBJECT DETECTION EXAMPLE:
    - class_id: Integer class identifier
    - class_name: Human-readable class name
    - confidence: Confidence score (0.0 to 1.0)
    - bbox: Bounding box [x_min, y_min, x_max, y_max] (normalized 0-1)

    OTHER MODEL TYPES:
    - Classification: only class_id, class_name, confidence
    - Segmentation: add segmentation_mask reference
    - Pose estimation: add keypoints array
    - Custom models: define custom schema

    IMPORTANT:
    - This is an EXAMPLE schema
    - Each model type MAY define its own detection format
    - Containers MUST document their detection schema
    """

    # Detection identity
    class_id: int
    class_name: str

    # Detection confidence (0.0 to 1.0)
    confidence: float

    # Bounding box (normalized coordinates: 0.0 to 1.0)
    # Format: [x_min, y_min, x_max, y_max]
    # Top-left origin: (0, 0) is top-left, (1, 1) is bottom-right
    bbox: List[float]  # [x_min, y_min, x_max, y_max]

    # Optional tracking ID (for multi-object tracking models)
    track_id: Optional[int] = None

    def __post_init__(self):
        """Validate detection on construction."""
        if not isinstance(self.class_id, int) or self.class_id < 0:
            raise ValueError("class_id must be a non-negative integer")

        if not self.class_name or not isinstance(self.class_name, str):
            raise ValueError("class_name must be a non-empty string")

        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")

        if not isinstance(self.bbox, list) or len(self.bbox) != 4:
            raise ValueError("bbox must be a list of 4 floats [x_min, y_min, x_max, y_max]")

        for coord in self.bbox:
            if not isinstance(coord, (int, float)) or not (0.0 <= coord <= 1.0):
                raise ValueError("bbox coordinates must be normalized between 0.0 and 1.0")


@dataclass
class InferenceResponse:
    """
    Single inference response returned from an AI model container.

    LIFECYCLE:
    - Exactly ONE request produces exactly ONE response
    - Response MUST be returned synchronously
    - No streaming, no partial results, no async continuations

    RESPONSE CONTRACT (MANDATORY FIELDS):
    - model_id: Echo from request (for correlation)
    - camera_id: Echo from request (for correlation)
    - frame_id: Frame identifier or timestamp (for correlation)
    - detections: List of Detection objects (may be empty)

    FAILURE SEMANTICS:
    - Empty detections list means: no objects detected (valid response)
    - Exception during inference: container SHOULD return error response
    - Container MUST NOT retry inference internally
    - Container MUST NOT cache or queue failed requests

    FORBIDDEN BEHAVIOR:
    - Do NOT return partial results
    - Do NOT buffer responses
    - Do NOT perform temporal aggregation (e.g., multi-frame tracking)
    - Do NOT maintain response history
    """

    # Response identity (echo from request)
    model_id: str
    camera_id: str

    # Frame correlation (echo from request metadata)
    # This may be frame_id (int) or timestamp (float)
    frame_id: Any  # Flexible type for correlation

    # Inference results (model-defined schema)
    # Empty list is valid (no detections)
    detections: List[Detection]

    # Optional inference metadata
    # Example: {"inference_time_ms": 42.3, "gpu_id": 0}
    metadata: Optional[Dict[str, Any]] = None

    # Optional error information (if inference failed)
    # If error is present, detections SHOULD be empty
    error: Optional[str] = None

    def __post_init__(self):
        """Validate response on construction."""
        if not self.model_id or not isinstance(self.model_id, str):
            raise ValueError("model_id must be a non-empty string")

        if not self.camera_id or not isinstance(self.camera_id, str):
            raise ValueError("camera_id must be a non-empty string")

        if not isinstance(self.detections, list):
            raise ValueError("detections must be a list")

        # Validate all detections
        for detection in self.detections:
            if not isinstance(detection, Detection):
                raise ValueError("All detections must be Detection objects")


# IPC TRANSPORT NOTES:
#
# Phase 4.1 uses Unix Domain Sockets (UDS) for IPC.
#
# SERIALIZATION:
# - Requests and responses are serialized to JSON
# - Binary frame data is NOT transferred via IPC
# - Only frame references (paths) are transferred
#
# PROTOCOL:
# - Length-prefixed JSON messages
# - Format: [4-byte length][JSON payload]
# - Network byte order (big-endian)
#
# CONNECTION MODEL:
# - One persistent UDS endpoint per container
# - Container listens on: /tmp/vas_model_{model_id}.sock
# - Ruth AI Core connects per request (or uses connection pool)
# - No long-lived connections required
#
# CONCURRENCY:
# - Container MUST handle concurrent connections
# - Each connection MAY have one in-flight request
# - Container chooses threading/async model (implementation detail)
