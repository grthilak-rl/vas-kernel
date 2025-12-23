"""Device model for cameras."""
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base
import uuid


class Device(Base):
    """Represents a camera device with RTSP URL."""
    
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    rtsp_url = Column(String(512), nullable=False, unique=True)
    is_active = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Device {self.name} ({self.rtsp_url})>"



