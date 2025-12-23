"""Recording model for video recordings."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Recording(BaseModel):
    """Represents a video recording/chunk."""
    
    __tablename__ = "recordings"
    
    stream_id = Column(UUID(as_uuid=True), ForeignKey("streams.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in seconds
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    format = Column(String(50), default="hls")  # hls, mp4, etc.
    recording_metadata = Column("metadata", Text, nullable=True)  # HLS playlist path or other metadata
    
    # Relationships
    stream = relationship("Stream", backref="recordings")
    
    def __repr__(self):
        return f"<Recording {self.file_path} ({self.duration}s)>"


