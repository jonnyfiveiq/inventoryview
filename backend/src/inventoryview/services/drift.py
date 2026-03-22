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
