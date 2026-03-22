"""Credentials and credential audit log tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credentials",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("credential_type", sa.Text, nullable=False),
        sa.Column("encrypted_secret", BYTEA, nullable=False),
        sa.Column("nonce", BYTEA, nullable=False),
        sa.Column("auth_tag", BYTEA, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("associated_collector", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "credential_type IN ("
            "'aws_key_pair', 'azure_service_principal', 'gcp_service_account', "
            "'vsphere', 'openshift_kubernetes', 'bearer_token', "
            "'username_password', 'ssh_key'"
            ")",
            name="credentials_type_check",
        ),
    )

    op.create_table(
        "credential_audit_log",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "credential_id",
            UUID,
            sa.ForeignKey("credentials.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("operation", sa.Text, nullable=False),
        sa.Column("actor", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("details", JSONB, nullable=True),
        sa.CheckConstraint(
            "operation IN ('create', 'read', 'update', 'delete', 'use')",
            name="audit_operation_check",
        ),
    )


def downgrade() -> None:
    op.drop_table("credential_audit_log")
    op.drop_table("credentials")
