"""Core Apache AGE / Cypher helpers for graph operations."""

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)


def parse_agtype(value: str) -> Any:
    """Parse an AGE agtype string into a Python object.

    Handles ::vertex, ::edge suffixes and scalar types.
    Strips the type suffix and JSON-loads the remainder.
    """
    if value is None:
        return None

    text = str(value).strip()

    # Handle ::vertex - extract properties dict with id and label
    if text.endswith("::vertex"):
        text = text[: -len("::vertex")].strip()
        parsed = json.loads(text)
        return {
            "id": parsed.get("id"),
            "label": parsed.get("label"),
            **parsed.get("properties", {}),
        }

    # Handle ::edge - extract properties with relationship metadata
    if text.endswith("::edge"):
        text = text[: -len("::edge")].strip()
        parsed = json.loads(text)
        return {
            "id": parsed.get("id"),
            "label": parsed.get("label"),
            "start_id": parsed.get("start_id"),
            "end_id": parsed.get("end_id"),
            **parsed.get("properties", {}),
        }

    # Strip any other ::type suffix (e.g. ::numeric, ::text)
    type_match = re.match(r"^(.+?)::(\w+)$", text)
    if type_match:
        text = type_match.group(1).strip()

    # Try JSON parse for objects/arrays/strings, fall back to raw string
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text


async def execute_cypher(
    conn: AsyncConnection,
    graph_name: str,
    cypher_query: str,
    params: dict | None = None,
    columns: str = "(v agtype)",
) -> list[dict]:
    """Execute a Cypher query via the AGE SQL wrapper.

    Wraps: SELECT * FROM ag_catalog.cypher(graph_name, $$ cypher $$) AS columns
    When params are provided they are serialized as JSON agtype.
    """
    if params is not None:
        params_json = json.dumps(params)
        sql = (
            f"SELECT * FROM ag_catalog.cypher('{graph_name}', "
            f"$cypher${cypher_query}$cypher$, "
            f"'{params_json}'::agtype) AS {columns}"
        )
    else:
        sql = (
            f"SELECT * FROM ag_catalog.cypher('{graph_name}', "
            f"$cypher${cypher_query}$cypher$) AS {columns}"
        )

    result = await conn.execute(sql)
    rows = await result.fetchall()

    def _to_str(v: Any) -> str:
        """Decode bytes/memoryview from AGE before parsing."""
        if isinstance(v, memoryview):
            v = bytes(v)
        if isinstance(v, bytes):
            return v.decode("utf-8")
        return str(v)

    parsed_rows = []
    for row in rows:
        if isinstance(row, dict):
            parsed = {k: parse_agtype(_to_str(v)) for k, v in row.items()}
            # Auto-unwrap single-column results (e.g. "(v agtype)")
            if len(parsed) == 1:
                parsed_rows.append(next(iter(parsed.values())))
            else:
                parsed_rows.append(parsed)
        elif isinstance(row, (tuple, list)):
            if len(row) == 1:
                parsed_rows.append(parse_agtype(_to_str(row[0])))
            else:
                parsed_rows.append([parse_agtype(_to_str(v)) for v in row])

    return parsed_rows


async def create_resource_node(
    conn: AsyncConnection,
    graph_name: str,
    resource_data: dict,
) -> dict:
    """Create or update a Resource node keyed on (vendor_id, vendor).

    AGE does not support MERGE … ON CREATE SET / ON MATCH SET, so we use
    a two-step MATCH-then-CREATE approach instead.
    """
    now = datetime.now(UTC).isoformat()
    vendor_id = str(resource_data["vendor_id"]).replace("'", "\\'")
    vendor = str(resource_data["vendor"]).replace("'", "\\'")

    # Step 1: check if node already exists
    match_cypher = (
        f" MATCH (r:Resource {{vendor_id: '{vendor_id}', vendor: '{vendor}'}}) "
        f"RETURN r "
    )
    existing = await execute_cypher(conn, graph_name, match_cypher)

    # Build property SET assignments
    def _escape(val):
        if isinstance(val, dict):
            return "'" + json.dumps(val).replace("'", "\\'") + "'"
        if isinstance(val, (int, float)):
            return str(val)
        return "'" + str(val).replace("'", "\\'") + "'"

    if existing:
        # Step 2a: update existing node
        sets = [f"r.last_seen = '{now}'"]
        for key, val in resource_data.items():
            if key in ("vendor_id", "vendor") or val is None:
                continue
            sets.append(f"r.{key} = {_escape(val)}")

        set_clause = ", ".join(sets)
        update_cypher = (
            f" MATCH (r:Resource {{vendor_id: '{vendor_id}', vendor: '{vendor}'}}) "
            f"SET {set_clause} "
            f"RETURN r "
        )
        rows = await execute_cypher(conn, graph_name, update_cypher)
    else:
        # Step 2b: create new node
        uid = str(uuid.uuid4())
        props = {
            "uid": uid,
            "vendor_id": resource_data["vendor_id"],
            "vendor": resource_data["vendor"],
            "first_seen": now,
            "last_seen": now,
        }
        for key, val in resource_data.items():
            if key in ("vendor_id", "vendor") or val is None:
                continue
            props[key] = val

        prop_parts = []
        for k, v in props.items():
            prop_parts.append(f"{k}: {_escape(v)}")
        prop_str = ", ".join(prop_parts)

        create_cypher = (
            f" CREATE (r:Resource {{{prop_str}}}) "
            f"RETURN r "
        )
        rows = await execute_cypher(conn, graph_name, create_cypher)

    if rows:
        return rows[0] if isinstance(rows[0], dict) else {}
    return {}


