"""Initial schema - admin, vault, settings, revoked tokens.

Revision ID: 001
Revises: None
Create Date: 2026-03-21

Note: AGE extension creation and graph setup are handled by the DB init
entrypoint and the application lifespan, not by migrations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Administrators table
    op.create_table(
        "administrators",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.Text, nullable=False, unique=True, server_default="admin"),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("setup_complete", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    # Vault configuration (singleton)
    op.create_table(
        "vault_config",
        sa.Column("id", sa.Integer, primary_key=True, server_default="1"),
        sa.Column("salt", BYTEA, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="vault_config_singleton"),
    )

    # System settings (key-value store)
    op.create_table(
        "system_settings",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", JSONB, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Insert default max_traversal_depth
    op.execute("""
        INSERT INTO system_settings (key, value) VALUES ('max_traversal_depth', '5')
        ON CONFLICT (key) DO NOTHING
    """)

    # Revoked tokens
    op.create_table(
        "revoked_tokens",
        sa.Column("jti", UUID, primary_key=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("revoked_tokens")
    op.drop_table("system_settings")
    op.drop_table("vault_config")
    op.drop_table("administrators")
