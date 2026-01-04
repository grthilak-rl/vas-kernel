"""add_ai_models_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-04 00:00:00.000000

Phase 5.4: AI Model Registry & Discovery APIs

This migration creates the ai_models table for storing persistent AI model
metadata. This table serves as the canonical source of truth for which AI
models exist in the system and their capabilities.

Critical constraints:
- Stores declarative metadata only (NOT runtime state)
- Environment-scoped (global, not per-camera)
- Independent of container lifecycle and inference execution
- No triggers or side effects
- Additive and reversible
- Fail-closed validation (unknown model_id = invalid assignment)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ai_models table (Phase 5.4).

    This table stores AI model registry metadata.
    It does NOT interact with containers, inference, or runtime state.
    It is the authoritative source for model existence validation.
    """
    # Create table
    op.create_table(
        'ai_models',
        sa.Column('model_id', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('supported_tasks', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('config_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('model_id')
    )

    # Create index for filtering by enabled status
    # Query pattern: list all enabled models, or list all disabled models
    op.create_index('ix_ai_models_enabled', 'ai_models', ['enabled'], unique=False)


def downgrade() -> None:
    """Drop ai_models table.

    This is safe to run as Phase 5.4 has no execution dependencies.
    Dropping this table only removes metadata, not runtime state.

    WARNING: Existing ai_model_assignments may reference model_ids that will
    become orphaned if this table is dropped. This is intentional (fail-closed).
    """
    # Drop index
    op.drop_index('ix_ai_models_enabled', table_name='ai_models')

    # Drop table
    op.drop_table('ai_models')
