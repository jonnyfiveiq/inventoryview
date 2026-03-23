"""Asset correlation service.

Detects when two resources from different vendors represent the same
underlying physical or virtual asset by matching hardware identifiers
(SMBIOS UUID, serial number, baseboard serial) stored in raw_properties.

Example: An OpenShift node running on a VMware VM — the node's
serial_number in raw_properties matches the VM's smbios_uuid.
"""

import json
import logging
from datetime import UTC, datetime

from psycopg_pool import AsyncConnectionPool

from inventoryview.services.graph import execute_cypher, parse_agtype

logger = logging.getLogger(__name__)

# Keys in raw_properties that serve as hardware fingerprints.
# Order matters: first match wins.
HARDWARE_ID_KEYS = [
    "smbios_uuid",
    "serial_number",
    "system_serial",
    "baseboard_serial",
    "system_uuid",
    "bios_uuid",
    "dmi_uuid",
]


def _extract_hw_ids(raw_properties) -> dict[str, str]:
    """Extract normalised hardware identifiers from raw_properties."""
    if not raw_properties:
        return {}

    props = raw_properties

    # Handle multiple layers of string encoding
    for _ in range(3):
        if isinstance(props, str):
            # Strip surrounding quotes if present
            stripped = props.strip()
            if stripped.startswith("'") and stripped.endswith("'"):
                stripped = stripped[1:-1]
            try:
                props = json.loads(stripped)
            except (json.JSONDecodeError, ValueError):
                # Try unescaping backslashes
                try:
                    props = json.loads(stripped.replace("\\'", "'"))
                except (json.JSONDecodeError, ValueError):
                    return {}
        else:
            break

    if not isinstance(props, dict):
        return {}

    ids: dict[str, str] = {}
    for key in HARDWARE_ID_KEYS:
        val = props.get(key)
        if val and isinstance(val, str) and val.strip():
            # Normalise: lowercase, strip whitespace
            ids[key] = val.strip().lower()

    return ids


