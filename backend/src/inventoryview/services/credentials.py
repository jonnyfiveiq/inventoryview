"""Credential service - business logic for credential CRUD operations."""

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from inventoryview.models.credential import CredentialType
from inventoryview.schemas.credentials import CredentialResponse, CredentialTestResponse
from inventoryview.schemas.pagination import (
    PaginatedResponse,
    PaginationInfo,
    clamp_page_size,
    decode_cursor,
    encode_cursor,
)
from inventoryview.services.vault import (
    decrypt_secret,
    encrypt_secret,
    vault_key_holder,
)

logger = logging.getLogger(__name__)


async def _write_audit_log(
    conn,
    credential_id: UUID | None,
    operation: str,
    actor: str,
    details: dict | None = None,
) -> None:
    """Write an entry to the credential audit log."""
    await conn.execute(
        """
        INSERT INTO credential_audit_log (credential_id, operation, actor, details)
        VALUES (%s, %s, %s, %s)
        """,
        [str(credential_id) if credential_id else None, operation, actor, json.dumps(details) if details else None],
    )


async def create_credential(
    pool,
    name: str,
    credential_type: CredentialType,
    secret_dict: dict,
    metadata: dict,
    actor: str,
) -> CredentialResponse:
    """Create a new credential, encrypting the secret with the vault key."""
    key = vault_key_holder.get_key()
    plaintext = json.dumps(secret_dict).encode("utf-8")
    ciphertext, nonce, auth_tag = encrypt_secret(plaintext, key)

    async with pool.connection() as conn:
        result = await conn.execute(
            """
            INSERT INTO credentials (name, credential_type, encrypted_secret, nonce, auth_tag, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, credential_type, metadata, associated_collector,
                      created_at, updated_at, last_used_at
            """,
            [name, str(credential_type), ciphertext, nonce, auth_tag, json.dumps(metadata)],
        )
        row = await result.fetchone()
        await _write_audit_log(conn, row["id"], "create", actor, {"name": name, "type": str(credential_type)})

    return CredentialResponse(**row)


async def list_credentials(
    pool,
    cursor: str | None = None,
    page_size: int | None = None,
    credential_type_filter: CredentialType | None = None,
) -> PaginatedResponse[CredentialResponse]:
    """List credentials with cursor-based pagination. Returns metadata only."""
    page_size = clamp_page_size(page_size)
    # Fetch one extra to check if there are more results
    limit = page_size + 1

    async with pool.connection() as conn:
        if cursor is not None:
            sort_val, cursor_id = decode_cursor(cursor)
            if credential_type_filter is not None:
                result = await conn.execute(
                    """
                    SELECT id, name, credential_type, metadata, associated_collector,
                           created_at, updated_at, last_used_at
                    FROM credentials
                    WHERE credential_type = %s
                      AND (created_at, id) < (%s, %s::uuid)
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    [str(credential_type_filter), sort_val, cursor_id, limit],
                )
            else:
                result = await conn.execute(
                    """
                    SELECT id, name, credential_type, metadata, associated_collector,
                           created_at, updated_at, last_used_at
                    FROM credentials
                    WHERE (created_at, id) < (%s, %s::uuid)
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    [sort_val, cursor_id, limit],
                )
        else:
            if credential_type_filter is not None:
                result = await conn.execute(
                    """
                    SELECT id, name, credential_type, metadata, associated_collector,
                           created_at, updated_at, last_used_at
                    FROM credentials
                    WHERE credential_type = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    [str(credential_type_filter), limit],
                )
            else:
                result = await conn.execute(
                    """
                    SELECT id, name, credential_type, metadata, associated_collector,
                           created_at, updated_at, last_used_at
                    FROM credentials
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    [limit],
                )

        rows = await result.fetchall()

    has_more = len(rows) > page_size
    rows = rows[:page_size]

    items = [CredentialResponse(**row) for row in rows]

    next_cursor = None
    if has_more and rows:
        last = rows[-1]
        next_cursor = encode_cursor(str(last["created_at"]), str(last["id"]))

    return PaginatedResponse[CredentialResponse](
        data=items,
        pagination=PaginationInfo(
            next_cursor=next_cursor,
            has_more=has_more,
            page_size=page_size,
        ),
    )


