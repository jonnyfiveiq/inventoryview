"""Resource endpoints - CRUD, filtering, pagination, graph queries."""

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.schemas.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from inventoryview.schemas.resources import (
    ResourceCreateRequest,
    ResourceDetailResponse,
    ResourceUpdateRequest,
)
from inventoryview.services.resources import (
    create_or_upsert,
    delete_resource,
    get_resource,
    list_resources,
    update_resource,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("")
async def create(body: ResourceCreateRequest, request: Request, payload: dict = Depends(require_auth)):
    """Create or upsert a resource."""
    pool = get_pool()
    settings = request.app.state.settings
    result, is_new = await create_or_upsert(pool, settings.graph_name, body)
    status_code = 201 if is_new else 200
    return JSONResponse(status_code=status_code, content=result)


@router.get("")
async def list_all(
    request: Request,
    vendor: str | None = Query(None),
    category: str | None = Query(None),
    region: str | None = Query(None),
    state: str | None = Query(None),
    cursor: str | None = Query(None),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    search: str | None = Query(None, min_length=2),
    payload: dict = Depends(require_auth),
):
    """List resources with filtering, search, and cursor-based pagination."""
    pool = get_pool()
    settings = request.app.state.settings
    return await list_resources(
        pool, settings.graph_name, vendor, category, region, state, cursor, page_size,
        search=search,
    )


@router.get("/{uid}")
async def get_one(uid: str, request: Request, payload: dict = Depends(require_auth)):
    """Get a single resource with full detail."""
    pool = get_pool()
    settings = request.app.state.settings
    result = await get_resource(pool, settings.graph_name, uid)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Resource {uid} not found"),
        )
    return result


@router.patch("/{uid}")
async def update(uid: str, body: ResourceUpdateRequest, request: Request, payload: dict = Depends(require_auth)):
    """Partial update a resource."""
    pool = get_pool()
    settings = request.app.state.settings
    updates = body.model_dump(exclude_unset=True)
    result = await update_resource(pool, settings.graph_name, uid, updates)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Resource {uid} not found"),
        )
    return result


@router.delete("/{uid}", status_code=204)
async def delete(uid: str, request: Request, payload: dict = Depends(require_auth)):
    """Delete a resource and all its relationships."""
    pool = get_pool()
    settings = request.app.state.settings
    deleted = await delete_resource(pool, settings.graph_name, uid)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Resource {uid} not found"),
        )


@router.get("/{uid}/relationships")
async def get_relationships(
    uid: str,
    request: Request,
    direction: str = Query("both", pattern="^(in|out|both)$"),
    type: str | None = Query(None),
    cursor: str | None = Query(None),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    payload: dict = Depends(require_auth),
):
    """List relationships for a resource."""
    from inventoryview.services.relationships import list_for_resource

    pool = get_pool()
    settings = request.app.state.settings
    return await list_for_resource(pool, settings.graph_name, uid, direction, type, cursor, page_size)


@router.get("/{uid}/drift")
async def get_drift(uid: str, request: Request, payload: dict = Depends(require_auth)):
    """Get drift history for a resource."""
    from inventoryview.services.drift import get_drift_history

    pool = get_pool()
    return {"data": await get_drift_history(pool, uid)}


@router.post("/{uid}/drift")
async def create_drift(uid: str, request: Request, payload: dict = Depends(require_auth)):
    """Record a drift entry for a resource (used by collectors and seed scripts)."""
    from datetime import datetime, UTC
    from inventoryview.services.drift import record_drift

    pool = get_pool()
    body = await request.json()
    field = body.get("field")
    if not field:
        return JSONResponse(
            status_code=400,
            content=error_response(ErrorCode.VALIDATION_ERROR, "field is required"),
        )

    changed_at_str = body.get("changed_at")
    changed_at = datetime.fromisoformat(changed_at_str) if changed_at_str else None

    await record_drift(
        pool,
        resource_uid=uid,
        field=field,
        old_value=body.get("old_value"),
        new_value=body.get("new_value"),
        changed_at=changed_at,
        source=body.get("source", "collector"),
    )
    return JSONResponse(status_code=201, content={"status": "recorded"})


@router.get("/{uid}/drift/timeline")
async def get_drift_timeline(
    uid: str,
    request: Request,
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payload: dict = Depends(require_auth),
):
    """Get aggregated daily drift timeline for a resource."""
    from inventoryview.services.drift import get_drift_timeline
    from inventoryview.services.resources import get_resource

    pool = get_pool()
    settings = request.app.state.settings
    timeline = await get_drift_timeline(pool, uid, start=start, end=end)

    # Get first_seen from the resource
    resource = await get_resource(pool, settings.graph_name, uid)
    first_seen = resource["first_seen"] if resource else None

    return {
        "data": timeline["data"],
        "total_drift_count": timeline["total_drift_count"],
        "first_seen": first_seen,
    }


