"""Resource request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResourceCreateRequest(BaseModel):
    """Request body for creating a new resource."""

    name: str
    vendor_id: str
    vendor: str
    vendor_type: str
    normalised_type: str
    category: str
    region: str | None = None
    state: str | None = None
    classification_confidence: float | None = Field(None, ge=0, le=1)
    classification_method: str | None = None
    raw_properties: dict | None = None


class ResourceResponse(BaseModel):
    """Public resource representation (excludes raw_properties)."""

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


class ResourceDetailResponse(BaseModel):
    """Full resource representation including raw_properties."""

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


class ResourceUpdateRequest(BaseModel):
    """Partial update request - all fields optional."""

    name: str | None = None
    vendor_id: str | None = None
    vendor: str | None = None
    vendor_type: str | None = None
    normalised_type: str | None = None
    category: str | None = None
    region: str | None = None
    state: str | None = None
    classification_confidence: float | None = Field(None, ge=0, le=1)
    classification_method: str | None = None
    raw_properties: dict | None = None
