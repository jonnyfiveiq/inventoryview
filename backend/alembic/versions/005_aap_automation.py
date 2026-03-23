"""AAP automation correlation tables.

Revision ID: 005
Revises: 004
Create Date: 2026-03-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- aap_host --
    op.create_table(
        "aap_host",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("host_id", sa.String(255), nullable=False),
        sa.Column("hostname", sa.String(512), nullable=False),
        sa.Column("canonical_facts", JSONB, nullable=True),
        sa.Column("smbios_uuid", sa.String(255), nullable=True),
        sa.Column("org_id", sa.String(255), nullable=False),
        sa.Column("inventory_id", sa.String(255), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_jobs", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_events", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "correlation_type",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'direct'"),
        ),
        sa.Column("correlated_resource_uid", UUID, nullable=True),
        sa.Column(
            "correlation_status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("match_score", sa.Integer, nullable=True),
        sa.Column("match_reason", sa.String(255), nullable=True),
        sa.Column("import_source", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("host_id", "org_id", name="uq_aap_host_host_org"),
        sa.CheckConstraint(
            "correlation_status IN ('auto_matched', 'manual_matched', 'pending', 'rejected')",
            name="ck_aap_host_correlation_status",
        ),
        sa.CheckConstraint(
            "correlation_type IN ('direct', 'indirect')",
            name="ck_aap_host_correlation_type",
        ),
    )

    op.create_index("ix_aap_host_smbios_uuid", "aap_host", ["smbios_uuid"])
    op.create_index("ix_aap_host_correlated_resource", "aap_host", ["correlated_resource_uid"])
    op.create_index("ix_aap_host_correlation_status", "aap_host", ["correlation_status"])
    op.create_index("ix_aap_host_hostname", "aap_host", ["hostname"])

    # -- aap_job_execution --
    op.create_table(
        "aap_job_execution",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "aap_host_id",
            UUID,
            sa.ForeignKey("aap_host.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_id", sa.String(255), nullable=False),
        sa.Column("job_name", sa.String(512), nullable=False),
        sa.Column("ok", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("changed", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("failures", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("dark", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("skipped", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("project", sa.String(512), nullable=True),
        sa.Column("org_name", sa.String(255), nullable=True),
        sa.Column("inventory_name", sa.String(255), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("aap_host_id", "job_id", name="uq_aap_job_host_job"),
    )

    op.create_index("ix_aap_job_execution_executed_at", "aap_job_execution", ["executed_at"])
    op.create_index("ix_aap_job_execution_host_id", "aap_job_execution", ["aap_host_id"])

    # -- aap_pending_match --
    op.create_table(
        "aap_pending_match",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "aap_host_id",
            UUID,
            sa.ForeignKey("aap_host.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("suggested_resource_uid", UUID, nullable=True),
        sa.Column("match_score", sa.Integer, nullable=False),
        sa.Column("match_reason", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("reviewed_by", UUID, nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("override_resource_uid", UUID, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'ignored')",
            name="ck_aap_pending_match_status",
        ),
    )

    op.create_index("ix_aap_pending_match_status", "aap_pending_match", ["status"])
    op.create_index("ix_aap_pending_match_host_id", "aap_pending_match", ["aap_host_id"])
    op.create_index("ix_aap_pending_match_score", "aap_pending_match", ["match_score"])

    # -- aap_learned_mapping --
    op.create_table(
        "aap_learned_mapping",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hostname", sa.String(512), nullable=False),
        sa.Column("resource_uid", UUID, nullable=False),
        sa.Column("org_id", sa.String(255), nullable=False),
        sa.Column("source_label", sa.String(255), nullable=False),
        sa.Column("created_by", UUID, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "hostname", "org_id", "source_label",
            name="uq_aap_learned_mapping_host_org_src",
        ),
    )

    op.create_index("ix_aap_learned_mapping_resource", "aap_learned_mapping", ["resource_uid"])


def downgrade() -> None:
    op.drop_index("ix_aap_learned_mapping_resource")
    op.drop_table("aap_learned_mapping")

    op.drop_index("ix_aap_pending_match_score")
    op.drop_index("ix_aap_pending_match_host_id")
    op.drop_index("ix_aap_pending_match_status")
    op.drop_table("aap_pending_match")

    op.drop_index("ix_aap_job_execution_host_id")
    op.drop_index("ix_aap_job_execution_executed_at")
    op.drop_table("aap_job_execution")

    op.drop_index("ix_aap_host_hostname")
    op.drop_index("ix_aap_host_correlation_status")
    op.drop_index("ix_aap_host_correlated_resource")
    op.drop_index("ix_aap_host_smbios_uuid")
    op.drop_table("aap_host")
