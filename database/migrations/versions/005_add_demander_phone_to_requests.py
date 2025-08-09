"""Add demander_phone to requests table

Revision ID: 005
Revises: 004_add_new_pricing
Create Date: 2024-03-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004_add_new_pricing'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Add demander_phone column to requests table
    op.add_column('requests', sa.Column('demander_phone', sa.String(length=20), nullable=True))

def downgrade():
    # Remove demander_phone column from requests table
    op.drop_column('requests', 'demander_phone')
