"""Enhanced AAP correlation engine — schema changes.

Adds ansible_facts and last_correlated_at to aap_host; adds tier,
matched_fields, ambiguity_group_id to aap_pending_match; creates
correlation_exclusion and correlation_audit tables; migrates match_score
from integer (0-100) to float (0.0-1.0); expands CHECK constraints for
new correlation tiers and statuses.

Revision ID: 007
Revises: 006
Create Date: 2026-03-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- aap_host: new columns ---
    op.add_column(
        "aap_host",
        sa.Column("ansible_facts", JSONB, nullable=True),
    )
    op.add_column(
        "aap_host",
        sa.Column(
            "last_correlated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # --- aap_host: migrate match_score from integer to float ---
    op.alter_column(
        "aap_host",
        "match_score",
        type_=sa.Float,
        existing_type=sa.Integer,
        existing_nullable=True,
        postgresql_using="match_score::double precision",
    )
    op.execute(
        "UPDATE aap_host SET match_score = match_score / 100.0 "
        "WHERE match_score IS NOT NULL AND match_score > 1.0"
    )

    # --- aap_host: expand correlation_type CHECK to include new tiers ---
    op.drop_constraint("ck_aap_host_correlation_type", "aap_host", type_="check")
    op.create_check_constraint(
        "ck_aap_host_correlation_type",
        "aap_host",
        "correlation_type IN ("
        "'direct', 'indirect', "
        "'smbios_serial', 'bios_uuid', 'mac_address', "
        "'ip_address', 'fqdn', 'hostname_heuristic', 'learned_mapping'"
        ")",
    )

    # --- aap_host: expand correlation_status CHECK ---
    op.drop_constraint("ck_aap_host_correlation_status", "aap_host", type_="check")
    op.create_check_constraint(
        "ck_aap_host_correlation_status",
        "aap_host",
        "correlation_status IN ("
        "'auto_matched', 'manual_matched', 'pending', 'rejected', 'confirmed'"
        ")",
    )

    # --- aap_pending_match: new columns ---
    op.add_column(
        "aap_pending_match",
        sa.Column("tier", sa.String(40), nullable=True),
    )
    op.add_column(
        "aap_pending_match",
        sa.Column("matched_fields", JSONB, nullable=True),
    )
    op.add_column(
        "aap_pending_match",
        sa.Column("ambiguity_group_id", UUID, nullable=True),
    )

    # --- aap_pending_match: migrate match_score from integer to float ---
    op.alter_column(
        "aap_pending_match",
        "match_score",
        type_=sa.Float,
        existing_type=sa.Integer,
        existing_nullable=False,
        postgresql_using="match_score::double precision",
    )
    op.execute(
        "UPDATE aap_pending_match SET match_score = match_score / 100.0 "
        "WHERE match_score > 1.0"
    )

    # --- aap_pending_match: expand status CHECK to include 'dismissed' ---
    op.drop_constraint("ck_aap_pending_match_status", "aap_pending_match", type_="check")
    op.create_check_constraint(
        "ck_aap_pending_match_status",
        "aap_pending_match",
        "status IN ('pending', 'approved', 'rejected', 'ignored', 'dismissed', 'confirmed')",
    )

    op.create_index(
        "ix_aap_pending_match_ambiguity_group",
        "aap_pending_match",
        ["ambiguity_group_id"],
    )

    # --- correlation_exclusion (new table) ---
    op.create_table(
        "correlation_exclusion",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "aap_host_id",
            UUID,
            sa.ForeignKey("aap_host.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resource_uid", UUID, nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "aap_host_id",
            "resource_uid",
            name="uq_correlation_exclusion_host_resource",
        ),
    )

    # --- correlation_audit (new table) ---
    op.create_table(
        "correlation_audit",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "action",
            sa.String(30),
            nullable=False,
        ),
        sa.Column(
            "aap_host_id",
            UUID,
            sa.ForeignKey("aap_host.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resource_uid", UUID, nullable=True),
        sa.Column("tier", sa.String(40), nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("matched_fields", JSONB, nullable=True),
        sa.Column("previous_state", JSONB, nullable=True),
        sa.Column("actor", sa.String(255), nullable=False, server_default=sa.text("'system'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_correlation_audit_host", "correlation_audit", ["aap_host_id"])
    op.create_index("ix_correlation_audit_action", "correlation_audit", ["action"])
    op.create_index("ix_correlation_audit_created", "correlation_audit", ["created_at"])


def downgrade() -> None:
    # --- drop new tables ---
    op.drop_index("ix_correlation_audit_created")
    op.drop_index("ix_correlation_audit_action")
    op.drop_index("ix_correlation_audit_host")
    op.drop_table("correlation_audit")

    op.drop_table("correlation_exclusion")

    # --- aap_pending_match: revert ---
    op.drop_index("ix_aap_pending_match_ambiguity_group")
    op.drop_column("aap_pending_match", "ambiguity_group_id")
    op.drop_column("aap_pending_match", "matched_fields")
    op.drop_column("aap_pending_match", "tier")

    op.drop_constraint("ck_aap_pending_match_status", "aap_pending_match", type_="check")
    op.create_check_constraint(
        "ck_aap_pending_match_status",
        "aap_pending_match",
        "status IN ('pending', 'approved', 'rejected', 'ignored')",
    )

    op.execute(
        "UPDATE aap_pending_match SET match_score = (match_score * 100)::integer "
        "WHERE match_score <= 1.0"
    )
    op.alter_column(
        "aap_pending_match",
        "match_score",
        type_=sa.Integer,
        existing_type=sa.Float,
        existing_nullable=False,
        postgresql_using="match_score::integer",
    )

    # --- aap_host: revert ---
    op.drop_constraint("ck_aap_host_correlation_status", "aap_host", type_="check")
    op.create_check_constraint(
        "ck_aap_host_correlation_status",
        "aap_host",
        "correlation_status IN ('auto_matched', 'manual_matched', 'pending', 'rejected')",
    )

    op.drop_constraint("ck_aap_host_correlation_type", "aap_host", type_="check")
    op.create_check_constraint(
        "ck_aap_host_correlation_type",
        "aap_host",
        "correlation_type IN ('direct', 'indirect')",
    )

    op.execute(
        "UPDATE aap_host SET match_score = (match_score * 100)::integer "
        "WHERE match_score IS NOT NULL AND match_score <= 1.0"
    )
    op.alter_column(
        "aap_host",
        "match_score",
        type_=sa.Integer,
        existing_type=sa.Float,
        existing_nullable=True,
        postgresql_using="match_score::integer",
    )

    op.drop_column("aap_host", "last_correlated_at")
    op.drop_column("aap_host", "ansible_facts")
