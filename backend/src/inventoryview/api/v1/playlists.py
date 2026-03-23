"""Playlist endpoints — CRUD, membership, activity."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.schemas.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from inventoryview.schemas.playlists import (
    AddMemberRequest,
    PlaylistCreateRequest,
    PlaylistUpdateRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _ensure_serializable(obj):
    """Recursively convert non-JSON-serializable types (UUID, datetime, bytes)."""
    if isinstance(obj, dict):
        return {k: _ensure_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_ensure_serializable(v) for v in obj]
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    return obj


@router.get("")
async def list_playlists(
    request: Request,
    cursor: str | None = Query(None),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    payload: dict = Depends(require_auth),
):
    """List all playlists with member counts."""
    from inventoryview.services.playlists import list_playlists as svc_list

    pool = get_pool()
    return await svc_list(pool, cursor=cursor, page_size=page_size)


@router.post("")
async def create_playlist(
    body: PlaylistCreateRequest,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Create a new playlist."""
    from inventoryview.services.playlists import create_playlist as svc_create

    pool = get_pool()
    result = await svc_create(pool, name=body.name, description=body.description)
    return JSONResponse(status_code=201, content=_ensure_serializable(result))


@router.get("/{identifier}")
async def get_playlist(
    identifier: str,
    request: Request,
    detail: str = Query("summary", pattern="^(summary|full)$"),
    payload: dict = Depends(require_auth),
):
    """Get a playlist by slug or UUID with member resources."""
    from inventoryview.services.playlists import get_playlist as svc_get

    pool = get_pool()
    settings = request.app.state.settings
    result = await svc_get(pool, identifier, graph_name=settings.graph_name, detail=detail)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Playlist '{identifier}' not found"),
        )
    return result


@router.patch("/{identifier}")
async def update_playlist(
    identifier: str,
    body: PlaylistUpdateRequest,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Update a playlist's name and/or description."""
    from inventoryview.services.playlists import update_playlist as svc_update

    pool = get_pool()
    updates = body.model_dump(exclude_unset=True)
    result = await svc_update(pool, identifier, updates)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Playlist '{identifier}' not found"),
        )
    return result


@router.delete("/{identifier}", status_code=204)
async def delete_playlist(
    identifier: str,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Delete a playlist."""
    from inventoryview.services.playlists import delete_playlist as svc_delete

    pool = get_pool()
    deleted = await svc_delete(pool, identifier)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Playlist '{identifier}' not found"),
        )


@router.post("/{identifier}/members")
async def add_member(
    identifier: str,
    body: AddMemberRequest,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Add a resource to a playlist."""
    from inventoryview.services.playlists import add_resource as svc_add

    pool = get_pool()
    settings = request.app.state.settings
    result = await svc_add(pool, identifier, body.resource_uid, graph_name=settings.graph_name)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Playlist '{identifier}' not found"),
        )
    if result == "duplicate":
        return JSONResponse(
            status_code=409,
            content=error_response(ErrorCode.VALIDATION_ERROR, "Resource already in playlist"),
        )
    return JSONResponse(status_code=201, content=_ensure_serializable(result))


@router.delete("/{identifier}/members/{resource_uid}", status_code=204)
async def remove_member(
    identifier: str,
    resource_uid: str,
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Remove a resource from a playlist."""
    from inventoryview.services.playlists import remove_resource as svc_remove

    pool = get_pool()
    settings = request.app.state.settings
    removed = await svc_remove(pool, identifier, resource_uid, graph_name=settings.graph_name)
    if not removed:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, "Playlist or membership not found"),
        )


@router.get("/{identifier}/activity")
async def get_activity(
    identifier: str,
    request: Request,
    date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    cursor: str | None = Query(None),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    payload: dict = Depends(require_auth),
):
    """Get activity log for a playlist."""
    from inventoryview.services.playlists import get_activity as svc_activity

    pool = get_pool()
    result = await svc_activity(pool, identifier, filter_date=date, cursor=cursor, page_size=page_size)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Playlist '{identifier}' not found"),
        )
    return result


@router.get("/{identifier}/activity/timeline")
async def get_activity_timeline(
    identifier: str,
    request: Request,
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payload: dict = Depends(require_auth),
):
    """Get aggregated daily activity timeline for a playlist."""
    from inventoryview.services.playlists import get_activity_timeline as svc_timeline

    pool = get_pool()
    result = await svc_timeline(pool, identifier, start=start, end=end)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Playlist '{identifier}' not found"),
        )
    return result
