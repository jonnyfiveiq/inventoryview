"""Resource business logic service."""

import logging

from psycopg_pool import AsyncConnectionPool

from inventoryview.schemas.pagination import (
    PaginatedResponse,
    PaginationInfo,
    clamp_page_size,
    encode_cursor,
)
from inventoryview.schemas.resources import ResourceCreateRequest, ResourceResponse
from inventoryview.services.graph import (
    create_resource_node,
    delete_resource_node,
    get_resource_node,
    query_resource_nodes,
    update_resource_node,
)

logger = logging.getLogger(__name__)


async def create_or_upsert(
    pool: AsyncConnectionPool,
    graph_name: str,
    data: ResourceCreateRequest,
) -> tuple[dict, bool]:
    """Create or upsert a resource node.

    The graph service MERGE handles insert-or-update semantics.
    Returns (resource_dict, is_new) where is_new is True if the node was created.
    """
    resource_data = data.model_dump(exclude_none=True)

    async with pool.connection() as conn:
        # Check if the resource already exists by vendor_id + vendor
        existing = None
        if "vendor_id" in resource_data and "vendor" in resource_data:
            # We detect is_new by checking for existence before the MERGE
            from inventoryview.services.graph import execute_cypher

            vendor_id = str(resource_data["vendor_id"]).replace("'", "\\'")
            vendor = str(resource_data["vendor"]).replace("'", "\\'")
            cypher = (
                f" MATCH (r:Resource {{vendor_id: '{vendor_id}', vendor: '{vendor}'}}) "
                f"RETURN r "
            )
            rows = await execute_cypher(conn, graph_name, cypher)
            if rows:
                existing = rows[0]

        node = await create_resource_node(conn, graph_name, resource_data)
        is_new = existing is None
        return node, is_new


async def list_resources(
    pool: AsyncConnectionPool,
    graph_name: str,
    vendor: str | None = None,
    category: str | None = None,
    region: str | None = None,
    state: str | None = None,
    cursor: str | None = None,
    page_size: int | None = None,
) -> PaginatedResponse[ResourceResponse]:
    """List resources with optional filters and cursor-based pagination."""
    page_size = clamp_page_size(page_size)

    filters: dict = {}
    if vendor is not None:
        filters["vendor"] = vendor
    if category is not None:
        filters["category"] = category
    if region is not None:
        filters["region"] = region
    if state is not None:
        filters["state"] = state

    # Decode cursor to get the uid for pagination
    cursor_uid: str | None = None
    if cursor is not None:
        from inventoryview.schemas.pagination import decode_cursor

        _, cursor_uid = decode_cursor(cursor)

    async with pool.connection() as conn:
        rows = await query_resource_nodes(
            conn, graph_name, filters, cursor_uid, page_size
        )

    # Determine if there are more pages
    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    # Build response items
    items = []
    for row in rows:
        if isinstance(row, dict):
            items.append(row)

    # Build next cursor from the last item
    next_cursor: str | None = None
    if has_more and items:
        last_uid = items[-1].get("uid", "")
        next_cursor = encode_cursor(last_uid, str(last_uid))

    pagination = PaginationInfo(
        next_cursor=next_cursor,
        has_more=has_more,
        page_size=page_size,
    )

    return PaginatedResponse(data=items, pagination=pagination)


async def get_resource(
    pool: AsyncConnectionPool,
    graph_name: str,
    uid: str,
) -> dict | None:
    """Get a single resource by uid."""
    async with pool.connection() as conn:
        return await get_resource_node(conn, graph_name, uid)


async def update_resource(
    pool: AsyncConnectionPool,
    graph_name: str,
    uid: str,
    updates: dict,
) -> dict | None:
    """Update a resource's properties."""
    async with pool.connection() as conn:
        return await update_resource_node(conn, graph_name, uid, updates)


async def delete_resource(
    pool: AsyncConnectionPool,
    graph_name: str,
    uid: str,
) -> bool:
    """Delete a resource and all its relationships."""
    async with pool.connection() as conn:
        return await delete_resource_node(conn, graph_name, uid)
