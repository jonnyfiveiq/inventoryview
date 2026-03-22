"""Credential request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from inventoryview.models.credential import CredentialType


class CredentialCreateRequest(BaseModel):
    """Request body for creating a credential."""

    name: str
    credential_type: CredentialType
    secret: dict
    metadata: dict = Field(default_factory=dict)


class CredentialResponse(BaseModel):
    """Credential response - NEVER includes the secret."""

    id: UUID
    name: str
    credential_type: CredentialType
    metadata: dict
    associated_collector: str | None = None
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None


class CredentialUpdateRequest(BaseModel):
    """Request body for updating a credential."""

    name: str | None = None
    credential_type: CredentialType | None = None
    secret: dict | None = None
    metadata: dict | None = None
    associated_collector: str | None = None


class CredentialTestResponse(BaseModel):
    """Response from testing a credential."""

    credential_id: UUID
    status: str  # "success" or "failure"
    message: str
    tested_at: datetime
