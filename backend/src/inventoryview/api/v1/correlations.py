"""Asset correlation endpoints."""

import logging

from fastapi import APIRouter, Depends, Request

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/scan")
async def scan_correlations(
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Scan all resources and create SAME_ASSET links where hardware IDs match."""
    from inventoryview.services.asset_correlation import correlate_assets

    pool = get_pool()
    settings = request.app.state.settings
    created = await correlate_assets(pool, settings.graph_name)
    return {
        "created": len(created),
        "correlations": created,
    }
