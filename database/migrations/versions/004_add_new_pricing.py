"""Add new pricing structure

Revision ID: 004_add_new_pricing
Revises: 003
Create Date: 2025-08-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_new_pricing'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Remove old pricing columns
    op.drop_column('suppliers', 'price_range_min')
    op.drop_column('suppliers', 'price_range_max')
    op.drop_column('suppliers', 'price_unit')
    
    # Add new pricing column
    op.add_column('suppliers', sa.Column('pricing_data', sa.JSON))


def downgrade():
    # Remove new pricing column
    op.drop_column('suppliers', 'pricing_data')
    # Note: old columns are not restored in this downgrade to avoid data loss complexity