async def get_credential(
    pool,
    credential_id: UUID,
    actor: str,
) -> CredentialResponse | None:
    """Get a single credential by ID. Returns metadata only. Writes audit log."""
    async with pool.connection() as conn:
        result = await conn.execute(
            """
            SELECT id, name, credential_type, metadata, associated_collector,
                   created_at, updated_at, last_used_at
            FROM credentials
            WHERE id = %s
            """,
            [str(credential_id)],
        )
        row = await result.fetchone()
        if row is None:
            return None

        await _write_audit_log(conn, credential_id, "read", actor)

    return CredentialResponse(**row)


async def update_credential(
    pool,
    credential_id: UUID,
    updates_dict: dict,
    actor: str,
) -> CredentialResponse | None:
    """Update credential metadata and/or re-encrypt the secret."""
    set_clauses = []
    params: list = []

    if "name" in updates_dict and updates_dict["name"] is not None:
        set_clauses.append("name = %s")
        params.append(updates_dict["name"])

    if "credential_type" in updates_dict and updates_dict["credential_type"] is not None:
        set_clauses.append("credential_type = %s")
        params.append(str(updates_dict["credential_type"]))

    if "metadata" in updates_dict and updates_dict["metadata"] is not None:
        set_clauses.append("metadata = %s")
        params.append(json.dumps(updates_dict["metadata"]))

    if "associated_collector" in updates_dict:
        set_clauses.append("associated_collector = %s")
        params.append(updates_dict["associated_collector"])

    if "secret" in updates_dict and updates_dict["secret"] is not None:
        key = vault_key_holder.get_key()
        plaintext = json.dumps(updates_dict["secret"]).encode("utf-8")
        ciphertext, nonce, auth_tag = encrypt_secret(plaintext, key)
        set_clauses.append("encrypted_secret = %s")
        params.append(ciphertext)
        set_clauses.append("nonce = %s")
        params.append(nonce)
        set_clauses.append("auth_tag = %s")
        params.append(auth_tag)

    if not set_clauses:
        # Nothing to update; just return existing credential
        return await get_credential(pool, credential_id, actor)

    set_clauses.append("updated_at = now()")
    params.append(str(credential_id))

    set_sql = ", ".join(set_clauses)
    query = f"""
        UPDATE credentials
        SET {set_sql}
        WHERE id = %s
        RETURNING id, name, credential_type, metadata, associated_collector,
                  created_at, updated_at, last_used_at
    """

    async with pool.connection() as conn:
        result = await conn.execute(query, params)
        row = await result.fetchone()
        if row is None:
            return None

        await _write_audit_log(
            conn,
            credential_id,
            "update",
            actor,
            {"updated_fields": [k for k in updates_dict if updates_dict[k] is not None]},
        )

    return CredentialResponse(**row)


async def delete_credential(
    pool,
    credential_id: UUID,
    actor: str,
) -> bool:
    """Delete a credential. Returns True if deleted, False if not found."""
    async with pool.connection() as conn:
        # Write audit log before deleting (FK is SET NULL on delete)
        await _write_audit_log(conn, credential_id, "delete", actor)

        result = await conn.execute(
            "DELETE FROM credentials WHERE id = %s",
            [str(credential_id)],
        )
        return result.rowcount > 0


async def test_credential(
    pool,
    credential_id: UUID,
    actor: str,
) -> CredentialTestResponse | None:
    """Test a credential by decrypting its secret.

    Actual connection testing is collector-dependent; for MVP this returns
    success if decryption succeeds.
    """
    async with pool.connection() as conn:
        result = await conn.execute(
            """
            SELECT id, encrypted_secret, nonce, auth_tag
            FROM credentials
            WHERE id = %s
            """,
            [str(credential_id)],
        )
        row = await result.fetchone()
        if row is None:
            return None

        key = vault_key_holder.get_key()
        now = datetime.now(timezone.utc)

        try:
            decrypt_secret(
                bytes(row["encrypted_secret"]),
                bytes(row["nonce"]),
                bytes(row["auth_tag"]),
                key,
            )
            status = "success"
            message = "Credential decrypted successfully"
        except Exception as exc:
            logger.warning("Credential test failed for %s: %s", credential_id, exc)
            status = "failure"
            message = f"Decryption failed: {exc}"

        await _write_audit_log(conn, credential_id, "use", actor, {"test_status": status})

        # Update last_used_at
        await conn.execute(
            "UPDATE credentials SET last_used_at = %s WHERE id = %s",
            [now, str(credential_id)],
        )

    return CredentialTestResponse(
        credential_id=credential_id,
        status=status,
        message=message,
        tested_at=now,
    )