async def get_resource_node(
    conn: AsyncConnection,
    graph_name: str,
    uid: str,
) -> dict | None:
    """Retrieve a Resource node by its uid. Returns properties or None."""
    escaped_uid = uid.replace("'", "\\'")
    cypher = f" MATCH (r:Resource {{uid: '{escaped_uid}'}}) RETURN r "

    rows = await execute_cypher(conn, graph_name, cypher)
    if rows:
        return rows[0] if isinstance(rows[0], dict) else None
    return None


async def update_resource_node(
    conn: AsyncConnection,
    graph_name: str,
    uid: str,
    updates: dict,
) -> dict | None:
    """Update properties on an existing Resource node. Returns updated node or None."""
    if not updates:
        return await get_resource_node(conn, graph_name, uid)

    set_parts = []
    for key, val in updates.items():
        if val is None:
            continue
        if isinstance(val, dict):
            escaped = json.dumps(val).replace("'", "\\'")
            set_parts.append(f"r.{key} = '{escaped}'")
        elif isinstance(val, (int, float)):
            set_parts.append(f"r.{key} = {val}")
        else:
            escaped = str(val).replace("'", "\\'")
            set_parts.append(f"r.{key} = '{escaped}'")

    if not set_parts:
        return await get_resource_node(conn, graph_name, uid)

    now = datetime.now(UTC).isoformat()
    set_parts.append(f"r.last_seen = '{now}'")
    set_clause = ", ".join(set_parts)

    escaped_uid = uid.replace("'", "\\'")
    cypher = (
        f" MATCH (r:Resource {{uid: '{escaped_uid}'}}) "
        f"SET {set_clause} "
        f"RETURN r "
    )

    rows = await execute_cypher(conn, graph_name, cypher)
    if rows:
        return rows[0] if isinstance(rows[0], dict) else None
    return None


async def delete_resource_node(
    conn: AsyncConnection,
    graph_name: str,
    uid: str,
) -> bool:
    """Delete a Resource node and all its edges. Returns True if a node was deleted."""
    escaped_uid = uid.replace("'", "\\'")
    cypher = (
        f" MATCH (r:Resource {{uid: '{escaped_uid}'}}) "
        f"DETACH DELETE r "
        f"RETURN true "
    )

    rows = await execute_cypher(conn, graph_name, cypher)
    return len(rows) > 0