async def correlate_assets(
    pool: AsyncConnectionPool,
    graph_name: str,
) -> list[dict]:
    """Scan all resources and create SAME_ASSET edges where hardware IDs match.

    Returns a list of newly created correlations.
    """
    now = datetime.now(UTC).isoformat()

    # Step 1: Fetch all resources with raw_properties
    async with pool.connection() as conn:
        cypher = (
            " MATCH (r:Resource) "
            "WHERE r.raw_properties IS NOT NULL "
            "RETURN r.uid AS uid, r.vendor AS vendor, r.name AS name, "
            "r.raw_properties AS raw_props "
        )
        rows = await execute_cypher(
            conn, graph_name, cypher,
            columns="(uid agtype, vendor agtype, name agtype, raw_props agtype)",
        )

    # Step 2: Build a map of hardware_id_value -> list of resources
    hw_index: dict[str, list[dict]] = {}
    for row in rows:
        if isinstance(row, dict):
            uid = str(row.get("uid", ""))
            vendor = str(row.get("vendor", ""))
            name = str(row.get("name", ""))
            raw = row.get("raw_props")
        elif isinstance(row, (list, tuple)):
            uid = str(row[0]) if len(row) > 0 else ""
            vendor = str(row[1]) if len(row) > 1 else ""
            name = str(row[2]) if len(row) > 2 else ""
            raw = row[3] if len(row) > 3 else None
        else:
            continue

        if not uid:
            continue

        for key, val in _extract_hw_ids(raw).items():
            # Index by VALUE only — the same UUID can appear as
            # smbios_uuid on one vendor and serial_number on another
            if val not in hw_index:
                hw_index[val] = []
            hw_index[val].append({
                "uid": uid,
                "vendor": vendor,
                "name": name,
                "hw_key": key,
                "hw_value": val,
            })

    # Step 3: Find groups where 2+ resources from DIFFERENT vendors share a hw value
    correlations = []
    seen_pairs: set[str] = set()

    for _hw_value, resources in hw_index.items():
        if len(resources) < 2:
            continue

        # Only link resources from different vendors
        for i, a in enumerate(resources):
            for b in resources[i + 1:]:
                if a["vendor"] == b["vendor"]:
                    continue

                pair_key = tuple(sorted([a["uid"], b["uid"]]))
                pair_str = f"{pair_key[0]}:{pair_key[1]}"
                if pair_str in seen_pairs:
                    continue
                seen_pairs.add(pair_str)

                correlations.append({
                    "source_uid": a["uid"],
                    "target_uid": b["uid"],
                    "source_name": a["name"],
                    "target_name": b["name"],
                    "matched_key": a["hw_key"],
                    "matched_value": a["hw_value"],
                })

    # Step 4: Create SAME_ASSET edges (skip if already exists)
    created = []
    async with pool.connection() as conn:
        for corr in correlations:
            src = corr["source_uid"].replace("'", "\\'")
            tgt = corr["target_uid"].replace("'", "\\'")

            # Check if edge already exists in either direction
            check_cypher = (
                f" MATCH (a:Resource {{uid: '{src}'}})-[r:SAME_ASSET]-(b:Resource {{uid: '{tgt}'}}) "
                f"RETURN r "
            )
            existing = await execute_cypher(conn, graph_name, check_cypher)
            if existing:
                continue

            # Create bidirectional-ish edge (one direction is sufficient for graph queries)
            matched_key = corr["matched_key"].replace("'", "\\'")
            matched_value = corr["matched_value"].replace("'", "\\'")
            create_cypher = (
                f" MATCH (a:Resource {{uid: '{src}'}}), (b:Resource {{uid: '{tgt}'}}) "
                f"CREATE (a)-[r:SAME_ASSET {{confidence: 0.95, "
                f"matched_key: '{matched_key}', matched_value: '{matched_value}', "
                f"inference_method: 'hardware_id_correlation', "
                f"established_at: '{now}', last_confirmed: '{now}'}}]->(b) "
                f"RETURN r "
            )
            await execute_cypher(conn, graph_name, create_cypher)
            created.append(corr)
            logger.info(
                "SAME_ASSET: %s (%s) <-> %s (%s) via %s=%s",
                corr["source_name"], corr["source_uid"][:8],
                corr["target_name"], corr["target_uid"][:8],
                corr["matched_key"], corr["matched_value"],
            )

    return created


async def get_asset_twins(
    pool: AsyncConnectionPool,
    graph_name: str,
    uid: str,
) -> list[dict]:
    """Get all resources linked to this resource via SAME_ASSET edges."""
    escaped_uid = uid.replace("'", "\\'")

    async with pool.connection() as conn:
        cypher = (
            f" MATCH (a:Resource {{uid: '{escaped_uid}'}})-[r:SAME_ASSET]-(b:Resource) "
            f"RETURN b.uid AS uid, b.name AS name, b.vendor AS vendor, "
            f"b.normalised_type AS ntype, b.category AS category, "
            f"r.matched_key AS matched_key, r.matched_value AS matched_value, "
            f"r.confidence AS confidence "
        )
        rows = await execute_cypher(
            conn, graph_name, cypher,
            columns="(uid agtype, name agtype, vendor agtype, ntype agtype, "
                    "category agtype, matched_key agtype, matched_value agtype, "
                    "confidence agtype)",
        )

    twins = []
    for row in rows:
        if isinstance(row, dict):
            twins.append({
                "uid": str(row.get("uid", "")),
                "name": str(row.get("name", "")),
                "vendor": str(row.get("vendor", "")),
                "normalised_type": str(row.get("ntype", "")),
                "category": str(row.get("category", "")),
                "matched_key": str(row.get("matched_key", "")),
                "matched_value": str(row.get("matched_value", "")),
                "confidence": float(row.get("confidence", 0.95)),
            })
        elif isinstance(row, (list, tuple)):
            twins.append({
                "uid": str(row[0]) if len(row) > 0 else "",
                "name": str(row[1]) if len(row) > 1 else "",
                "vendor": str(row[2]) if len(row) > 2 else "",
                "normalised_type": str(row[3]) if len(row) > 3 else "",
                "category": str(row[4]) if len(row) > 4 else "",
                "matched_key": str(row[5]) if len(row) > 5 else "",
                "matched_value": str(row[6]) if len(row) > 6 else "",
                "confidence": float(row[7]) if len(row) > 7 and row[7] else 0.95,
            })

    return twins


