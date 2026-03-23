"""Usage analytics and login audit endpoints."""

import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import unquote

from fastapi import APIRouter, Depends, Query

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.usage import (
    FeatureDetailResponse,
    LoginAuditResponse,
    UsageEventBatchRequest,
    UsageEventRequest,
    UsageEventResponse,
    UsageSummaryResponse,
)
from inventoryview.services.usage import (
    get_feature_detail,
    get_login_audit,
    get_usage_summary,
    record_event,
    record_events_batch,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_date_range(
    start_date: str | None,
    end_date: str | None,
) -> tuple[datetime, datetime]:
    """Parse start/end date strings into UTC datetimes with sensible defaults."""
    now = datetime.now(UTC)
    if end_date:
        end = datetime.fromisoformat(end_date).replace(
            hour=23, minute=59, second=59, tzinfo=UTC
        )
    else:
        end = now.replace(hour=23, minute=59, second=59)

    if start_date:
        start = datetime.fromisoformat(start_date).replace(
            hour=0, minute=0, second=0, tzinfo=UTC
        )
    else:
        start = (end - timedelta(days=7)).replace(hour=0, minute=0, second=0)

    return start, end


# -- Event ingestion --


@router.post("/events", response_model=UsageEventResponse, status_code=201)
async def create_event(body: UsageEventRequest, auth: dict = Depends(require_auth)):
    """Record a single UI usage event."""
    pool = get_pool()
    user_id = auth["sub"]
    await record_event(pool, user_id, body.feature_area, body.action)
    return UsageEventResponse(status="ok")


@router.post("/events/batch", response_model=UsageEventResponse, status_code=201)
async def create_events_batch(
    body: UsageEventBatchRequest, auth: dict = Depends(require_auth)
):
    """Record multiple UI usage events in a single request."""
    pool = get_pool()
    user_id = auth["sub"]
    events = [{"feature_area": e.feature_area, "action": e.action} for e in body.events]
    count = await record_events_batch(pool, user_id, events)
    return UsageEventResponse(status="ok", count=count)


# -- Dashboard --


@router.get("/summary", response_model=UsageSummaryResponse)
async def usage_summary(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _auth: dict = Depends(require_auth),
):
    """Get aggregate usage statistics grouped by feature area."""
    pool = get_pool()
    start, end = _parse_date_range(start_date, end_date)
    data = await get_usage_summary(pool, start, end)
    return UsageSummaryResponse(**data)


@router.get("/feature/{feature_area}", response_model=FeatureDetailResponse)
async def feature_detail(
    feature_area: str,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _auth: dict = Depends(require_auth),
):
    """Get detailed action breakdown for a specific feature area."""
    pool = get_pool()
    decoded = unquote(feature_area)
    start, end = _parse_date_range(start_date, end_date)
    data = await get_feature_detail(pool, decoded, start, end)
    return FeatureDetailResponse(**data)


@router.get("/logins", response_model=LoginAuditResponse)
async def login_audit(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _auth: dict = Depends(require_auth),
):
    """Get login audit history with pagination."""
    pool = get_pool()
    start, end = _parse_date_range(start_date, end_date)
    data = await get_login_audit(pool, start, end, page, page_size)
    return LoginAuditResponse(**data)
