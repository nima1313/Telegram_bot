"""Add search history and analytics

Revision ID: 003
Revises: 002
Create Date: 2024-02-01 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # جدول search_history برای ذخیره تاریخچه جستجوها
    op.create_table('search_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demander_id', sa.Integer(), nullable=False),
        sa.Column('search_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['demander_id'], ['demanders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_search_history_demander_id'), 'search_history', ['demander_id'], unique=False)
    
    # جدول view_logs برای آمار بازدید پروفایل‌ها
    op.create_table('view_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('demander_id', sa.Integer(), nullable=True),
        sa.Column('view_type', sa.String(length=20), nullable=False),  # 'list' or 'detail'
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['demander_id'], ['demanders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_view_logs_supplier_id'), 'view_logs', ['supplier_id'], unique=False)
    
    # اضافه کردن فیلدهای آماری به suppliers
    op.add_column('suppliers', sa.Column('view_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('suppliers', sa.Column('request_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('suppliers', sa.Column('last_active', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('suppliers', 'last_active')
    op.drop_column('suppliers', 'request_count')
    op.drop_column('suppliers', 'view_count')
    
    op.drop_index(op.f('ix_view_logs_supplier_id'), table_name='view_logs')
    op.drop_table('view_logs')
    
    op.drop_index(op.f('ix_search_history_demander_id'), table_name='search_history')
    op.drop_table('search_history')