@router.get("/{uid}/drift/exists")
async def drift_exists(uid: str, request: Request, payload: dict = Depends(require_auth)):
    """Check if a resource has drift history."""
    from inventoryview.services.drift import has_drift

    pool = get_pool()
    return {"has_drift": await has_drift(pool, uid)}


@router.get("/{uid}/asset-twins")
async def get_asset_twins_endpoint(
    uid: str,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Get resources that represent the same underlying asset (matched by hardware IDs)."""
    from inventoryview.services.asset_correlation import get_asset_twins

    pool = get_pool()
    settings = request.app.state.settings
    twins = await get_asset_twins(pool, settings.graph_name, uid)
    return {"data": twins}


@router.get("/{uid}/asset-chain")
async def get_asset_chain_endpoint(
    uid: str,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Get the full transitive chain of SAME_ASSET-linked resources."""
    from inventoryview.services.asset_correlation import get_asset_chain

    pool = get_pool()
    settings = request.app.state.settings
    return await get_asset_chain(pool, settings.graph_name, uid)


@router.get("/{uid}/playlists")
async def get_resource_playlists(
    uid: str,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Get all playlists that contain this resource."""
    from inventoryview.services.playlists import get_playlists_for_resource

    pool = get_pool()
    playlists = await get_playlists_for_resource(pool, uid)
    return {"data": playlists}


@router.get("/{uid}/graph")
async def get_graph(
    uid: str,
    request: Request,
    depth: int = Query(1, ge=1),
    payload: dict = Depends(require_auth),
):
    """Get the subgraph around a resource at a specified depth."""
    from inventoryview.services.graph import get_subgraph

    pool = get_pool()
    settings = request.app.state.settings

    # Respect max traversal depth from system settings
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT value FROM system_settings WHERE key = 'max_traversal_depth'"
        )
        row = await result.fetchone()
        max_depth = int(row["value"]) if row else settings.max_traversal_depth

    if depth > max_depth:
        return JSONResponse(
            status_code=400,
            content=error_response(
                ErrorCode.VALIDATION_ERROR,
                f"Requested depth {depth} exceeds maximum allowed depth {max_depth}",
            ),
        )

    return await get_subgraph(pool, settings.graph_name, uid, depth)


@router.get("/{uid}/correlation")
async def get_resource_correlation(
    uid: str,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Get correlation detail (temperature gauge data) for a resource."""
    from inventoryview.services.graph import execute_cypher

    pool = get_pool()
    settings = request.app.state.settings

    def _band(confidence: float) -> str:
        if confidence >= 0.90:
            return "hot"
        if confidence >= 0.70:
            return "warm"
        if confidence >= 0.40:
            return "tepid"
        return "cold"

    async with pool.connection() as conn:
        cypher = (
            f" MATCH (a:AAPHost)-[rel:AUTOMATED_BY]->(r:Resource {{uid: '{uid}'}}) "
            f"RETURN a.host_id AS host_id, a.hostname AS hostname, "
            f"rel.confidence AS conf, rel.tier AS tier, "
            f"rel.matched_fields AS mf, rel.status AS st, "
            f"rel.confirmed_by AS cb, rel.created_at AS cat, rel.updated_at AS uat"
        )
        rows = await execute_cypher(
            conn, settings.graph_name, cypher,
            columns="(host_id agtype, hostname agtype, conf agtype, tier agtype, mf agtype, st agtype, cb agtype, cat agtype, uat agtype)",
        )

    if not rows or not isinstance(rows[0], dict):
        return {"resource_uid": uid, "is_correlated": False, "correlation": None}

    row = rows[0]
    conf = float(row.get("conf", 0))
    import json as _json
    mf_raw = row.get("mf")
    matched_fields = []
    if mf_raw:
        try:
            matched_fields = _json.loads(str(mf_raw)) if isinstance(mf_raw, str) else mf_raw
        except Exception:
            pass

    return {
        "resource_uid": uid,
        "is_correlated": True,
        "correlation": {
            "aap_host_id": str(row.get("host_id", "")),
            "aap_hostname": str(row.get("hostname", "")),
            "confidence": conf,
            "tier": str(row.get("tier", "")),
            "matched_fields": matched_fields,
            "status": str(row.get("st", "proposed")),
            "temperature": _band(conf),
            "confirmed_by": str(row.get("cb", "")) if row.get("cb") else None,
            "created_at": str(row.get("cat", "")) if row.get("cat") else None,
            "updated_at": str(row.get("uat", "")) if row.get("uat") else None,
        },
    }
