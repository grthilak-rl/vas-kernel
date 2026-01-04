"""AI Model Registry model for persistent model metadata.

Phase 5.4: AI Model Registry & Discovery APIs

This model provides the canonical source of truth for which AI models exist
in the system and their capabilities. It is environment-scoped (global),
not per-camera or per-project.

Critical constraints:
- Stores declarative metadata only (NOT runtime state)
- Independent of container lifecycle
- Independent of inference execution
- Does NOT discover or manage containers
- Does NOT read filesystem or Docker state
- Safe to modify without affecting live inference
- Fail-closed validation (unknown model_id = invalid assignment)
"""
from sqlalchemy import Column, String, Boolean, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class AIModel(Base):
    """Represents an AI model registered in the system (Phase 5.4).

    Phase 5.4 Constraints:
    - Stores metadata only (no execution semantics)
    - Environment-scoped (global, not per-camera)
    - Models registered once per deployment
    - Assignments reference model_id from this registry
    - Disabled models can still be queried but marked enabled=false
    - No automatic discovery or synchronization with runtime

    Registry lifecycle:
    - Models are manually registered (outside Phase 5.4 scope)
    - enabled=True: Model is available for assignment
    - enabled=False: Model exists but cannot be assigned (soft disable)
    - Deleted row: Model removed entirely (assignments may become orphaned)

    This is the authoritative source for model existence validation.
    """

    __tablename__ = "ai_models"

    # Primary key: immutable model identifier
    # This is the canonical ID used in assignments, events, and Ruth AI Core
    # Must be unique and should never change once created
    # Format examples: "ruth-person-detection-v1", "custom-face-recognition"
    model_id = Column(String(128), primary_key=True, nullable=False)

    # Human-readable display name
    # Examples: "Ruth Person Detection v1.0", "Custom Face Recognition"
    name = Column(String(256), nullable=False)

    # Detailed description of model purpose and capabilities
    # Displayed in frontend model selection UI
    description = Column(Text, nullable=True)

    # Array of supported task types (stored as JSON array)
    # Examples: ["object_detection"], ["face_recognition", "person_detection"]
    # Used for filtering and capability discovery
    # Frontend can filter models by required task type
    supported_tasks = Column(JSONB, nullable=False, default=list)

    # JSON schema for model-specific configuration parameters
    # Defines valid structure for parameters in ai_model_assignments.parameters
    # Optional: None means model accepts no configuration
    # Example: {"type": "object", "properties": {"confidence_threshold": {"type": "number"}}}
    config_schema = Column(JSONB, nullable=True)

    # Availability flag
    # enabled=True: Model is available for new assignments
    # enabled=False: Model exists but cannot be used (soft disable)
    # Note: Disabling a model does NOT affect existing assignments or running inference
    # It only prevents NEW assignments from being created
    enabled = Column(Boolean, nullable=False, default=True, index=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # No composite indexes needed - queries are simple lookups by model_id or filter by enabled
    # Single-column index on enabled is sufficient for filtering

    def __repr__(self):
        return f"<AIModel model_id={self.model_id} name={self.name} enabled={self.enabled}>"
