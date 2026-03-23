"""Usage analytics and login audit service."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

logger = logging.getLogger(__name__)

# Simple in-memory guard for lazy purge (resets on restart — acceptable per research.md)
_last_purge_at: datetime | None = None
RETENTION_DAYS = 90


async def record_event(pool, user_id: UUID, feature_area: str, action: str) -> None:
    """Insert a single usage event."""
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO usage_event (user_id, feature_area, action) VALUES (%s, %s, %s)",
            [str(user_id), feature_area, action],
        )


async def record_events_batch(
    pool, user_id: UUID, events: list[dict[str, str]]
) -> int:
    """Insert multiple usage events. Returns count inserted."""
    async with pool.connection() as conn:
        for ev in events:
            await conn.execute(
                "INSERT INTO usage_event (user_id, feature_area, action) VALUES (%s, %s, %s)",
                [str(user_id), ev["feature_area"], ev["action"]],
            )
    return len(events)


async def record_login_audit(
    pool,
    username: str,
    outcome: str,
    ip_address: str,
    failure_reason: str | None = None,
) -> None:
    """Insert a login audit entry."""
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO login_audit (username, outcome, ip_address, failure_reason) VALUES (%s, %s, %s, %s)",
            [username, outcome, ip_address, failure_reason],
        )


async def get_usage_summary(
    pool,
    start: datetime,
    end: datetime,
) -> dict:
    """Aggregate usage stats grouped by feature area with trend calculation."""
    await _lazy_purge(pool)

    # Calculate previous period for trend comparison
    period_length = end - start
    prev_start = start - period_length
    prev_end = start

    async with pool.connection() as conn:
        # Current period aggregation
        result = await conn.execute(
            """
            SELECT feature_area,
                   COUNT(*) AS total_events,
                   COUNT(DISTINCT user_id) AS unique_users
            FROM usage_event
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY feature_area
            ORDER BY total_events DESC
            """,
            [start, end],
        )
        current_rows = await result.fetchall()

        # Previous period aggregation (for trend)
        result = await conn.execute(
            """
            SELECT feature_area, COUNT(*) AS total_events
            FROM usage_event
            WHERE created_at >= %s AND created_at < %s
            GROUP BY feature_area
            """,
            [prev_start, prev_end],
        )
        prev_rows = await result.fetchall()

        # Totals
        result = await conn.execute(
            """
            SELECT COUNT(*) AS total_events,
                   COUNT(DISTINCT user_id) AS total_unique_users
            FROM usage_event
            WHERE created_at >= %s AND created_at <= %s
            """,
            [start, end],
        )
        totals = await result.fetchone()

    prev_map = {row["feature_area"]: row["total_events"] for row in prev_rows}

    feature_areas = []
    for row in current_rows:
        fa = row["feature_area"]
        current_count = row["total_events"]
        prev_count = prev_map.get(fa, 0)

        if prev_count == 0:
            trend = "up" if current_count > 0 else "flat"
            trend_pct = 100.0 if current_count > 0 else 0.0
        else:
            change = ((current_count - prev_count) / prev_count) * 100
            trend_pct = round(change, 1)
            if abs(change) < 1:
                trend = "flat"
            elif change > 0:
                trend = "up"
            else:
                trend = "down"

        feature_areas.append({
            "feature_area": fa,
            "total_events": current_count,
            "unique_users": row["unique_users"],
            "trend": trend,
            "trend_percentage": trend_pct,
        })

    return {
        "period": {"start": start, "end": end},
        "feature_areas": feature_areas,
        "total_events": totals["total_events"] if totals else 0,
        "total_unique_users": totals["total_unique_users"] if totals else 0,
    }


async def get_feature_detail(
    pool,
    feature_area: str,
    start: datetime,
    end: datetime,
) -> dict:
    """Get action-level breakdown for a specific feature area."""
    async with pool.connection() as conn:
        result = await conn.execute(
            """
            SELECT action,
                   COUNT(*) AS count,
                   COUNT(DISTINCT user_id) AS unique_users
            FROM usage_event
            WHERE feature_area = %s AND created_at >= %s AND created_at <= %s
            GROUP BY action
            ORDER BY count DESC
            """,
            [feature_area, start, end],
        )
        rows = await result.fetchall()

    total = sum(r["count"] for r in rows)

    return {
        "feature_area": feature_area,
        "period": {"start": start, "end": end},
        "actions": [
            {"action": r["action"], "count": r["count"], "unique_users": r["unique_users"]}
            for r in rows
        ],
        "total_events": total,
    }


async def get_login_audit(
    pool,
    start: datetime,
    end: datetime,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Get paginated login audit entries with summary."""
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    async with pool.connection() as conn:
        # Summary counts
        result = await conn.execute(
            """
            SELECT COUNT(*) AS total_attempts,
                   COUNT(*) FILTER (WHERE outcome = 'success') AS successful,
                   COUNT(*) FILTER (WHERE outcome = 'failure') AS failed,
                   COUNT(DISTINCT username) AS unique_users
            FROM login_audit
            WHERE created_at >= %s AND created_at <= %s
            """,
            [start, end],
        )
        summary = await result.fetchone()

        # Paginated entries
        result = await conn.execute(
            """
            SELECT id, username, outcome, failure_reason, ip_address, created_at
            FROM login_audit
            WHERE created_at >= %s AND created_at <= %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            [start, end, page_size, offset],
        )
        entries = await result.fetchall()

    return {
        "period": {"start": start, "end": end},
        "summary": {
            "total_attempts": summary["total_attempts"] if summary else 0,
            "successful": summary["successful"] if summary else 0,
            "failed": summary["failed"] if summary else 0,
            "unique_users": summary["unique_users"] if summary else 0,
        },
        "entries": [dict(e) for e in entries],
        "page": page,
        "page_size": page_size,
        "total_count": summary["total_attempts"] if summary else 0,
    }


async def _lazy_purge(pool) -> None:
    """Purge data older than RETENTION_DAYS. Runs at most once per 24 hours."""
    global _last_purge_at
    now = datetime.now(UTC)

    if _last_purge_at and (now - _last_purge_at) < timedelta(hours=24):
        return

    cutoff = now - timedelta(days=RETENTION_DAYS)
    logger.info("Running usage data purge for records older than %s", cutoff.isoformat())

    async with pool.connection() as conn:
        result = await conn.execute(
            "DELETE FROM usage_event WHERE created_at < %s", [cutoff]
        )
        usage_deleted = result.rowcount
        result = await conn.execute(
            "DELETE FROM login_audit WHERE created_at < %s", [cutoff]
        )
        login_deleted = result.rowcount

    _last_purge_at = now
    if usage_deleted or login_deleted:
        logger.info("Purged %d usage events and %d login audit entries", usage_deleted, login_deleted)
