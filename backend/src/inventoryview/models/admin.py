"""Administrator model."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Admin(BaseModel):
    """Administrator account for InventoryView."""

    id: UUID = Field(default_factory=uuid4)
    username: str = "admin"
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    setup_complete: bool = False
