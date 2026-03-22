"""Vault service - AES-256-GCM encryption with Argon2id key derivation."""

import logging
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# AES-GCM tag length in bytes
_TAG_LEN = 16


class VaultKeyHolder:
    """Holds the derived vault key in memory only."""

    def __init__(self) -> None:
        self._key: bytes | None = None

    def set_key(self, key: bytes) -> None:
        """Store the derived key."""
        self._key = key

    def get_key(self) -> bytes:
        """Return the derived key. Raises if not set."""
        if self._key is None:
            raise RuntimeError("Vault key not initialized")
        return self._key

    def clear_key(self) -> None:
        """Remove the key from memory."""
        self._key = None


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using Argon2id."""
    return hash_secret_raw(
        secret=passphrase.encode("utf-8"),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID,
    )


def encrypt_secret(plaintext: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
    """Encrypt plaintext with AES-256-GCM.

    Returns:
        (ciphertext, nonce, auth_tag)
    """
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    # AESGCM.encrypt returns ciphertext || tag (last 16 bytes are the tag)
    ct_with_tag = aesgcm.encrypt(nonce, plaintext, None)
    ciphertext = ct_with_tag[:-_TAG_LEN]
    auth_tag = ct_with_tag[-_TAG_LEN:]
    return ciphertext, nonce, auth_tag


def decrypt_secret(ciphertext: bytes, nonce: bytes, auth_tag: bytes, key: bytes) -> bytes:
    """Decrypt ciphertext with AES-256-GCM."""
    aesgcm = AESGCM(key)
    # Reconstruct the ciphertext+tag blob that AESGCM.decrypt expects
    ct_with_tag = ciphertext + auth_tag
    return aesgcm.decrypt(nonce, ct_with_tag, None)


# Module-level singleton
vault_key_holder = VaultKeyHolder()


async def init_vault(passphrase: str, pool) -> None:
    """Read or create the vault salt and derive the encryption key.

    Args:
        passphrase: The vault passphrase.
        pool: An asyncpg-compatible connection pool (psycopg AsyncConnectionPool).
    """
    async with pool.connection() as conn:
        result = await conn.execute("SELECT salt FROM vault_config WHERE id = 1")
        row = await result.fetchone()

        if row is not None:
            salt = bytes(row["salt"])
            logger.info("Loaded existing vault salt")
        else:
            salt = os.urandom(16)
            await conn.execute(
                "INSERT INTO vault_config (id, salt) VALUES (1, %s)",
                [salt],
            )
            logger.info("Created new vault salt")

    key = derive_key(passphrase, salt)
    vault_key_holder.set_key(key)
    logger.info("Vault key derived and stored in memory")
