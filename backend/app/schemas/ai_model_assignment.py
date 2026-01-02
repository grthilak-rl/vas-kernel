"""AI Model Assignment schemas for request/response validation.

Phase 8.1: Backend Model Assignment APIs

These schemas define the API contract for camera-to-model assignment operations.
All operations are control-plane only and do NOT trigger execution.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class AIModelAssignmentCreate(BaseModel):
    """Schema for creating a camera-to-model assignment.

    Phase 8.1: This represents user intent to assign a model to a camera.
    It does NOT trigger model execution.
    """
    camera_id: UUID = Field(..., description="UUID of the camera/device")
    model_id: str = Field(..., min_length=1, max_length=128, description="AI model identifier")
    enabled: bool = Field(default=True, description="Whether assignment is enabled (default: true)")
    desired_fps: Optional[int] = Field(None, ge=1, le=30, description="Desired inference FPS (1-30, optional)")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Priority hint (0-100, higher = more important)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Model-specific parameters (optional)")

    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v):
        """Ensure parameters is a dict if provided."""
        if v is not None and not isinstance(v, dict):
            raise ValueError('parameters must be a dictionary')
        return v or {}


class AIModelAssignmentUpdate(BaseModel):
    """Schema for updating an existing assignment.

    Phase 8.1: All fields are optional.
    Only provided fields will be updated (PATCH semantics).
    """
    enabled: Optional[bool] = Field(None, description="Whether assignment is enabled")
    desired_fps: Optional[int] = Field(None, ge=1, le=30, description="Desired inference FPS (1-30)")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Priority hint (0-100)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Model-specific parameters")

    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v):
        """Ensure parameters is a dict if provided."""
        if v is not None and not isinstance(v, dict):
            raise ValueError('parameters must be a dictionary')
        return v


class AIModelAssignmentResponse(BaseModel):
    """Schema for assignment response.

    Phase 8.1: This represents stored assignment intent.
    It does NOT reflect execution state.
    """
    id: UUID
    camera_id: UUID
    model_id: str
    enabled: bool
    desired_fps: Optional[int]
    priority: Optional[int]
    parameters: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AIModelAssignmentListResponse(BaseModel):
    """Schema for paginated list of assignments.

    Phase 8.1: Provides standard pagination metadata.
    """
    assignments: List[AIModelAssignmentResponse]
    total: int
    limit: int
    offset: int
