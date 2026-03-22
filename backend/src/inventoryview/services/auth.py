"""JWT authentication service."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def create_token(
    subject: str,
    secret: str,
    expiry_hours: int = 24,
) -> tuple[str, datetime]:
    """Create a JWT token. Returns (token_string, expires_at)."""
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=expiry_hours)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expires_at,
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token, expires_at


def decode_token(token: str, secret: str) -> dict:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, secret, algorithms=[ALGORITHM])


async def check_revoked(pool: AsyncConnectionPool, jti: str) -> bool:
    """Check if a token JTI is in the revocation blocklist."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT 1 FROM revoked_tokens WHERE jti = %s",
            [jti],
        )
        row = await result.fetchone()
        return row is not None


async def revoke_token(pool: AsyncConnectionPool, jti: str, expires_at: datetime) -> None:
    """Add a token JTI to the revocation blocklist."""
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO revoked_tokens (jti, expires_at) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            [jti, expires_at],
        )
    logger.info("Token revoked: jti=%s", jti)
