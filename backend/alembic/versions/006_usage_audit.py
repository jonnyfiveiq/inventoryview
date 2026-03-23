"""Usage analytics and login audit tables.

Revision ID: 006
Revises: 005
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- usage_event --
    op.create_table(
        "usage_event",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("feature_area", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("administrators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_usage_event_feature_area", "usage_event", ["feature_area"])
    op.create_index("ix_usage_event_created_at", "usage_event", ["created_at"])
    op.create_index(
        "ix_usage_event_feature_area_created_at",
        "usage_event",
        ["feature_area", "created_at"],
    )

    # -- login_audit --
    op.create_table(
        "login_audit",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(150), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("failure_reason", sa.String(200), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure')",
            name="ck_login_audit_outcome",
        ),
    )

    op.create_index("ix_login_audit_created_at", "login_audit", ["created_at"])
    op.create_index("ix_login_audit_username", "login_audit", ["username"])


def downgrade() -> None:
    op.drop_index("ix_login_audit_username")
    op.drop_index("ix_login_audit_created_at")
    op.drop_table("login_audit")

    op.drop_index("ix_usage_event_feature_area_created_at")
    op.drop_index("ix_usage_event_created_at")
    op.drop_index("ix_usage_event_feature_area")
    op.drop_table("usage_event")
