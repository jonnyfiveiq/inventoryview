"""Playlist tables for resource collections.

Revision ID: 004
Revises: 003
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- playlist --
    op.create_table(
        "playlist",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("slug", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_playlist_name", "playlist", ["name"])

    # -- playlist_membership --
    op.create_table(
        "playlist_membership",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("playlist_id", UUID, sa.ForeignKey("playlist.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_uid", sa.Text, nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("playlist_id", "resource_uid", name="uq_playlist_membership_pid_ruid"),
    )

    op.create_index("ix_playlist_membership_resource_uid", "playlist_membership", ["resource_uid"])
    op.create_index("ix_playlist_membership_playlist_id", "playlist_membership", ["playlist_id"])

    # -- playlist_activity --
    op.create_table(
        "playlist_activity",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("playlist_id", UUID, sa.ForeignKey("playlist.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("resource_uid", sa.Text, nullable=True),
        sa.Column("resource_name", sa.Text, nullable=True),
        sa.Column("resource_vendor", sa.Text, nullable=True),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "action IN ('playlist_created', 'playlist_renamed', 'playlist_deleted', "
            "'resource_added', 'resource_removed', 'resource_deleted_from_system')",
            name="ck_playlist_activity_action",
        ),
    )

    op.create_index(
        "ix_playlist_activity_pid_occurred",
        "playlist_activity",
        ["playlist_id", "occurred_at"],
    )
    op.create_index("ix_playlist_activity_occurred_at", "playlist_activity", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_playlist_activity_occurred_at")
    op.drop_index("ix_playlist_activity_pid_occurred")
    op.drop_table("playlist_activity")

    op.drop_index("ix_playlist_membership_playlist_id")
    op.drop_index("ix_playlist_membership_resource_uid")
    op.drop_table("playlist_membership")

    op.drop_index("ix_playlist_name")
    op.drop_table("playlist")
