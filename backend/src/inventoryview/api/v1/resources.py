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
    """Get correlation detail (temperature gauge data) for a resource.

    Queries both the graph edge and relational aap_host data to build a
    complete picture — handles edges created by older correlation code that
    lack tier/matched_fields properties.
    """
    import json as _json

    from inventoryview.services.graph import execute_cypher

    pool = get_pool()
    settings = request.app.state.settings

    def _band(confidence: float) -> str:
        if confidence >= 0.90:
            return "deterministic"
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.50:
            return "moderate"
        return "low"

    # Map legacy match_reason values to canonical CorrelationTier names
    _TIER_ALIASES = {
        "smbios_match": "smbios_serial",
        "smbios": "smbios_serial",
        "bios_match": "bios_uuid",
        "bios": "bios_uuid",
        "mac_match": "mac_address",
        "mac": "mac_address",
        "ip_match": "ip_address",
        "ip": "ip_address",
        "fqdn_match": "fqdn",
        "hostname_match": "hostname_heuristic",
        "hostname": "hostname_heuristic",
        "learned": "learned_mapping",
        "manual": "learned_mapping",
    }

    def _clean(val) -> str | None:
        """Convert agtype values to clean strings, treating None as absent."""
        if val is None:
            return None
        s = str(val).strip('"')
        if s in ("None", "null", ""):
            return None
        # Strip Python bytes repr like b'...'
        if s.startswith("b'") and s.endswith("'"):
            s = s[2:-1]
        elif s.startswith('b"') and s.endswith('"'):
            s = s[2:-1]
        return s

    def _clean_value(val: str) -> str:
        """Strip Python bytes repr like b'...' from values."""
        s = str(val)
        if s.startswith("b'") and s.endswith("'"):
            s = s[2:-1]
        elif s.startswith('b"') and s.endswith('"'):
            s = s[2:-1]
        return s

    # 1. Query graph edge
    graph_row = None
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
        if rows and isinstance(rows[0], dict):
            graph_row = rows[0]

    # 2. Query relational data (richer: has ansible_facts, canonical_facts, etc.)
    rel_row = None
    async with pool.connection() as conn:
        from psycopg.rows import dict_row
        conn.row_factory = dict_row
        result = await conn.execute(
            """
            SELECT h.id, h.host_id, h.hostname, h.correlation_type, h.match_score,
                   h.match_reason, h.correlation_status, h.ansible_facts,
                   h.canonical_facts, h.smbios_uuid
            FROM aap_host h
            WHERE h.correlated_resource_uid = %(uid)s::uuid
              AND h.correlation_status IN ('auto_matched', 'manual_matched')
            ORDER BY h.match_score DESC NULLS LAST
            LIMIT 1
            """,
            {"uid": uid},
        )
        rel_row = await result.fetchone()

    if not graph_row and not rel_row:
        return {"resource_uid": uid, "is_correlated": False, "correlation": None}

    # 3. Merge: prefer graph edge confidence, fall back to relational
    conf = 0.0
    if graph_row and graph_row.get("conf") is not None:
        try:
            conf = float(graph_row["conf"])
        except (ValueError, TypeError):
            pass
    if conf == 0.0 and rel_row and rel_row.get("match_score") is not None:
        conf = float(rel_row["match_score"])

    # Tier: prefer graph, fall back to relational match_reason/correlation_type
    tier = None
    if graph_row:
        tier = _clean(graph_row.get("tier"))
    if not tier and rel_row:
        tier = rel_row.get("match_reason") or rel_row.get("correlation_type")
    # Normalize legacy tier names — also strip bytes repr
    if tier:
        tier = _clean_value(tier)
        tier = _TIER_ALIASES.get(tier, tier)

    # Status
    status = "proposed"
    if graph_row:
        status = _clean(graph_row.get("st")) or "proposed"
    if status == "proposed" and rel_row:
        rs = rel_row.get("correlation_status", "")
        if rs == "auto_matched":
            status = "auto_matched"
        elif rs == "manual_matched":
            status = "confirmed"

    # Hostname
    hostname = ""
    if graph_row:
        hostname = _clean(graph_row.get("hostname")) or ""
    if not hostname and rel_row:
        hostname = rel_row.get("hostname", "")

    host_id = ""
    if graph_row:
        host_id = _clean(graph_row.get("host_id")) or ""
    if not host_id and rel_row:
        host_id = str(rel_row.get("host_id", ""))

    # Matched fields: prefer graph edge, else reconstruct from relational data
    matched_fields = []
    if graph_row:
        mf_raw = graph_row.get("mf")
        if mf_raw is not None:
            try:
                s = str(mf_raw).strip('"')
                if s not in ("None", "null", ""):
                    parsed = _json.loads(s.replace('\\"', '"'))
                    if isinstance(parsed, list):
                        matched_fields = parsed
            except Exception:
                pass

    # If graph didn't have matched_fields, reconstruct from relational data
    if not matched_fields and rel_row:
        matched_fields = []
        facts = rel_row.get("ansible_facts") or {}
        canonical = rel_row.get("canonical_facts") or {}
        if isinstance(facts, str):
            try:
                facts = _json.loads(facts)
            except Exception:
                facts = {}
        if isinstance(canonical, str):
            try:
                canonical = _json.loads(canonical)
            except Exception:
                canonical = {}

        smbios = rel_row.get("smbios_uuid") or ""

        # Fetch resource raw_properties from graph for comparison
        res_raw = {}
        async with pool.connection() as conn2:
            res_cypher = (
                f" MATCH (r:Resource {{uid: '{uid}'}}) "
                f"RETURN r.raw_properties AS rp, r.name AS name"
            )
            res_rows = await execute_cypher(
                conn2, settings.graph_name, res_cypher,
                columns="(rp agtype, name agtype)",
            )
            if res_rows and isinstance(res_rows[0], dict):
                rp = res_rows[0].get("rp")
                if rp:
                    try:
                        rp_str = str(rp).strip('"')
                        res_raw = _json.loads(rp_str.replace('\\"', '"'))
                    except Exception:
                        res_raw = {}

        # Build matched_fields by comparing what we know
        if tier in ("smbios_serial",) or (not tier and smbios and res_raw.get("serial_number")):
            serial_fact = facts.get("ansible_product_serial") or ""
            serial_res = res_raw.get("serial_number", "")
            if serial_fact and serial_res:
                matched_fields.append({
                    "ansible_field": "ansible_product_serial",
                    "resource_field": "serial_number",
                    "values": [str(serial_fact), str(serial_res)],
                })

        if tier in ("bios_uuid", "smbios_uuid") or (not tier and smbios):
            uuid_fact = (
                facts.get("ansible_product_uuid")
                or canonical.get("ansible_machine_id")
                or smbios
                or ""
            )
            uuid_res = res_raw.get("smbios_uuid") or res_raw.get("system_uuid") or ""
            if uuid_fact and uuid_res:
                matched_fields.append({
                    "ansible_field": "ansible_product_uuid",
                    "resource_field": "smbios_uuid",
                    "values": [str(uuid_fact), str(uuid_res)],
                })

        if tier == "mac_address":
            mac_fact = ""
            dipv4 = facts.get("ansible_default_ipv4") or {}
            if isinstance(dipv4, dict):
                mac_fact = dipv4.get("macaddress", "")
            mac_res = res_raw.get("macAddress") or res_raw.get("mac_address") or ""
            if mac_fact and mac_res:
                matched_fields.append({
                    "ansible_field": "ansible_default_ipv4.macaddress",
                    "resource_field": "macAddress",
                    "values": [str(mac_fact), str(mac_res)],
                })

        if tier == "ip_address":
            ips = facts.get("ansible_all_ipv4_addresses") or []
            dipv4 = facts.get("ansible_default_ipv4") or {}
            ip_fact = ""
            if isinstance(dipv4, dict):
                ip_fact = dipv4.get("address", "")
            if not ip_fact and ips:
                ip_fact = ips[0] if isinstance(ips, list) and ips else ""
            ip_res = res_raw.get("ip_address") or ""
            if ip_fact and ip_res:
                matched_fields.append({
                    "ansible_field": "ansible_all_ipv4_addresses",
                    "resource_field": "ip_address",
                    "values": [str(ip_fact), str(ip_res)],
                })

        if tier in ("fqdn",):
            fqdn_fact = facts.get("ansible_fqdn") or canonical.get("ansible_fqdn") or ""
            # Resource FQDN may be its name
            fqdn_res = res_raw.get("fqdn") or ""
            if fqdn_fact:
                matched_fields.append({
                    "ansible_field": "ansible_fqdn",
                    "resource_field": "fqdn",
                    "values": [str(fqdn_fact), str(fqdn_res) or "(resource name)"],
                })

        if tier in ("hostname_heuristic",):
            hn_fact = facts.get("ansible_hostname") or canonical.get("ansible_hostname") or hostname
            matched_fields.append({
                "ansible_field": "ansible_hostname",
                "resource_field": "name (normalised)",
                "values": [str(hn_fact), "(normalised match)"],
            })

        # If we still have nothing but do have smbios, show what we can
        if not matched_fields and smbios:
            uuid_res = res_raw.get("smbios_uuid", "")
            if uuid_res:
                matched_fields.append({
                    "ansible_field": "smbios_uuid",
                    "resource_field": "smbios_uuid",
                    "values": [str(smbios), str(uuid_res)],
                })

    # Clean bytes representations from matched field values
    for mf in matched_fields:
        if "values" in mf and isinstance(mf["values"], list):
            mf["values"] = [_clean_value(v) for v in mf["values"]]

    confirmed_by = None
    if graph_row:
        confirmed_by = _clean(graph_row.get("cb"))

    return {
        "resource_uid": uid,
        "is_correlated": True,
        "correlation": {
            "aap_host_id": host_id,
            "aap_hostname": hostname,
            "confidence": conf,
            "tier": tier or "unknown",
            "matched_fields": matched_fields,
            "status": status,
            "temperature": _band(conf),
            "confirmed_by": confirmed_by,
            "created_at": _clean(graph_row.get("cat")) if graph_row else None,
            "updated_at": _clean(graph_row.get("uat")) if graph_row else None,
        },
    }
