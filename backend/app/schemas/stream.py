"""Stream schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class StreamCreate(BaseModel):
    """Schema for creating a stream."""
    device_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    visibility: str = Field(default="private")


class StreamUpdate(BaseModel):
    """Schema for updating a stream."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None
    visibility: Optional[str] = None
    access_scopes: Optional[Dict[str, Any]] = None


class StreamResponse(BaseModel):
    """Schema for stream response."""
    id: UUID
    device_id: UUID
    name: str
    status: str
    producer_id: Optional[str]
    router_id: Optional[str]
    transport_id: Optional[str]
    visibility: str
    access_scopes: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


