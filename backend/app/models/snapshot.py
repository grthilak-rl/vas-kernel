"""Snapshot model for single frame captures."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid


class Snapshot(Base):
    """Represents a snapshot (single frame) from a device."""

    __tablename__ = "snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    format = Column(String(10), default="jpg")
    source = Column(String(20), nullable=False)  # 'live' or 'historical'
    file_size = Column(Integer, nullable=True)  # File size in bytes

    # Optional: user_id for future auth (nullable for now)
    user_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps (matching BaseModel)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # FIXME: Temporarily disabled due to SQLAlchemy lazy loading issues with async
    # device = relationship("Device", backref="snapshots")

    def __repr__(self):
        return f"<Snapshot {self.file_path} at {self.timestamp}>"



