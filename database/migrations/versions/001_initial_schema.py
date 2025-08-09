"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ایجاد enum types
    op.execute("CREATE TYPE userrole AS ENUM ('supplier', 'demander')")
    op.execute("CREATE TYPE requeststatus AS ENUM ('pending', 'accepted', 'rejected')")
    op.execute("CREATE TYPE gendertype AS ENUM ('مرد', 'زن')")
    op.execute("CREATE TYPE cooperationtype AS ENUM ('in_person', 'project_based', 'part_time')")
    op.execute("CREATE TYPE workstyletype AS ENUM ('fashion', 'advertising', 'religious', 'children', 'sports', 'artistic', 'outdoor', 'studio')")
    op.execute("CREATE TYPE priceunit AS ENUM ('hourly', 'daily', 'project')")
    
    # جدول users
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('role', sa.Enum('supplier', 'demander', name='userrole'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    
    # جدول suppliers
    op.create_table('suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('gender', sa.Enum('مرد', 'زن', name='gendertype'), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('area', sa.String(length=100), nullable=True),
        sa.Column('instagram_id', sa.String(length=100), nullable=True),
        sa.Column('portfolio_link', sa.String(length=500), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('weight', sa.Integer(), nullable=True),
        sa.Column('hair_color', sa.String(length=50), nullable=True),
        sa.Column('eye_color', sa.String(length=50), nullable=True),
        sa.Column('skin_color', sa.String(length=50), nullable=True),
        sa.Column('top_size', sa.String(length=20), nullable=True),
        sa.Column('bottom_size', sa.String(length=20), nullable=True),
        sa.Column('special_features', sa.Text(), nullable=True),
        sa.Column('price_range_min', sa.Integer(), nullable=False),
        sa.Column('price_range_max', sa.Integer(), nullable=False),
        sa.Column('price_unit', sa.Enum('hourly', 'daily', 'project', name='priceunit'), nullable=False),
        sa.Column('cooperation_types', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('work_styles', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('brand_experience', sa.Text(), nullable=True),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suppliers_city'), 'suppliers', ['city'], unique=False)
    op.create_index(op.f('ix_suppliers_user_id'), 'suppliers', ['user_id'], unique=True)
    
    # جدول demanders
    op.create_table('demanders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=False),
        sa.Column('company_name', sa.String(length=200), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_demanders_user_id'), 'demanders', ['user_id'], unique=True)
    
    # جدول requests
    op.create_table('requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demander_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'rejected', name='requeststatus'), server_default='pending', nullable=False),
        sa.Column('response_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['demander_id'], ['demanders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requests_demander_id'), 'requests', ['demander_id'], unique=False)
    op.create_index(op.f('ix_requests_status'), 'requests', ['status'], unique=False)
    op.create_index(op.f('ix_requests_supplier_id'), 'requests', ['supplier_id'], unique=False)

def downgrade() -> None:
    # حذف جداول
    op.drop_index(op.f('ix_requests_supplier_id'), table_name='requests')
    op.drop_index(op.f('ix_requests_status'), table_name='requests')
    op.drop_index(op.f('ix_requests_demander_id'), table_name='requests')
    op.drop_table('requests')
    
    op.drop_index(op.f('ix_demanders_user_id'), table_name='demanders')
    op.drop_table('demanders')
    
    op.drop_index(op.f('ix_suppliers_user_id'), table_name='suppliers')
    op.drop_index(op.f('ix_suppliers_city'), table_name='suppliers')
    op.drop_table('suppliers')
    
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_table('users')
    
    # حذف enum types
    op.execute("DROP TYPE IF EXISTS priceunit")
    op.execute("DROP TYPE IF EXISTS workstyletype")
    op.execute("DROP TYPE IF EXISTS cooperationtype")
    op.execute("DROP TYPE IF EXISTS gendertype")
    op.execute("DROP TYPE IF EXISTS requeststatus")
    op.execute("DROP TYPE IF EXISTS userrole")
