"""Resource model for inventory graph nodes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Resource(BaseModel):
    """A cloud/infrastructure resource stored as a graph node."""

    uid: UUID
    name: str
    vendor_id: str
    vendor: str
    vendor_type: str
    normalised_type: str
    category: str
    region: str | None = None
    state: str | None = None
    classification_confidence: float | None = None
    classification_method: str | None = None
    first_seen: datetime
    last_seen: datetime
    raw_properties: dict | None = None
