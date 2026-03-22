"""Credential vault endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.credentials import (
    CredentialCreateRequest,
    CredentialResponse,
    CredentialTestResponse,
    CredentialUpdateRequest,
)
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.schemas.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from inventoryview.services.credentials import (
    create_credential,
    delete_credential,
    get_credential,
    list_credentials,
    test_credential,
    update_credential,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", status_code=201, response_model=CredentialResponse)
async def create(body: CredentialCreateRequest, payload: dict = Depends(require_auth)):
    """Store a new credential in the encrypted vault."""
    pool = get_pool()
    actor = payload.get("sub", "unknown")

    result = await create_credential(
        pool=pool,
        name=body.name,
        credential_type=body.credential_type,
        secret_dict=body.secret,
        metadata=body.metadata or {},
        actor=actor,
    )
    return result


@router.get("")
async def list_all(
    credential_type: str | None = Query(None),
    cursor: str | None = Query(None),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    payload: dict = Depends(require_auth),
):
    """List credentials (metadata only, never secrets)."""
    pool = get_pool()
    return await list_credentials(pool, cursor, page_size, credential_type)


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_one(credential_id: UUID, payload: dict = Depends(require_auth)):
    """Get a single credential by ID (metadata only)."""
    pool = get_pool()
    actor = payload.get("sub", "unknown")
    result = await get_credential(pool, str(credential_id), actor)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Credential {credential_id} not found"),
        )
    return result


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update(credential_id: UUID, body: CredentialUpdateRequest, payload: dict = Depends(require_auth)):
    """Update a credential's metadata and/or secret."""
    pool = get_pool()
    actor = payload.get("sub", "unknown")
    updates = body.model_dump(exclude_unset=True)
    result = await update_credential(pool, str(credential_id), updates, actor)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Credential {credential_id} not found"),
        )
    return result


@router.delete("/{credential_id}", status_code=204)
async def delete(credential_id: UUID, payload: dict = Depends(require_auth)):
    """Permanently delete a credential."""
    pool = get_pool()
    actor = payload.get("sub", "unknown")
    deleted = await delete_credential(pool, str(credential_id), actor)
    if not deleted:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Credential {credential_id} not found"),
        )


@router.post("/{credential_id}/test", response_model=CredentialTestResponse)
async def test(credential_id: UUID, payload: dict = Depends(require_auth)):
    """Test a stored credential's connectivity."""
    pool = get_pool()
    actor = payload.get("sub", "unknown")
    result = await test_credential(pool, str(credential_id), actor)
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, f"Credential {credential_id} not found"),
        )
    return result
