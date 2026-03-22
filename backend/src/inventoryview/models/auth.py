"""JWT token and revoked token models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RevokedToken(BaseModel):
    """A revoked JWT token stored in the database."""

    jti: UUID
    revoked_at: datetime
    expires_at: datetime
