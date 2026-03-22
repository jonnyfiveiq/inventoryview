"""Relationship endpoints - create and delete edges."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.schemas.relationships import (
    RelationshipCreateRequest,
    RelationshipDeleteRequest,
    RelationshipResponse,
)
from inventoryview.services.relationships import create_relationship, delete_relationship

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", status_code=201, response_model=RelationshipResponse)
async def create(body: RelationshipCreateRequest, request: Request, payload: dict = Depends(require_auth)):
    """Create a directed relationship between two resources."""
    pool = get_pool()
    settings = request.app.state.settings
    result = await create_relationship(
        pool=pool,
        graph_name=settings.graph_name,
        source_uid=body.source_uid,
        target_uid=body.target_uid,
        edge_type=body.type,
        confidence=body.confidence,
        source_collector=body.source_collector,
        inference_method=body.inference_method,
        metadata=body.metadata,
    )
    if result is None:
        return JSONResponse(
            status_code=404,
            content=error_response(
                ErrorCode.NOT_FOUND,
                "Source or target resource not found",
            ),
        )
    return result


@router.delete("", status_code=204)
async def delete(body: RelationshipDeleteRequest, request: Request, payload: dict = Depends(require_auth)):
    """Delete a relationship by source, target, and type."""
    pool = get_pool()
    settings = request.app.state.settings
    deleted = await delete_relationship(
        pool=pool,
        graph_name=settings.graph_name,
        source_uid=body.source_uid,
        target_uid=body.target_uid,
        edge_type=body.type,
    )
    if not deleted:
        return JSONResponse(
            status_code=404,
            content=error_response(ErrorCode.NOT_FOUND, "Relationship not found"),
        )
