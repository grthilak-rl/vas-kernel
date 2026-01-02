"""AI Model Assignment model for camera-to-model assignment intent.

Phase 8.1: Backend Model Assignment APIs

This model represents the authoritative control-plane state for which AI models
are intended to run on which cameras. It stores INTENT only, not execution state.

Critical constraints:
- Does NOT trigger model execution
- Does NOT communicate with Ruth AI Core or model containers
- Does NOT affect video pipelines
- Purely persistence layer for user-defined assignments
"""
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from database import Base
import uuid


class AIModelAssignment(Base):
    """Represents camera-to-AI-model assignment intent (Phase 8.1).

    Phase 8.1 Constraints:
    - Stores intent only (what SHOULD run, not what IS running)
    - No execution semantics
    - No lifecycle control
    - No side effects beyond persistence
    - Idempotent operations

    Assignment lifecycle:
    - enabled=True: Model is intended to run on camera (intent recorded)
    - enabled=False: Assignment disabled (soft delete, intent preserved)
    - Deleted row: Assignment removed entirely (intent removed)

    Multiple models per camera are supported.
    Each camera+model pair is unique.
    """

    __tablename__ = "ai_model_assignments"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identifiers (required)
    # camera_id must reference an existing device
    camera_id = Column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # model_id is a string identifier for the AI model
    # This should match model identifiers used in Ruth AI Core
    # but Phase 8.1 does NOT validate against running models
    model_id = Column(String(128), nullable=False, index=True)

    # Assignment state
    # enabled=True means the model SHOULD run on this camera (intent)
    # enabled=False means assignment is disabled (soft delete)
    # This does NOT reflect actual execution state
    enabled = Column(Boolean, nullable=False, default=True)

    # Optional assignment parameters
    # These are hints for future execution (Phase 8.2+), not enforced in Phase 8.1

    # desired_fps: Requested inference frame rate (frames per second)
    # None means use model default or system default
    desired_fps = Column(Integer, nullable=True)

    # priority: Execution priority hint (higher = more important)
    # None means default priority
    # Future phases may use this for resource allocation
    priority = Column(Integer, nullable=True)

    # parameters: Extensible model-specific configuration (JSONB)
    # Examples: confidence thresholds, region of interest, etc.
    # Interpretation is model-specific and deferred to execution phase
    parameters = Column(JSONB, nullable=True, default=dict)

    # Audit timestamps
    # Note: Using server_default for created_at to match existing pattern
    from sqlalchemy import DateTime, func
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constraints
    __table_args__ = (
        # Each camera+model pair must be unique
        # This allows multiple models per camera but prevents duplicate assignments
        UniqueConstraint('camera_id', 'model_id', name='uq_camera_model'),

        # Composite indexes for common query patterns
        # Query pattern: all assignments for a camera
        Index('ix_ai_model_assignments_camera', 'camera_id'),

        # Query pattern: all cameras assigned to a model
        Index('ix_ai_model_assignments_model', 'model_id'),

        # Query pattern: all enabled assignments
        Index('ix_ai_model_assignments_enabled', 'enabled'),

        # Query pattern: enabled assignments for a camera
        Index('ix_ai_model_assignments_camera_enabled', 'camera_id', 'enabled'),
    )

    def __repr__(self):
        return f"<AIModelAssignment camera={self.camera_id} model={self.model_id} enabled={self.enabled}>"
