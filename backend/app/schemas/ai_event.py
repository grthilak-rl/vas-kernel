"""Pydantic schemas for AI Event API.

Phase 5.1: Backend AI Integration (AI Event Schema + Persistence)
Phase 5.3: Read-only Backend APIs (added list response schemas)
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


class AIEventCreate(BaseModel):
    """Schema for creating an AI event (write-only, insert-only).

    Phase 5.1 Constraints:
    - No validation of detections payload (model-specific)
    - Best-effort semantics (validation failures = silent drop)
    - No coupling to inference execution
    """

    # Core identifiers (required)
    camera_id: UUID = Field(..., description="Camera/device UUID")
    model_id: str = Field(..., min_length=1, max_length=128, description="Model identifier")

    # Temporal data (required)
    timestamp: datetime = Field(..., description="Event timestamp (timezone-aware)")

    # Frame correlation (optional)
    frame_id: Optional[int] = Field(None, description="Frame ID if available")

    # Model-specific inference results (opaque, model-defined)
    detections: Dict[str, Any] = Field(
        default_factory=dict,
        description="Model-specific detection payload (opaque JSON)"
    )

    # Optional confidence scores
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0.0-1.0)"
    )

    # Additional metadata (optional, extensible)
    event_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata (e.g., model version, inference latency)"
    )


class AIEventResponse(BaseModel):
    """Schema for AI event response (Phase 5.3: Read APIs)."""

    id: UUID
    camera_id: UUID
    model_id: str
    timestamp: datetime
    frame_id: Optional[int]
    detections: Dict[str, Any]
    confidence: Optional[float]
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class AIEventListResponse(BaseModel):
    """Schema for paginated list of AI events (Phase 5.3: Read APIs)."""

    events: List[AIEventResponse]
    total: int
    limit: int
    offset: int