async def get_subgraph(
    pool,
    graph_name: str,
    uid: str,
    depth: int = 1,
) -> dict:
    """Get the subgraph around a resource at a given traversal depth.

    Uses separate queries for nodes and edges because AGE does not support
    the ``relationships(path)`` or ``nodes(path)`` Cypher functions.

    Returns a dict with 'nodes' and 'edges' lists.
    """
    escaped_uid = uid.replace("'", "\\'")

    nodes_by_uid: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[str] = set()

    async with pool.connection() as conn:
        # 1. Get the start node
        start_cypher = (
            f" MATCH (s:Resource {{uid: '{escaped_uid}'}}) RETURN s "
        )
        start_rows = await execute_cypher(conn, graph_name, start_cypher)
        for node in start_rows:
            if isinstance(node, dict) and "uid" in node:
                nodes_by_uid[node["uid"]] = {
                    "uid": node.get("uid", ""),
                    "name": node.get("name", ""),
                    "category": node.get("category", ""),
                    "vendor": node.get("vendor", ""),
                    "normalised_type": node.get("normalised_type", ""),
                }

        # Helper to extract a value from a row (dict or list)
        def _val(row, key_or_idx):
            if isinstance(row, dict):
                return row.get(key_or_idx)
            if isinstance(row, (list, tuple)):
                return row[key_or_idx] if key_or_idx < len(row) else None
            return None

        # 2. Iteratively expand depth levels using BFS
        current_uids = {escaped_uid}
        for _level in range(depth):
            if not current_uids:
                break

            next_uids: set[str] = set()
            for cur_uid in current_uids:
                esc = cur_uid.replace("'", "\\'")

                # Outgoing edges
                out_cypher = (
                    f" MATCH (a:Resource {{uid: '{esc}'}})-[r]->(b:Resource) "
                    f"RETURN a.uid AS a_uid, b.uid AS b_uid, "
                    f"b.name AS b_name, b.category AS b_cat, "
                    f"b.vendor AS b_vendor, b.normalised_type AS b_ntype, "
                    f"label(r) AS rtype, r.confidence AS rconf "
                )
                out_rows = await execute_cypher(
                    conn, graph_name, out_cypher,
                    columns="(a_uid agtype, b_uid agtype, b_name agtype, "
                            "b_cat agtype, b_vendor agtype, b_ntype agtype, "
                            "rtype agtype, rconf agtype)",
                )
                for row in out_rows:
                    a_uid = str(_val(row, "a_uid") or _val(row, 0) or "")
                    b_uid = str(_val(row, "b_uid") or _val(row, 1) or "")
                    b_name = str(_val(row, "b_name") or _val(row, 2) or "")
                    b_cat = str(_val(row, "b_cat") or _val(row, 3) or "")
                    b_vendor = str(_val(row, "b_vendor") or _val(row, 4) or "")
                    b_ntype = str(_val(row, "b_ntype") or _val(row, 5) or "")
                    rtype = str(_val(row, "rtype") or _val(row, 6) or "")
                    rconf_raw = _val(row, "rconf") or _val(row, 7)
                    rconf = float(rconf_raw) if rconf_raw is not None else 1.0

                    if b_uid and b_uid not in nodes_by_uid:
                        nodes_by_uid[b_uid] = {
                            "uid": b_uid,
                            "name": b_name,
                            "category": b_cat,
                            "vendor": b_vendor,
                            "normalised_type": b_ntype,
                        }
                        next_uids.add(b_uid)

                    edge_key = f"{a_uid}-{b_uid}-{rtype}"
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append({
                            "source_uid": a_uid,
                            "target_uid": b_uid,
                            "type": rtype,
                            "confidence": rconf,
                        })

                # Incoming edges
                in_cypher = (
                    f" MATCH (a:Resource)-[r]->(b:Resource {{uid: '{esc}'}}) "
                    f"RETURN a.uid AS a_uid, a.name AS a_name, "
                    f"a.category AS a_cat, a.vendor AS a_vendor, "
                    f"a.normalised_type AS a_ntype, "
                    f"b.uid AS b_uid, label(r) AS rtype, "
                    f"r.confidence AS rconf "
                )
                in_rows = await execute_cypher(
                    conn, graph_name, in_cypher,
                    columns="(a_uid agtype, a_name agtype, a_cat agtype, "
                            "a_vendor agtype, a_ntype agtype, b_uid agtype, "
                            "rtype agtype, rconf agtype)",
                )
                for row in in_rows:
                    a_uid = str(_val(row, "a_uid") or _val(row, 0) or "")
                    a_name = str(_val(row, "a_name") or _val(row, 1) or "")
                    a_cat = str(_val(row, "a_cat") or _val(row, 2) or "")
                    a_vendor = str(_val(row, "a_vendor") or _val(row, 3) or "")
                    a_ntype = str(_val(row, "a_ntype") or _val(row, 4) or "")
                    b_uid = str(_val(row, "b_uid") or _val(row, 5) or "")
                    rtype = str(_val(row, "rtype") or _val(row, 6) or "")
                    rconf_raw = _val(row, "rconf") or _val(row, 7)
                    rconf = float(rconf_raw) if rconf_raw is not None else 1.0

                    if a_uid and a_uid not in nodes_by_uid:
                        nodes_by_uid[a_uid] = {
                            "uid": a_uid,
                            "name": a_name,
                            "category": a_cat,
                            "vendor": a_vendor,
                            "normalised_type": a_ntype,
                        }
                        next_uids.add(a_uid)

                    edge_key = f"{a_uid}-{b_uid}-{rtype}"
                    if edge_key not in seen_edges:
                        seen_edges.add(edge_key)
                        edges.append({
                            "source_uid": a_uid,
                            "target_uid": b_uid,
                            "type": rtype,
                            "confidence": rconf,
                        })

            current_uids = next_uids

    return {
        "nodes": list(nodes_by_uid.values()),
        "edges": edges,
    }


async def query_resource_nodes(
    conn: AsyncConnection,
    graph_name: str,
    filters: dict,
    cursor_uid: str | None = None,
    page_size: int = 50,
) -> list[dict]:
    """Query Resource nodes with optional filters and cursor-based pagination.

    Filters are applied as WHERE clauses (exact match).
    Results are ordered by uid with cursor-based pagination using WHERE uid > cursor_uid.
    Returns up to page_size + 1 rows (extra row indicates more pages).
    """
    where_parts = []

    for key, val in filters.items():
        if val is not None:
            escaped = str(val).replace("'", "\\'")
            where_parts.append(f"r.{key} = '{escaped}'")

    if cursor_uid is not None:
        escaped_cursor = cursor_uid.replace("'", "\\'")
        where_parts.append(f"r.uid > '{escaped_cursor}'")

    where_clause = ""
    if where_parts:
        where_clause = "WHERE " + " AND ".join(where_parts)

    cypher = (
        f" MATCH (r:Resource) "
        f"{where_clause} "
        f"RETURN r "
        f"ORDER BY r.uid "
        f"LIMIT {page_size + 1} "
    )

    return await execute_cypher(conn, graph_name, cypher)
