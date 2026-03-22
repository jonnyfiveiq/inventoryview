"""Auth and setup request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SetupStatusResponse(BaseModel):
    """Response indicating whether initial setup has been completed."""

    setup_complete: bool


class SetupInitRequest(BaseModel):
    """Request to initialise the admin account during first-time setup."""

    password: str = Field(min_length=12)


class SetupInitResponse(BaseModel):
    """Response after successful setup initialisation."""

    message: str
    username: str


class LoginRequest(BaseModel):
    """Credentials for admin login."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Response containing an authentication token."""

    token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenRevokeRequest(BaseModel):
    """Request to revoke an existing token."""

    token: str
