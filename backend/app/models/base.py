"""Base model with common fields."""
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
import uuid


class BaseModel(DeclarativeBase):
    """Base model with common fields."""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())



