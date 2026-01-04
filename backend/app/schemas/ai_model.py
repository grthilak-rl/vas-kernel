"""AI Model Registry schemas for request/response validation.

Phase 5.4: AI Model Registry & Discovery APIs

These schemas define the API contract for AI model metadata discovery.
All operations are read-only from the caller's perspective and serve
metadata only (NOT runtime state).
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AIModelResponse(BaseModel):
    """Schema for AI model metadata response.

    Phase 5.4: This represents persistent model registry metadata.
    It does NOT reflect runtime state, container status, or execution state.

    Used by:
    - Frontend model selection UI (Phase 8.3)
    - Backend validation for model assignments (Phase 8.1)
    - Ruth AI Core model discovery (future phases)
    """
    model_id: str = Field(..., description="Unique model identifier (immutable)")
    name: str = Field(..., description="Human-readable model name")
    description: Optional[str] = Field(None, description="Detailed model description")
    supported_tasks: List[str] = Field(
        default_factory=list,
        description="Array of supported task types (e.g., ['object_detection'])"
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON schema for model-specific configuration (optional)"
    )
    enabled: bool = Field(..., description="Whether model is available for assignment")
    created_at: datetime = Field(..., description="Model registration timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class AIModelListResponse(BaseModel):
    """Schema for list of AI models.

    Phase 5.4: Provides simple list response (no pagination needed for models).
    Model count is expected to be small (< 100) so pagination is not required.
    """
    models: List[AIModelResponse] = Field(..., description="List of registered AI models")
    total: int = Field(..., description="Total number of models returned")