async def get_asset_chain(
    pool: AsyncConnectionPool,
    graph_name: str,
    uid: str,
) -> dict:
    """Get the full chain of SAME_ASSET-linked resources (transitive).

    Uses BFS to walk all SAME_ASSET edges from the starting resource,
    returning every node and edge in the chain.

    Returns {nodes: [...], edges: [...]} where nodes include full resource
    metadata and edges include the matched hardware identifier.
    """
    escaped_uid = uid.replace("'", "\\'")
    nodes_by_uid: dict[str, dict] = {}
    edges: list[dict] = []
    seen_edges: set[str] = set()

    async with pool.connection() as conn:
        # Seed with the starting node
        start_cypher = (
            f" MATCH (r:Resource {{uid: '{escaped_uid}'}}) "
            f"RETURN r.uid AS uid, r.name AS name, r.vendor AS vendor, "
            f"r.normalised_type AS ntype, r.category AS category, "
            f"r.vendor_type AS vtype, r.state AS state "
        )
        start_rows = await execute_cypher(
            conn, graph_name, start_cypher,
            columns="(uid agtype, name agtype, vendor agtype, ntype agtype, "
                    "category agtype, vtype agtype, state agtype)",
        )

        def _parse_node(row):
            if isinstance(row, dict):
                return {
                    "uid": str(row.get("uid", "")),
                    "name": str(row.get("name", "")),
                    "vendor": str(row.get("vendor", "")),
                    "normalised_type": str(row.get("ntype", "")),
                    "category": str(row.get("category", "")),
                    "vendor_type": str(row.get("vtype", "")),
                    "state": str(row.get("state", "")),
                }
            elif isinstance(row, (list, tuple)):
                return {
                    "uid": str(row[0]) if len(row) > 0 else "",
                    "name": str(row[1]) if len(row) > 1 else "",
                    "vendor": str(row[2]) if len(row) > 2 else "",
                    "normalised_type": str(row[3]) if len(row) > 3 else "",
                    "category": str(row[4]) if len(row) > 4 else "",
                    "vendor_type": str(row[5]) if len(row) > 5 else "",
                    "state": str(row[6]) if len(row) > 6 else "",
                }
            return None

        for row in start_rows:
            node = _parse_node(row)
            if node and node["uid"]:
                nodes_by_uid[node["uid"]] = node

        # BFS walk along SAME_ASSET edges
        queue = [uid]
        visited: set[str] = {uid}

        while queue:
            current_uid = queue.pop(0)
            esc = current_uid.replace("'", "\\'")

            cypher = (
                f" MATCH (a:Resource {{uid: '{esc}'}})-[r:SAME_ASSET]-(b:Resource) "
                f"RETURN a.uid AS a_uid, b.uid AS b_uid, b.name AS name, "
                f"b.vendor AS vendor, b.normalised_type AS ntype, "
                f"b.category AS category, b.vendor_type AS vtype, "
                f"b.state AS state, "
                f"r.matched_key AS matched_key, r.matched_value AS matched_value "
            )
            rows = await execute_cypher(
                conn, graph_name, cypher,
                columns="(a_uid agtype, b_uid agtype, name agtype, vendor agtype, "
                        "ntype agtype, category agtype, vtype agtype, state agtype, "
                        "matched_key agtype, matched_value agtype)",
            )

            for row in rows:
                if isinstance(row, dict):
                    a_uid = str(row.get("a_uid", ""))
                    b_uid = str(row.get("b_uid", ""))
                    matched_key = str(row.get("matched_key", ""))
                    matched_value = str(row.get("matched_value", ""))
                    node = {
                        "uid": b_uid,
                        "name": str(row.get("name", "")),
                        "vendor": str(row.get("vendor", "")),
                        "normalised_type": str(row.get("ntype", "")),
                        "category": str(row.get("category", "")),
                        "vendor_type": str(row.get("vtype", "")),
                        "state": str(row.get("state", "")),
                    }
                elif isinstance(row, (list, tuple)):
                    a_uid = str(row[0]) if len(row) > 0 else ""
                    b_uid = str(row[1]) if len(row) > 1 else ""
                    matched_key = str(row[8]) if len(row) > 8 else ""
                    matched_value = str(row[9]) if len(row) > 9 else ""
                    node = {
                        "uid": b_uid,
                        "name": str(row[2]) if len(row) > 2 else "",
                        "vendor": str(row[3]) if len(row) > 3 else "",
                        "normalised_type": str(row[4]) if len(row) > 4 else "",
                        "category": str(row[5]) if len(row) > 5 else "",
                        "vendor_type": str(row[6]) if len(row) > 6 else "",
                        "state": str(row[7]) if len(row) > 7 else "",
                    }
                else:
                    continue

                if b_uid and b_uid not in nodes_by_uid:
                    nodes_by_uid[b_uid] = node

                edge_key = ":".join(sorted([a_uid, b_uid]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges.append({
                        "source_uid": a_uid,
                        "target_uid": b_uid,
                        "matched_key": matched_key,
                        "matched_value": matched_value,
                    })

                if b_uid not in visited:
                    visited.add(b_uid)
                    queue.append(b_uid)

        # Also include AAPHost nodes linked via AUTOMATED_BY edges
        # Walk from every resource in the chain to find automation links
        for resource_uid in list(nodes_by_uid.keys()):
            esc = resource_uid.replace("'", "\\'")

            aap_cypher = (
                f" MATCH (a:AAPHost)-[r:AUTOMATED_BY]->(res:Resource {{uid: '{esc}'}}) "
                f"RETURN a.host_id AS host_id, a.hostname AS hostname, "
                f"a.org_id AS org_id, a.smbios_uuid AS smbios_uuid, "
                f"a.correlation_type AS ctype, a.total_jobs AS total_jobs, "
                f"a.total_events AS total_events, "
                f"a.first_seen AS first_seen, a.last_seen AS last_seen, "
                f"r.correlation_key AS corr_key, r.inference_method AS method, "
                f"r.confidence AS confidence "
            )
            aap_rows = await execute_cypher(
                conn, graph_name, aap_cypher,
                columns="(host_id agtype, hostname agtype, org_id agtype, "
                        "smbios_uuid agtype, ctype agtype, total_jobs agtype, "
                        "total_events agtype, first_seen agtype, last_seen agtype, "
                        "corr_key agtype, method agtype, confidence agtype)",
            )

            for row in aap_rows:
                if not isinstance(row, dict):
                    continue
                host_id = str(row.get("host_id", "")).strip('"')
                hostname = str(row.get("hostname", "")).strip('"')
                method = str(row.get("method", "")).strip('"')
                corr_key = str(row.get("corr_key", "")).strip('"')
                confidence = row.get("confidence", 0)

                # Use host_id as the node uid (prefixed to avoid collisions)
                aap_uid = f"aap:{host_id}"
                if aap_uid not in nodes_by_uid:
                    nodes_by_uid[aap_uid] = {
                        "uid": aap_uid,
                        "name": hostname,
                        "vendor": "aap",
                        "normalised_type": "aap_host",
                        "category": "automation",
                        "vendor_type": "AAP::ManagedHost",
                        "state": "",
                    }

                edge_key = ":".join(sorted([resource_uid, aap_uid]))
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    # Use the inference method as the matched_key label
                    # and the correlation key as the matched_value
                    edges.append({
                        "source_uid": aap_uid,
                        "target_uid": resource_uid,
                        "matched_key": method,
                        "matched_value": corr_key,
                    })

    return {
        "nodes": list(nodes_by_uid.values()),
        "edges": edges,
    }
