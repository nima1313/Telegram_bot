"""Remove address and gender from demanders

Revision ID: 006_remove_demander_address_gender
Revises: 005
Create Date: 2025-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "006_remove_demander_address_gender"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in cols


def upgrade() -> None:
    # Drop columns if they exist to be compatible with older DBs
    if _has_column("demanders", "address"):
        op.drop_column("demanders", "address")
    if _has_column("demanders", "gender"):
        op.drop_column("demanders", "gender")


def downgrade() -> None:
    # Recreate columns if missing
    if not _has_column("demanders", "address"):
        op.add_column("demanders", sa.Column("address", sa.String(length=255), nullable=True))
    if not _has_column("demanders", "gender"):
        op.add_column("demanders", sa.Column("gender", sa.String(length=10), nullable=True))


