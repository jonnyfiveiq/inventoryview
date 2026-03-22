"""Relationship business logic."""

import logging
from datetime import UTC, datetime

from psycopg_pool import AsyncConnectionPool

from inventoryview.schemas.pagination import (
    PaginatedResponse,
    PaginationInfo,
    clamp_page_size,
    decode_cursor,
    encode_cursor,
)
from inventoryview.services.graph import execute_cypher, parse_agtype

logger = logging.getLogger(__name__)


async def create_relationship(
    pool: AsyncConnectionPool,
    graph_name: str,
    source_uid: str,
    target_uid: str,
    edge_type: str,
    confidence: float = 1.0,
    source_collector: str | None = None,
    inference_method: str | None = None,
    metadata: dict | None = None,
) -> dict | None:
    """Create a directed edge between two resource nodes.

    Returns the relationship dict or None if source/target not found.
    """
    now = datetime.now(UTC).isoformat()

    async with pool.connection() as conn:
        # Verify both resources exist
        for uid in (source_uid, target_uid):
            rows = await execute_cypher(
                conn,
                graph_name,
                f"MATCH (n:Resource {{uid: '{uid}'}}) RETURN n",
            )
            if not rows:
                return None

        # Create the edge
        props = {
            "confidence": confidence,
            "established_at": now,
            "last_confirmed": now,
        }
        if source_collector:
            props["source_collector"] = source_collector
        if inference_method:
            props["inference_method"] = inference_method

        props_str = ", ".join(f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" for k, v in props.items())

        cypher = (
            f"MATCH (a:Resource {{uid: '{source_uid}'}}), (b:Resource {{uid: '{target_uid}'}}) "
            f"CREATE (a)-[r:{edge_type} {{{props_str}}}]->(b) "
            f"RETURN r"
        )
        rows = await execute_cypher(conn, graph_name, cypher)

    return {
        "source_uid": source_uid,
        "target_uid": target_uid,
        "type": edge_type,
        "confidence": confidence,
        "source_collector": source_collector,
        "established_at": now,
        "last_confirmed": now,
        "inference_method": inference_method,
        "metadata": metadata,
    }


async def delete_relationship(
    pool: AsyncConnectionPool,
    graph_name: str,
    source_uid: str,
    target_uid: str,
    edge_type: str,
) -> bool:
    """Delete a relationship by source, target, and type."""
    async with pool.connection() as conn:
        cypher = (
            f"MATCH (a:Resource {{uid: '{source_uid}'}})"
            f"-[r:{edge_type}]->"
            f"(b:Resource {{uid: '{target_uid}'}}) "
            f"DELETE r RETURN true"
        )
        rows = await execute_cypher(conn, graph_name, cypher)
        return len(rows) > 0


async def list_for_resource(
    pool: AsyncConnectionPool,
    graph_name: str,
    uid: str,
    direction: str = "both",
    edge_type: str | None = None,
    cursor: str | None = None,
    page_size: int = 50,
) -> PaginatedResponse:
    """List relationships for a resource with pagination."""
    page_size = clamp_page_size(page_size)

    if direction == "out":
        pattern = f"(a:Resource {{uid: '{uid}'}})-[r]->(b:Resource)"
    elif direction == "in":
        pattern = f"(a:Resource)<-[r]-(b:Resource {{uid: '{uid}'}})"
    else:
        pattern = f"(a:Resource {{uid: '{uid}'}})-[r]-(b:Resource)"

    type_filter = f"WHERE type(r) = '{edge_type}'" if edge_type else ""

    cypher = f"MATCH {pattern} {type_filter} RETURN a, r, b"

    async with pool.connection() as conn:
        rows = await execute_cypher(
            conn, graph_name, cypher, columns="(a agtype, r agtype, b agtype)"
        )

    results = []
    for row in rows:
        a_props = parse_agtype(row.get("a", "")) if isinstance(row.get("a"), str) else row.get("a", {})
        r_props = parse_agtype(row.get("r", "")) if isinstance(row.get("r"), str) else row.get("r", {})
        b_props = parse_agtype(row.get("b", "")) if isinstance(row.get("b"), str) else row.get("b", {})

        a_data = a_props.get("properties", a_props) if isinstance(a_props, dict) else {}
        r_data = r_props.get("properties", r_props) if isinstance(r_props, dict) else {}
        b_data = b_props.get("properties", b_props) if isinstance(b_props, dict) else {}

        results.append({
            "source_uid": a_data.get("uid", ""),
            "target_uid": b_data.get("uid", ""),
            "type": r_props.get("label", "") if isinstance(r_props, dict) else "",
            "confidence": r_data.get("confidence", 1.0),
            "source_collector": r_data.get("source_collector"),
            "established_at": r_data.get("established_at", ""),
            "last_confirmed": r_data.get("last_confirmed", ""),
            "inference_method": r_data.get("inference_method"),
        })

    # Simple pagination (slice based)
    has_more = len(results) > page_size
    results = results[:page_size]

    next_cursor = None
    if has_more and results:
        last = results[-1]
        next_cursor = encode_cursor(last["established_at"], last["source_uid"])

    return PaginatedResponse(
        data=results,
        pagination=PaginationInfo(
            next_cursor=next_cursor,
            has_more=has_more,
            page_size=page_size,
        ),
    )
