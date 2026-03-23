"""Fleet-wide drift endpoints."""

import logging

from fastapi import APIRouter, Depends, Query, Request

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/fleet-timeline")
async def fleet_timeline(
    request: Request,
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payload: dict = Depends(require_auth),
):
    """Get aggregated daily drift timeline across all resources."""
    from inventoryview.services.drift import get_fleet_drift_timeline

    pool = get_pool()
    return await get_fleet_drift_timeline(pool, start=start, end=end)
