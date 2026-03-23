"""Playlist request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlaylistCreateRequest(BaseModel):
    """Request body for creating a new playlist."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class PlaylistUpdateRequest(BaseModel):
    """Partial update request - all fields optional."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class PlaylistResponse(BaseModel):
    """Public playlist representation."""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime


class PlaylistMembershipResponse(BaseModel):
    """Playlist membership representation."""

    playlist_id: UUID
    resource_uid: str
    added_at: datetime


class PlaylistActivityResponse(BaseModel):
    """Single playlist activity entry."""

    id: UUID
    action: str
    resource_uid: str | None = None
    resource_name: str | None = None
    resource_vendor: str | None = None
    detail: str | None = None
    occurred_at: datetime


class PlaylistActivityTimelineDay(BaseModel):
    """Aggregated activity counts for a single day."""

    date: str
    count: int
    actions: list[str] = []


class AddMemberRequest(BaseModel):
    """Request body for adding a resource to a playlist."""

    resource_uid: str
