"""add_api_keys_table

Revision ID: 3b53dc2e5aab
Revises: 32ddad4b1c2a
Create Date: 2025-11-18 12:20:17.762965

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '3b53dc2e5aab'
down_revision: Union[str, None] = '32ddad4b1c2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key', sa.String(64), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Indexes are created automatically by SQLAlchemy via index=True in model
    # Only create additional indexes not covered by model definition


def downgrade() -> None:
    op.drop_table('api_keys')
