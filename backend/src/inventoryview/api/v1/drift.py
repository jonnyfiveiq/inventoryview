"""Fleet-wide drift endpoints."""

import logging

from fastapi import APIRouter, Depends, Query, Request

from inventoryview.database import get_pool
from inventoryview.middleware.auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/fleet-timeline")
async def fleet_timeline(
    request: Request,
    start: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payload: dict = Depends(require_auth),
):
    """Get aggregated daily drift timeline across all resources."""
    from inventoryview.services.drift import get_fleet_drift_timeline

    pool = get_pool()
    return await get_fleet_drift_timeline(pool, start=start, end=end)


@router.get("/fleet-day")
async def fleet_day(
    request: Request,
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payload: dict = Depends(require_auth),
):
    """Get resources that had drift on a specific date."""
    from inventoryview.services.graph import execute_cypher

    pool = get_pool()
    settings = request.app.state.settings

    # Step 1: Get resource UIDs + drift counts from relational table
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT resource_uid, "
            "       COUNT(*) AS drift_count, "
            "       ARRAY_AGG(DISTINCT field) AS fields "
            "FROM resource_drift "
            "WHERE DATE(changed_at) = %s::date "
            "GROUP BY resource_uid "
            "ORDER BY drift_count DESC",
            (date,),
        )
        drift_rows = await result.fetchall()

    if not drift_rows:
        return {"date": date, "count": 0, "resources": []}

    # Step 2: Get resource details from graph
    uid_map: dict[str, dict] = {}
    for row in drift_rows:
        raw_uid = row["resource_uid"]
        uid = raw_uid.decode() if isinstance(raw_uid, (bytes, memoryview)) else str(raw_uid)
        uid_map[uid] = {
            "uid": uid,
            "drift_count": row["drift_count"],
            "fields": list(row["fields"]) if row["fields"] else [],
        }

    # Batch-fetch resource details from the graph
    uid_list = list(uid_map.keys())
    async with pool.connection() as conn:
        for uid in uid_list:
            cypher = (
                f" MATCH (r:Resource {{uid: '{uid}'}}) "
                "RETURN r.name AS name, r.vendor AS vendor, "
                "r.normalised_type AS ntype, r.category AS cat, r.state AS state"
            )
            rows = await execute_cypher(
                conn, settings.graph_name, cypher,
                columns="(name agtype, vendor agtype, ntype agtype, cat agtype, state agtype)",
            )
            if rows:
                r = rows[0] if isinstance(rows[0], dict) else {}
                uid_map[uid]["name"] = str(r.get("name", "")).strip('"')
                uid_map[uid]["vendor"] = str(r.get("vendor", "")).strip('"')
                uid_map[uid]["normalised_type"] = str(r.get("ntype", "")).strip('"')
                uid_map[uid]["category"] = str(r.get("cat", "")).strip('"')
                uid_map[uid]["state"] = str(r.get("state", "")).strip('"') or None
            else:
                uid_map[uid].update(
                    name=uid, vendor="unknown", normalised_type="unknown",
                    category="unknown", state=None,
                )

    resources = list(uid_map.values())
    return {"date": date, "count": len(resources), "resources": resources}
