"""Stream model for active video streams."""
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class Stream(BaseModel):
    """Represents an active video stream."""
    
    __tablename__ = "streams"
    
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="inactive", index=True)  # inactive, starting, active, error
    producer_id = Column(String(255), nullable=True)
    router_id = Column(String(255), nullable=True)
    transport_id = Column(String(255), nullable=True)
    visibility = Column(String(50), default="private")  # private, public
    access_scopes = Column(JSON, nullable=True)
    stream_metadata = Column("metadata", JSON, nullable=True)  # For storing stream-specific data
    
    # Relationships
    # FIXME: Temporarily disabled due to SQLAlchemy lazy loading issues with async
    # device = relationship("Device", backref="streams")
    
    def __repr__(self):
        return f"<Stream {self.name} ({self.status})>"


