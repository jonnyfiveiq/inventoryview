"""AAP automation correlation models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AAPHost(BaseModel):
    """An AAP host imported from metrics utility data."""

    id: UUID
    host_id: str
    hostname: str
    canonical_facts: dict | None = None
    smbios_uuid: str | None = None
    org_id: str
    inventory_id: str
    first_seen: datetime
    last_seen: datetime
    total_jobs: int = 0
    total_events: int = 0
    correlation_type: str = "direct"
    correlated_resource_uid: UUID | None = None
    correlation_status: str = "pending"
    match_score: int | None = None
    match_reason: str | None = None
    import_source: str
    created_at: datetime
    updated_at: datetime


class AAPJobExecution(BaseModel):
    """A single job execution record against an AAP host."""

    id: UUID
    aap_host_id: UUID
    job_id: str
    job_name: str
    ok: int = 0
    changed: int = 0
    failures: int = 0
    dark: int = 0
    skipped: int = 0
    project: str | None = None
    org_name: str | None = None
    inventory_name: str | None = None
    executed_at: datetime
    created_at: datetime


class AAPPendingMatch(BaseModel):
    """A pending correlation awaiting admin review."""

    id: UUID
    aap_host_id: UUID
    suggested_resource_uid: UUID | None = None
    match_score: int
    match_reason: str
    status: str = "pending"
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    override_resource_uid: UUID | None = None
    created_at: datetime


class AAPLearnedMapping(BaseModel):
    """A confirmed hostname-to-resource mapping that persists across imports."""

    id: UUID
    hostname: str
    resource_uid: UUID
    org_id: str
    source_label: str
    created_by: UUID | None = None
    created_at: datetime
