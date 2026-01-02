"""add_ai_model_assignments_table

Revision ID: a1b2c3d4e5f6
Revises: 905390c5a2aa
Create Date: 2026-01-02 00:00:00.000000

Phase 8.1: Backend Model Assignment APIs

This migration creates the ai_model_assignments table for storing
camera-to-AI-model assignment intent.

Critical constraints:
- Purely control-plane state (intent only, not execution state)
- No triggers or side effects
- Additive and reversible
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '905390c5a2aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ai_model_assignments table (Phase 8.1).

    This table stores camera-to-model assignment intent.
    It does NOT trigger execution or affect AI runtime.
    """
    # Create table
    op.create_table(
        'ai_model_assignments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('camera_id', sa.UUID(), nullable=False),
        sa.Column('model_id', sa.String(length=128), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('desired_fps', sa.Integer(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['camera_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('camera_id', 'model_id', name='uq_camera_model')
    )

    # Create indexes
    # Query pattern: all assignments for a camera
    op.create_index('ix_ai_model_assignments_camera', 'ai_model_assignments', ['camera_id'], unique=False)

    # Query pattern: all cameras assigned to a model
    op.create_index('ix_ai_model_assignments_model', 'ai_model_assignments', ['model_id'], unique=False)

    # Query pattern: all enabled assignments
    op.create_index('ix_ai_model_assignments_enabled', 'ai_model_assignments', ['enabled'], unique=False)

    # Query pattern: enabled assignments for a camera
    op.create_index('ix_ai_model_assignments_camera_enabled', 'ai_model_assignments', ['camera_id', 'enabled'], unique=False)


def downgrade() -> None:
    """Drop ai_model_assignments table.

    This is safe to run as Phase 8.1 has no execution dependencies.
    Dropping this table only removes intent records, not runtime state.
    """
    # Drop indexes
    op.drop_index('ix_ai_model_assignments_camera_enabled', table_name='ai_model_assignments')
    op.drop_index('ix_ai_model_assignments_enabled', table_name='ai_model_assignments')
    op.drop_index('ix_ai_model_assignments_model', table_name='ai_model_assignments')
    op.drop_index('ix_ai_model_assignments_camera', table_name='ai_model_assignments')

    # Drop table
    op.drop_table('ai_model_assignments')
