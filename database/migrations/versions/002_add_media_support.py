"""Add media support for suppliers

Revision ID: 002
Revises: 001
Create Date: 2024-01-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # جدول media برای ذخیره تصاویر و ویدیوهای پورتفولیو
    op.create_table('media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.String(length=200), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('order_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_supplier_id'), 'media', ['supplier_id'], unique=False)
    
    # اضافه کردن فیلد تعداد media به suppliers
    op.add_column('suppliers', sa.Column('media_count', sa.Integer(), server_default='0', nullable=False))

def downgrade() -> None:
    op.drop_column('suppliers', 'media_count')
    op.drop_index(op.f('ix_media_supplier_id'), table_name='media')
    op.drop_table('media')
