"""Usage analytics and login audit request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# -- Event ingestion --

class UsageEventRequest(BaseModel):
    """Single usage event submission."""

    feature_area: str = Field(max_length=100)
    action: str = Field(max_length=100)


class UsageEventBatchRequest(BaseModel):
    """Batch usage event submission."""

    events: list[UsageEventRequest] = Field(max_items=50)


class UsageEventResponse(BaseModel):
    """Response after recording usage event(s)."""

    status: str = "ok"
    count: int | None = None


# -- Dashboard summary --

class Period(BaseModel):
    """Time period for usage queries."""

    start: datetime
    end: datetime


class FeatureAreaSummary(BaseModel):
    """Aggregate stats for a single feature area."""

    feature_area: str
    total_events: int
    unique_users: int
    trend: str  # "up", "down", "flat"
    trend_percentage: float


class UsageSummaryResponse(BaseModel):
    """Top-level usage dashboard response."""

    period: Period
    feature_areas: list[FeatureAreaSummary]
    total_events: int
    total_unique_users: int


# -- Feature detail --

class ActionBreakdown(BaseModel):
    """Stats for a single action within a feature area."""

    action: str
    count: int
    unique_users: int


class FeatureDetailResponse(BaseModel):
    """Detailed action breakdown for a feature area."""

    feature_area: str
    period: Period
    actions: list[ActionBreakdown]
    total_events: int


# -- Login audit --

class LoginAuditEntry(BaseModel):
    """Single login audit log entry."""

    id: UUID
    username: str
    outcome: str
    failure_reason: str | None = None
    ip_address: str
    created_at: datetime


class LoginSummary(BaseModel):
    """Summary counts for login activity."""

    total_attempts: int
    successful: int
    failed: int
    unique_users: int


class LoginAuditResponse(BaseModel):
    """Paginated login audit response."""

    period: Period
    summary: LoginSummary
    entries: list[LoginAuditEntry]
    page: int
    page_size: int
    total_count: int
