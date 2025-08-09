"""Add demander_phone to requests table

Revision ID: 005_add_demander_phone_to_requests
Revises: 004_add_demander_fields
Create Date: 2024-03-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_demander_phone_to_requests'
down_revision = '004_add_demander_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add demander_phone column to requests table
    op.add_column('requests', sa.Column('demander_phone', sa.String(length=20), nullable=True))

def downgrade():
    # Remove demander_phone column from requests table
    op.drop_column('requests', 'demander_phone')
