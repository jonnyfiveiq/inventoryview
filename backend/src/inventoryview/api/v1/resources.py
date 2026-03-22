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
    payload: dict = Depends(require_auth),
):
    """List resources with filtering and cursor-based pagination."""
    pool = get_pool()
    settings = request.app.state.settings
    return await list_resources(
        pool, settings.graph_name, vendor, category, region, state, cursor, page_size
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


@router.get("/{uid}/drift/exists")
async def drift_exists(uid: str, request: Request, payload: dict = Depends(require_auth)):
    """Check if a resource has drift history."""
    from inventoryview.services.drift import has_drift

    pool = get_pool()
    return {"has_drift": await has_drift(pool, uid)}


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
