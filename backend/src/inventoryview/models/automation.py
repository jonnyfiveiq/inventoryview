"""AAP automation correlation models."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class CorrelationTier(StrEnum):
    """Tiered correlation matchers, ordered by confidence."""

    SMBIOS_SERIAL = "smbios_serial"
    BIOS_UUID = "bios_uuid"
    MAC_ADDRESS = "mac_address"
    IP_ADDRESS = "ip_address"
    FQDN = "fqdn"
    HOSTNAME_HEURISTIC = "hostname_heuristic"
    LEARNED_MAPPING = "learned_mapping"


class AAPHost(BaseModel):
    """An AAP host imported from metrics utility data."""

    id: UUID
    host_id: str
    hostname: str
    canonical_facts: dict | None = None
    ansible_facts: dict | None = None
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
    match_score: float | None = None
    match_reason: str | None = None
    import_source: str
    last_correlated_at: datetime | None = None
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
    match_score: float
    match_reason: str
    tier: str | None = None
    matched_fields: list[dict] | None = None
    ambiguity_group_id: UUID | None = None
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


class CorrelationExclusion(BaseModel):
    """A NOT_CORRELATED rule preventing a host-resource pair from being re-proposed."""

    id: int
    aap_host_id: UUID
    resource_uid: UUID
    created_by: str | None = None
    reason: str | None = None
    created_at: datetime


class CorrelationAuditEntry(BaseModel):
    """Audit log entry for a correlation action."""

    id: int
    action: str
    aap_host_id: UUID | None = None
    resource_uid: UUID | None = None
    tier: str | None = None
    confidence: float | None = None
    matched_fields: list[dict] | None = None
    previous_state: dict | None = None
    actor: str = "system"
    created_at: datetime
