"""Add address, gender, instagram_id and additional_notes to demanders

Revision ID: 004
Revises: 003
Create Date: 2025-01-08 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add new columns to demanders table
    op.add_column('demanders', sa.Column('address', sa.String(length=255), nullable=True))
    op.add_column('demanders', sa.Column('gender', sa.String(length=10), nullable=True))
    op.add_column('demanders', sa.Column('instagram_id', sa.String(length=100), nullable=True))
    op.add_column('demanders', sa.Column('additional_notes', sa.Text(), nullable=True))

def downgrade() -> None:
    # Remove the added columns
    op.drop_column('demanders', 'additional_notes')
    op.drop_column('demanders', 'instagram_id')
    op.drop_column('demanders', 'gender')
    op.drop_column('demanders', 'address')