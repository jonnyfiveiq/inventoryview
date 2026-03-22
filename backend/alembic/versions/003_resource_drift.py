"""Resource drift tracking table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resource_drift",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resource_uid", sa.Text, nullable=False, index=True),
        sa.Column("field", sa.Text, nullable=False),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("source", sa.Text, nullable=False, server_default="collector"),
    )

    # Composite index for efficient per-resource queries ordered by time
    op.create_index(
        "ix_resource_drift_uid_changed",
        "resource_drift",
        ["resource_uid", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_resource_drift_uid_changed")
    op.drop_table("resource_drift")
