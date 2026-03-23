"""Resource drift tracking service."""

import json
import logging
from datetime import datetime

from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)


async def record_drift(
    pool: AsyncConnectionPool,
    resource_uid: str,
    field: str,
    old_value: str | None,
    new_value: str | None,
    changed_at: datetime | None = None,
    source: str = "collector",
) -> None:
    """Record a single field change for a resource."""
    async with pool.connection() as conn:
        if changed_at is not None:
            await conn.execute(
                "INSERT INTO resource_drift (resource_uid, field, old_value, new_value, changed_at, source) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (resource_uid, field, old_value, new_value, changed_at, source),
            )
        else:
            await conn.execute(
                "INSERT INTO resource_drift (resource_uid, field, old_value, new_value, source) "
                "VALUES (%s, %s, %s, %s, %s)",
                (resource_uid, field, old_value, new_value, source),
            )


async def record_drift_batch(
    pool: AsyncConnectionPool,
    resource_uid: str,
    old_props: dict,
    new_props: dict,
    tracked_fields: set[str] | None = None,
    source: str = "collector",
) -> list[dict]:
    """Compare old and new properties and record any changes.

    Returns list of drift entries that were recorded.
    """
    if tracked_fields is None:
        tracked_fields = {
            "state", "num_cpu", "memory_mb", "disk_gb", "cpu_cores",
            "ip_address", "version", "tools_status", "name",
            "normalised_type", "category", "region",
        }

    drifts = []
    for field in tracked_fields:
        old_val = _extract(old_props, field)
        new_val = _extract(new_props, field)
        if old_val != new_val and (old_val is not None or new_val is not None):
            drifts.append({
                "field": field,
                "old_value": old_val,
                "new_value": new_val,
            })
            await record_drift(pool, resource_uid, field, old_val, new_val, source=source)

    return drifts


def _extract(props: dict, field: str) -> str | None:
    """Extract a field value from either top-level or raw_properties."""
    if field in props and props[field] is not None:
        val = props[field]
        if isinstance(val, dict):
            return json.dumps(val)
        return str(val)

    raw = props.get("raw_properties") or {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None

    if field in raw and raw[field] is not None:
        val = raw[field]
        if isinstance(val, dict):
            return json.dumps(val)
        return str(val)

    return None


async def get_drift_history(
    pool: AsyncConnectionPool,
    resource_uid: str,
) -> list[dict]:
    """Get all drift entries for a resource, newest first."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT id, resource_uid, field, old_value, new_value, changed_at, source "
            "FROM resource_drift "
            "WHERE resource_uid = %s "
            "ORDER BY changed_at DESC",
            (resource_uid,),
        )
        rows = await result.fetchall()

    return [
        {
            "id": str(row["id"]),
            "resource_uid": row["resource_uid"],
            "field": row["field"],
            "old_value": row["old_value"],
            "new_value": row["new_value"],
            "changed_at": row["changed_at"].isoformat(),
            "source": row["source"],
        }
        for row in rows
    ]


async def get_drift_timeline(
    pool: AsyncConnectionPool,
    resource_uid: str,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    """Get aggregated daily drift counts for a resource within a date range.

    Returns {data: [{date, count, fields}], total_drift_count: int}.
    """
    from datetime import date, timedelta

    end_date = date.fromisoformat(end) if end else date.today()
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=364)

    async with pool.connection() as conn:
        # Daily aggregation within date range
        result = await conn.execute(
            "SELECT DATE(changed_at) AS day, "
            "       COUNT(*) AS cnt, "
            "       ARRAY_AGG(DISTINCT field) AS fields "
            "FROM resource_drift "
            "WHERE resource_uid = %s "
            "  AND changed_at >= %s::date "
            "  AND changed_at < %s::date + INTERVAL '1 day' "
            "GROUP BY DATE(changed_at) "
            "ORDER BY day",
            (resource_uid, start_date.isoformat(), end_date.isoformat()),
        )
        rows = await result.fetchall()

        # Total lifetime count
        total_result = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM resource_drift WHERE resource_uid = %s",
            (resource_uid,),
        )
        total_row = await total_result.fetchone()

    data = [
        {
            "date": row["day"].isoformat() if hasattr(row["day"], "isoformat") else str(row["day"]),
            "count": row["cnt"],
            "fields": list(row["fields"]) if row["fields"] else [],
        }
        for row in rows
    ]

    return {
        "data": data,
        "total_drift_count": total_row["cnt"] if total_row else 0,
    }


async def get_fleet_drift_timeline(
    pool: AsyncConnectionPool,
    start: str | None = None,
    end: str | None = None,
) -> dict:
    """Get aggregated daily drift counts across ALL resources within a date range.

    Returns {data: [{date, count, fields}], fleet_avg_lifetime: float, total_resources_with_drift: int}.
    """
    from datetime import date, timedelta

    end_date = date.fromisoformat(end) if end else date.today()
    start_date = date.fromisoformat(start) if start else end_date - timedelta(days=364)

    async with pool.connection() as conn:
        # Daily aggregation across all resources
        result = await conn.execute(
            "SELECT DATE(changed_at) AS day, "
            "       COUNT(*) AS cnt, "
            "       ARRAY_AGG(DISTINCT field) AS fields "
            "FROM resource_drift "
            "WHERE changed_at >= %s::date "
            "  AND changed_at < %s::date + INTERVAL '1 day' "
            "GROUP BY DATE(changed_at) "
            "ORDER BY day",
            (start_date.isoformat(), end_date.isoformat()),
        )
        rows = await result.fetchall()

        # Fleet stats
        stats_result = await conn.execute(
            "SELECT COUNT(*) AS total_events, "
            "       COUNT(DISTINCT resource_uid) AS total_resources "
            "FROM resource_drift"
        )
        stats_row = await stats_result.fetchone()

    data = [
        {
            "date": row["day"].isoformat() if hasattr(row["day"], "isoformat") else str(row["day"]),
            "count": row["cnt"],
            "fields": list(row["fields"]) if row["fields"] else [],
        }
        for row in rows
    ]

    total_events = stats_row["total_events"] if stats_row else 0
    total_resources = stats_row["total_resources"] if stats_row else 0
    fleet_avg = total_events / total_resources if total_resources > 0 else 0

    return {
        "data": data,
        "fleet_avg_lifetime": round(fleet_avg, 2),
        "total_resources_with_drift": total_resources,
    }


async def has_drift(
    pool: AsyncConnectionPool,
    resource_uid: str,
) -> bool:
    """Check if a resource has any drift history."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT 1 FROM resource_drift WHERE resource_uid = %s LIMIT 1",
            (resource_uid,),
        )
        row = await result.fetchone()
    return row is not None
