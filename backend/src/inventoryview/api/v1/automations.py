"""AAP automation correlation endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth
from inventoryview.schemas.automation import (
    AAPHostItem,
    AAPHostListResponse,
    AutomationGraphResponse,
    CoverageResponse,
    HistoryResponse,
    PendingMatchListResponse,
    ReviewRequest,
    ReviewResponse,
    UploadCorrelationSummary,
    UploadResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB


@router.post("/upload", response_model=UploadResponse)
async def upload_metrics(
    request: Request,
    file: UploadFile,
    source_label: str | None = Query(None),
    payload: dict = Depends(require_auth),
):
    """Upload an AAP metrics utility archive and auto-correlate."""
    from inventoryview.services.aap_import import extract_archive, persist_import

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    fname = file.filename.lower()
    if not (fname.endswith(".zip") or fname.endswith(".tar.gz") or fname.endswith(".tgz")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Expected .zip or .tar.gz",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 200MB limit")

    label = source_label or file.filename or "unknown"
    import_id = str(uuid.uuid4())

    try:
        csvs = await extract_archive(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    pool = get_pool()
    stats = await persist_import(pool, csvs, label)

    # Auto-correlate
    correlation_summary = None
    try:
        from inventoryview.services.aap_correlation import correlate_hosts

        settings = request.app.state.settings
        summary = await correlate_hosts(pool, settings.graph_name, label)
        correlation_summary = UploadCorrelationSummary(**summary)
    except Exception:
        logger.exception("Auto-correlation failed after import")

    return UploadResponse(
        import_id=import_id,
        source_label=label,
        hosts_imported=stats["hosts_imported"],
        hosts_updated=stats["hosts_updated"],
        jobs_imported=stats["jobs_imported"],
        events_counted=stats["events_counted"],
        indirect_nodes_imported=stats["indirect_nodes_imported"],
        correlation_summary=correlation_summary,
    )


@router.get("/hosts", response_model=AAPHostListResponse)
async def list_hosts(
    request: Request,
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    search: str | None = Query(None),
    payload: dict = Depends(require_auth),
):
    """List AAP hosts with filtering and pagination."""
    pool = get_pool()
    settings = request.app.state.settings

    conditions = []
    params: dict = {"limit": limit + 1}

    if status:
        conditions.append("h.correlation_status = %(status)s")
        params["status"] = status

    if search:
        conditions.append("h.hostname ILIKE %(search)s")
        params["search"] = f"%{search}%"

    if cursor:
        from inventoryview.schemas.pagination import decode_cursor

        try:
            sort_val, item_id = decode_cursor(cursor)
            conditions.append("(h.created_at, h.id::text) < (%(cursor_ts)s::timestamptz, %(cursor_id)s)")
            params["cursor_ts"] = sort_val
            params["cursor_id"] = item_id
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    where = " AND ".join(conditions) if conditions else "TRUE"

    async with pool.connection() as conn:
        # Count
        count_result = await conn.execute(
            f"SELECT COUNT(*) AS cnt FROM aap_host h WHERE {where}", params
        )
        count_row = await count_result.fetchone()
        total = count_row["cnt"] if count_row else 0

        # Fetch
        result = await conn.execute(
            f"""
            SELECT h.*
            FROM aap_host h
            WHERE {where}
            ORDER BY h.created_at DESC, h.id DESC
            LIMIT %(limit)s
            """,
            params,
        )
        rows = await result.fetchall()

    items = []
    for row in rows[:limit]:
        correlated_resource = None
        if row.get("correlated_resource_uid"):
            # Fetch resource brief from graph
            try:
                async with pool.connection() as conn:
                    from inventoryview.services.graph import execute_cypher

                    uid = str(row["correlated_resource_uid"])
                    cypher = f" MATCH (r:Resource {{uid: '{uid}'}}) RETURN r.name AS name, r.vendor AS vendor, r.normalised_type AS ntype"
                    res_rows = await execute_cypher(
                        conn, settings.graph_name, cypher,
                        columns="(name agtype, vendor agtype, ntype agtype)",
                    )
                    if res_rows:
                        r = res_rows[0] if isinstance(res_rows[0], dict) else {}
                        correlated_resource = {
                            "uid": uid,
                            "name": str(r.get("name", "")),
                            "vendor": str(r.get("vendor", "")),
                            "normalised_type": str(r.get("ntype", "")),
                        }
            except Exception:
                pass

        items.append(AAPHostItem(
            id=row["id"],
            host_id=row["host_id"],
            hostname=row["hostname"],
            smbios_uuid=row.get("smbios_uuid"),
            org_id=row["org_id"],
            inventory_id=row["inventory_id"],
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            total_jobs=row["total_jobs"],
            total_events=row["total_events"],
            correlation_type=row["correlation_type"],
            correlation_status=row["correlation_status"],
            match_score=row.get("match_score"),
            match_reason=row.get("match_reason"),
            correlated_resource=correlated_resource,
        ))

    next_cursor = None
    if len(rows) > limit:
        from inventoryview.schemas.pagination import encode_cursor

        last = rows[limit - 1]
        next_cursor = encode_cursor(str(last["created_at"]), str(last["id"]))

    return AAPHostListResponse(items=items, next_cursor=next_cursor, total_count=total)


@router.get("/pending", response_model=PendingMatchListResponse)
async def list_pending(
    request: Request,
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    min_score: int | None = Query(None),
    max_score: int | None = Query(None),
    sort: str = Query("score_desc"),
    payload: dict = Depends(require_auth),
):
    """List pending matches for admin review."""
    pool = get_pool()
    settings = request.app.state.settings

    conditions = ["pm.status = 'pending'"]
    params: dict = {"limit": limit + 1}

    if min_score is not None:
        conditions.append("pm.match_score >= %(min_score)s")
        params["min_score"] = min_score
    if max_score is not None:
        conditions.append("pm.match_score <= %(max_score)s")
        params["max_score"] = max_score

    where = " AND ".join(conditions)

    order = "pm.match_score DESC, pm.id DESC"
    if sort == "score_asc":
        order = "pm.match_score ASC, pm.id ASC"
    elif sort == "hostname_asc":
        order = "h.hostname ASC, pm.id ASC"

    async with pool.connection() as conn:
        count_result = await conn.execute(
            f"""
            SELECT COUNT(*) AS cnt
            FROM aap_pending_match pm
            JOIN aap_host h ON pm.aap_host_id = h.id
            WHERE {where}
            """,
            params,
        )
        count_row = await count_result.fetchone()
        total = count_row["cnt"] if count_row else 0

        result = await conn.execute(
            f"""
            SELECT pm.*, h.host_id AS h_host_id, h.hostname AS h_hostname,
                   h.smbios_uuid AS h_smbios_uuid, h.total_jobs AS h_total_jobs
            FROM aap_pending_match pm
            JOIN aap_host h ON pm.aap_host_id = h.id
            WHERE {where}
            ORDER BY {order}
            LIMIT %(limit)s
            """,
            params,
        )
        rows = await result.fetchall()

    items = []
    for row in rows[:limit]:
        suggested_resource = None
        suid = row.get("suggested_resource_uid")
        if suid:
            try:
                async with pool.connection() as conn:
                    from inventoryview.services.graph import execute_cypher

                    uid = str(suid)
                    cypher = f" MATCH (r:Resource {{uid: '{uid}'}}) RETURN r.name AS name, r.vendor AS vendor, r.normalised_type AS ntype"
                    res_rows = await execute_cypher(
                        conn, settings.graph_name, cypher,
                        columns="(name agtype, vendor agtype, ntype agtype)",
                    )
                    if res_rows:
                        r = res_rows[0] if isinstance(res_rows[0], dict) else {}
                        suggested_resource = {
                            "uid": uid,
                            "name": str(r.get("name", "")),
                            "vendor": str(r.get("vendor", "")),
                            "normalised_type": str(r.get("ntype", "")),
                        }
            except Exception:
                pass

        items.append({
            "id": row["id"],
            "aap_host": {
                "id": row["aap_host_id"],
                "host_id": row["h_host_id"],
                "hostname": row["h_hostname"],
                "smbios_uuid": row.get("h_smbios_uuid"),
                "total_jobs": row["h_total_jobs"],
            },
            "suggested_resource": suggested_resource,
            "match_score": row["match_score"],
            "match_reason": row["match_reason"],
            "status": row["status"],
            "created_at": row["created_at"],
        })

    return PendingMatchListResponse(items=items, next_cursor=None, total_count=total)


@router.post("/pending/review", response_model=ReviewResponse)
async def review_pending(
    request: Request,
    body: ReviewRequest,
    payload: dict = Depends(require_auth),
):
    """Approve, reject, or ignore pending matches. Supports bulk operations."""
    from inventoryview.services.aap_correlation import process_review_actions

    pool = get_pool()
    settings = request.app.state.settings
    admin_id = payload.get("sub")

    results = await process_review_actions(
        pool, settings.graph_name, body.actions, admin_id
    )

    return ReviewResponse(
        processed=len(results),
        results=results,
    )


@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(
    request: Request,
    payload: dict = Depends(require_auth),
):
    """Get automation coverage statistics."""
    from inventoryview.services.aap_reports import get_coverage_stats

    pool = get_pool()
    settings = request.app.state.settings
    return await get_coverage_stats(pool, settings.graph_name)


@router.get("/resources/{resource_uid}/history", response_model=HistoryResponse)
async def get_resource_history(
    request: Request,
    resource_uid: str,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    payload: dict = Depends(require_auth),
):
    """Get automation history for a specific resource."""
    pool = get_pool()

    async with pool.connection() as conn:
        # Get all AAP hosts correlated to this resource
        hosts_result = await conn.execute(
            """
            SELECT h.hostname, h.correlation_type, h.match_reason, h.id AS host_id
            FROM aap_host h
            WHERE h.correlated_resource_uid = %(uid)s::uuid
              AND h.correlation_status IN ('auto_matched', 'manual_matched')
            """,
            {"uid": resource_uid},
        )
        host_rows = await hosts_result.fetchall()

        if not host_rows:
            return HistoryResponse(
                resource_uid=resource_uid,
                aap_hosts=[],
                executions={"items": [], "next_cursor": None, "total_count": 0},
            )

        host_ids = [str(r["host_id"]) for r in host_rows]
        aap_hosts = [
            {"hostname": r["hostname"], "correlation_type": r["correlation_type"], "match_reason": r.get("match_reason")}
            for r in host_rows
        ]

        # Count total
        placeholders = ", ".join(f"'{hid}'::uuid" for hid in host_ids)
        count_result = await conn.execute(
            f"SELECT COUNT(*) AS cnt FROM aap_job_execution WHERE aap_host_id IN ({placeholders})"
        )
        count_row = await count_result.fetchone()
        total = count_row["cnt"] if count_row else 0

        # Fetch executions with pagination
        exec_result = await conn.execute(
            f"""
            SELECT je.*, h.correlation_type
            FROM aap_job_execution je
            JOIN aap_host h ON je.aap_host_id = h.id
            WHERE je.aap_host_id IN ({placeholders})
            ORDER BY je.executed_at DESC
            LIMIT %(limit)s
            """,
            {"limit": limit + 1},
        )
        exec_rows = await exec_result.fetchall()

        # Get aggregate dates
        agg_result = await conn.execute(
            f"""
            SELECT MIN(je.executed_at) AS first_exec, MAX(je.executed_at) AS last_exec
            FROM aap_job_execution je
            WHERE je.aap_host_id IN ({placeholders})
            """
        )
        agg_row = await agg_result.fetchone()

    exec_items = []
    for row in exec_rows[:limit]:
        exec_items.append({
            "job_id": row["job_id"],
            "job_name": row["job_name"],
            "ok": row["ok"],
            "changed": row["changed"],
            "failures": row["failures"],
            "dark": row["dark"],
            "skipped": row["skipped"],
            "project": row.get("project"),
            "org_name": row.get("org_name"),
            "correlation_type": row.get("correlation_type", "direct"),
            "executed_at": row["executed_at"],
        })

    next_cursor = None
    if len(exec_rows) > limit:
        from inventoryview.schemas.pagination import encode_cursor

        last = exec_rows[limit - 1]
        next_cursor = encode_cursor(str(last["executed_at"]), str(last["id"]))

    return HistoryResponse(
        resource_uid=resource_uid,
        first_automated=agg_row["first_exec"] if agg_row else None,
        last_automated=agg_row["last_exec"] if agg_row else None,
        total_jobs=total,
        aap_hosts=aap_hosts,
        executions={"items": exec_items, "next_cursor": next_cursor, "total_count": total},
    )


@router.get("/reports/coverage")
async def get_coverage_report(
    request: Request,
    format: str = Query("json"),
    vendor: str | None = Query(None),
    payload: dict = Depends(require_auth),
):
    """Generate automation coverage report. Supports JSON and CSV export."""
    from inventoryview.services.aap_reports import generate_coverage_report

    pool = get_pool()
    settings = request.app.state.settings
    return await generate_coverage_report(pool, settings.graph_name, format, vendor)


@router.get("/graph/{resource_uid}", response_model=AutomationGraphResponse)
async def get_automation_graph(
    request: Request,
    resource_uid: str,
    payload: dict = Depends(require_auth),
):
    """Get automation subgraph for Cytoscape.js rendering."""
    pool = get_pool()
    settings = request.app.state.settings

    nodes = []
    edges = []

    async with pool.connection() as conn:
        from inventoryview.services.graph import execute_cypher

        # Get the resource node
        res_cypher = f" MATCH (r:Resource {{uid: '{resource_uid}'}}) RETURN r.uid AS uid, r.name AS name, r.vendor AS vendor, r.normalised_type AS ntype"
        res_rows = await execute_cypher(
            conn, settings.graph_name, res_cypher,
            columns="(uid agtype, name agtype, vendor agtype, ntype agtype)",
        )
        if res_rows:
            r = res_rows[0] if isinstance(res_rows[0], dict) else {}
            nodes.append({
                "id": str(r.get("uid", resource_uid)),
                "label": str(r.get("name", "")),
                "type": "Resource",
                "vendor": str(r.get("vendor", "")),
                "normalised_type": str(r.get("ntype", "")),
            })

        # Get AAPHost nodes connected via AUTOMATED_BY
        aap_cypher = (
            f" MATCH (a:AAPHost)-[rel:AUTOMATED_BY]->(r:Resource {{uid: '{resource_uid}'}}) "
            f"RETURN a.host_id AS host_id, a.hostname AS hostname, "
            f"a.correlation_type AS ctype, a.total_jobs AS tjobs, "
            f"rel.confidence AS conf, rel.correlation_type AS rel_ctype, "
            f"rel.inference_method AS method"
        )
        aap_rows = await execute_cypher(
            conn, settings.graph_name, aap_cypher,
            columns="(host_id agtype, hostname agtype, ctype agtype, tjobs agtype, conf agtype, rel_ctype agtype, method agtype)",
        )

        for row in aap_rows:
            if isinstance(row, dict):
                node_id = f"aaphost-{row.get('host_id', '')}"
                nodes.append({
                    "id": node_id,
                    "label": str(row.get("hostname", "")),
                    "type": "AAPHost",
                    "correlation_type": str(row.get("ctype", "direct")),
                    "total_jobs": int(row.get("tjobs", 0)) if row.get("tjobs") else 0,
                })
                edges.append({
                    "source": node_id,
                    "target": resource_uid,
                    "type": "AUTOMATED_BY",
                    "confidence": float(row.get("conf", 0)) if row.get("conf") else None,
                    "correlation_type": str(row.get("rel_ctype", "direct")),
                    "inference_method": str(row.get("method", "")) if row.get("method") else None,
                })

    return AutomationGraphResponse(nodes=nodes, edges=edges)
