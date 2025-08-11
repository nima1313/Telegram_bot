"""Change supplier top_size and bottom_size to Integer

Revision ID: 007_change_size_to_integer
Revises: 006_remove_demander_address_gender
Create Date: 2025-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_change_size_to_integer"
down_revision: Union[str, None] = "006_remove_demander_address_gender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert existing string values to integers when possible and alter type
    # Use PostgreSQL USING clause to safely cast after stripping non-digits
    op.alter_column(
        "suppliers",
        "top_size",
        type_=sa.Integer(),
        existing_type=sa.String(length=20),
        postgresql_using="NULLIF(regexp_replace(top_size, '\\D+', '', 'g'), '')::integer",
        existing_nullable=True,
    )
    op.alter_column(
        "suppliers",
        "bottom_size",
        type_=sa.Integer(),
        existing_type=sa.String(length=20),
        postgresql_using="NULLIF(regexp_replace(bottom_size, '\\D+', '', 'g'), '')::integer",
        existing_nullable=True,
    )


def downgrade() -> None:
    # Revert columns back to string representations
    op.alter_column(
        "suppliers",
        "top_size",
        type_=sa.String(length=20),
        existing_type=sa.Integer(),
        postgresql_using="top_size::text",
        existing_nullable=True,
    )
    op.alter_column(
        "suppliers",
        "bottom_size",
        type_=sa.String(length=20),
        existing_type=sa.Integer(),
        postgresql_using="bottom_size::text",
        existing_nullable=True,
    )


