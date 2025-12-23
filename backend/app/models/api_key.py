"""API Key model for authentication."""
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid


class ApiKey(Base):
    """Represents an API key for authenticating third-party applications."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ApiKey {self.name} (active={self.is_active})>"
