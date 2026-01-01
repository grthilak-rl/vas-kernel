"""AI Event model for recording AI inference results.

Phase 5.1: Backend AI Integration (AI Event Schema + Persistence)

This model provides write-only, insert-only persistence for AI inference events.
Failures are silent (best-effort semantics).
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base
import uuid


class AIEvent(Base):
    """Represents an AI inference event from a model execution.

    Phase 5.1 Constraints:
    - Insert-only semantics (no updates, no deletes)
    - Best-effort persistence (failures are silent)
    - No coupling to inference execution
    - Model-agnostic payload storage
    """

    __tablename__ = "ai_events"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identifiers (required)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    model_id = Column(String(128), nullable=False, index=True)

    # Temporal data (required)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Frame correlation (optional - may not be available)
    frame_id = Column(Integer, nullable=True)

    # Model-specific inference results (opaque payload)
    # This is model-defined and varies by model type
    # Examples: bounding boxes, classifications, embeddings
    detections = Column(JSONB, nullable=False, default=dict)

    # Optional confidence scores
    # Model may provide overall confidence or per-detection confidence
    confidence = Column(Float, nullable=True)

    # Additional metadata (optional, extensible)
    # Examples: model version, inference latency, GPU usage, etc.
    # Note: column name is 'event_metadata' to avoid SQLAlchemy reserved word 'metadata'
    event_metadata = Column(JSONB, nullable=True, default=dict)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default="now()")

    # Composite indexes for common query patterns
    __table_args__ = (
        # Query pattern: all events for a camera within time range
        Index('ix_ai_events_camera_timestamp', 'camera_id', 'timestamp'),
        # Query pattern: all events for a model within time range
        Index('ix_ai_events_model_timestamp', 'model_id', 'timestamp'),
        # Query pattern: all events for a camera+model combination
        Index('ix_ai_events_camera_model', 'camera_id', 'model_id'),
    )

    # Relationships
    # FIXME: Temporarily disabled due to SQLAlchemy lazy loading issues with async
    # device = relationship("Device", backref="ai_events")

    def __repr__(self):
        return f"<AIEvent camera={self.camera_id} model={self.model_id} ts={self.timestamp}>"
