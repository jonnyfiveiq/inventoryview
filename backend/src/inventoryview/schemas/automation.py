"""AAP automation request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Upload ---

class UploadCorrelationSummary(BaseModel):
    auto_matched: int = 0
    pending_review: int = 0
    unmatched: int = 0


class UploadResponse(BaseModel):
    import_id: str
    source_label: str
    hosts_imported: int = 0
    hosts_updated: int = 0
    jobs_imported: int = 0
    events_counted: int = 0
    indirect_nodes_imported: int = 0
    correlation_summary: UploadCorrelationSummary | None = None
    correlation_job_id: str | None = None
    message: str | None = None


class CorrelationJobResponse(BaseModel):
    job_id: str
    status: str
    progress: int = 0
    total: int = 0
    matched: int = 0
    queued_for_review: int = 0
    errors: list[str] = []
    started_at: str | None = None
    completed_at: str | None = None


# --- AAP Host list ---

class CorrelatedResourceBrief(BaseModel):
    uid: UUID
    name: str
    vendor: str
    normalised_type: str


class AAPHostItem(BaseModel):
    id: UUID
    host_id: str
    hostname: str
    smbios_uuid: str | None = None
    org_id: str
    inventory_id: str
    first_seen: datetime
    last_seen: datetime
    total_jobs: int
    total_events: int
    correlation_type: str
    correlation_status: str
    match_score: int | None = None
    match_reason: str | None = None
    correlated_resource: CorrelatedResourceBrief | None = None


class AAPHostListResponse(BaseModel):
    items: list[AAPHostItem]
    next_cursor: str | None = None
    total_count: int


# --- Pending Match ---

class PendingMatchHostBrief(BaseModel):
    id: UUID
    host_id: str
    hostname: str
    smbios_uuid: str | None = None
    total_jobs: int


class PendingMatchResourceBrief(BaseModel):
    uid: UUID
    name: str
    vendor: str
    normalised_type: str


class MatchedFieldDetail(BaseModel):
    ansible_field: str
    resource_field: str
    values: list[str]


class PendingMatchItem(BaseModel):
    id: UUID
    aap_host: PendingMatchHostBrief
    suggested_resource: PendingMatchResourceBrief | None = None
    match_score: float
    match_reason: str
    tier: str | None = None
    matched_fields: list[MatchedFieldDetail] | None = None
    ambiguity_group_id: UUID | None = None
    status: str
    created_at: datetime


class PendingMatchListResponse(BaseModel):
    items: list[PendingMatchItem]
    next_cursor: str | None = None
    total_count: int


# --- Review ---

class ReviewAction(BaseModel):
    pending_match_id: UUID
    action: str = Field(pattern=r"^(approve|reject|ignore|dismiss|confirm)$")
    override_resource_uid: UUID | None = None
    reason: str | None = None


class ReviewRequest(BaseModel):
    actions: list[ReviewAction]


class ReviewResultItem(BaseModel):
    pending_match_id: UUID
    action: str
    success: bool
    learned_mapping_created: bool = False
    error: str | None = None


class ReviewResponse(BaseModel):
    processed: int
    results: list[ReviewResultItem]


# --- Coverage ---

class ProviderCoverage(BaseModel):
    vendor: str
    total: int
    automated: int
    coverage_percentage: float


class TopAutomatedResource(BaseModel):
    resource_uid: UUID
    resource_name: str
    vendor: str
    total_jobs: int
    last_automated: datetime


class RecentImport(BaseModel):
    source_label: str
    imported_at: datetime
    hosts_count: int


class CoverageResponse(BaseModel):
    total_resources: int
    automated_resources: int
    coverage_percentage: float
    by_provider: list[ProviderCoverage]
    top_automated: list[TopAutomatedResource]
    recent_imports: list[RecentImport]


# --- History ---

class AAPHostBrief(BaseModel):
    hostname: str
    correlation_type: str
    match_reason: str | None = None


class JobExecutionItem(BaseModel):
    job_id: str
    job_name: str
    ok: int
    changed: int
    failures: int
    dark: int
    skipped: int
    project: str | None = None
    org_name: str | None = None
    correlation_type: str
    executed_at: datetime


class HistoryExecutions(BaseModel):
    items: list[JobExecutionItem]
    next_cursor: str | None = None
    total_count: int


class HistoryResponse(BaseModel):
    resource_uid: UUID
    first_automated: datetime | None = None
    last_automated: datetime | None = None
    total_jobs: int = 0
    aap_hosts: list[AAPHostBrief]
    executions: HistoryExecutions


# --- Reports ---

class AutomatedResourceReport(BaseModel):
    resource_uid: UUID
    resource_name: str
    vendor: str
    normalised_type: str
    first_automated: datetime
    last_automated: datetime
    total_jobs: int
    aap_hostnames: list[str]


class UnautomatedResourceReport(BaseModel):
    resource_uid: UUID
    resource_name: str
    vendor: str
    normalised_type: str


class ReportSummary(BaseModel):
    total_resources: int
    automated_resources: int
    coverage_percentage: float
    deduplicated_note: str = ""


class ReportResponse(BaseModel):
    generated_at: datetime
    summary: ReportSummary
    automated: list[AutomatedResourceReport]
    unautomated: list[UnautomatedResourceReport]


# --- Graph ---

class AutomationGraphNode(BaseModel):
    id: str
    label: str
    type: str
    vendor: str | None = None
    normalised_type: str | None = None
    correlation_type: str | None = None
    total_jobs: int | None = None


class AutomationGraphEdge(BaseModel):
    source: str
    target: str
    type: str = "AUTOMATED_BY"
    confidence: float | None = None
    correlation_type: str | None = None
    inference_method: str | None = None


class AutomationGraphResponse(BaseModel):
    nodes: list[AutomationGraphNode]
    edges: list[AutomationGraphEdge]


# --- Correlation Temperature ---


class ResourceCorrelationDetail(BaseModel):
    aap_host_id: UUID | str
    aap_hostname: str
    confidence: float
    tier: str
    matched_fields: list[MatchedFieldDetail] = []
    status: str
    temperature: str
    confirmed_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResourceCorrelationResponse(BaseModel):
    resource_uid: str
    is_correlated: bool
    correlation: ResourceCorrelationDetail | None = None


class ConfidenceBucket(BaseModel):
    label: str
    count: int
    description: str


class FleetTemperatureResponse(BaseModel):
    total_correlated: int
    total_aap_hosts: int
    total_resources: int
    uncorrelated: int
    weighted_average_confidence: float
    temperature: str
    tier_distribution: dict[str, int]
    band_distribution: dict[str, int]
    confidence_buckets: list[ConfidenceBucket]


# --- Re-correlate ---


class ReCorrelateRequest(BaseModel):
    resource_uid: str


class ReCorrelateResponse(BaseModel):
    correlation_job_id: str
    message: str
