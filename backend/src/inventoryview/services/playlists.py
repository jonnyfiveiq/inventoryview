"""Playlist management service — CRUD, membership, activity, timeline."""

import logging
import re
import uuid
from datetime import date, timedelta

from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert a playlist name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    slug = slug.strip("-")
    return slug or "playlist"


async def _unique_slug(conn, name: str, exclude_id: str | None = None) -> str:
    """Generate a unique slug, appending -2, -3, etc. on collision."""
    base = slugify(name)
    candidate = base
    suffix = 2
    while True:
        if exclude_id:
            result = await conn.execute(
                "SELECT 1 FROM playlist WHERE slug = %s AND id != %s LIMIT 1",
                (candidate, exclude_id),
            )
        else:
            result = await conn.execute(
                "SELECT 1 FROM playlist WHERE slug = %s LIMIT 1",
                (candidate,),
            )
        if not await result.fetchone():
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


# ---------------------------------------------------------------------------
# Playlist CRUD
# ---------------------------------------------------------------------------

async def create_playlist(
    pool: AsyncConnectionPool,
    name: str,
    description: str | None = None,
) -> dict:
    """Create a new playlist and log the activity."""
    async with pool.connection() as conn:
        slug = await _unique_slug(conn, name)
        result = await conn.execute(
            "INSERT INTO playlist (name, slug, description) "
            "VALUES (%s, %s, %s) "
            "RETURNING id, name, slug, description, created_at, updated_at",
            (name, slug, description),
        )
        row = await result.fetchone()
        playlist = _playlist_row_to_dict(row, member_count=0)

        # Log creation activity
        await _record_activity(
            conn,
            playlist_id=str(row["id"]),
            action="playlist_created",
        )
        return playlist


async def list_playlists(
    pool: AsyncConnectionPool,
    cursor: str | None = None,
    page_size: int = 50,
) -> dict:
    """List all playlists with member counts, paginated."""
    async with pool.connection() as conn:
        if cursor:
            result = await conn.execute(
                "SELECT p.*, "
                "  (SELECT COUNT(*) FROM playlist_membership pm WHERE pm.playlist_id = p.id) AS member_count "
                "FROM playlist p "
                "WHERE p.name > (SELECT name FROM playlist WHERE id = %s) "
                "ORDER BY p.name "
                "LIMIT %s",
                (cursor, page_size + 1),
            )
        else:
            result = await conn.execute(
                "SELECT p.*, "
                "  (SELECT COUNT(*) FROM playlist_membership pm WHERE pm.playlist_id = p.id) AS member_count "
                "FROM playlist p "
                "ORDER BY p.name "
                "LIMIT %s",
                (page_size + 1,),
            )
        rows = await result.fetchall()

    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    data = [_playlist_row_to_dict(r, member_count=r["member_count"]) for r in rows]
    next_cursor = str(rows[-1]["id"]) if has_more and rows else None

    return {
        "data": data,
        "next_cursor": next_cursor,
        "page_size": page_size,
    }


def _is_uuid(value: str) -> bool:
    """Check if a string looks like a UUID."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


async def get_playlist(
    pool: AsyncConnectionPool,
    identifier: str,
    graph_name: str | None = None,
    detail: str = "summary",
) -> dict | None:
    """Get a playlist by slug or UUID, with member resources."""
    async with pool.connection() as conn:
        if _is_uuid(identifier):
            result = await conn.execute(
                "SELECT p.*, "
                "  (SELECT COUNT(*) FROM playlist_membership pm WHERE pm.playlist_id = p.id) AS member_count "
                "FROM playlist p WHERE p.id = %s",
                (identifier,),
            )
        else:
            result = await conn.execute(
                "SELECT p.*, "
                "  (SELECT COUNT(*) FROM playlist_membership pm WHERE pm.playlist_id = p.id) AS member_count "
                "FROM playlist p WHERE p.slug = %s",
                (identifier,),
            )
        row = await result.fetchone()
        if not row:
            return None

        playlist = _playlist_row_to_dict(row, member_count=row["member_count"])

        # Get member resources
        members_result = await conn.execute(
            "SELECT resource_uid FROM playlist_membership "
            "WHERE playlist_id = %s ORDER BY added_at",
            (row["id"],),
        )
        member_rows = await members_result.fetchall()

        resources = []
        if member_rows and graph_name:
            from inventoryview.services.graph import get_resource_node

            for m in member_rows:
                raw_uid = m["resource_uid"]
                uid = raw_uid.decode("utf-8") if isinstance(raw_uid, (bytes, memoryview)) else str(raw_uid)
                r = await get_resource_node(conn, graph_name, uid)
                if r:
                    if detail == "full":
                        resources.append(r)
                    else:
                        resources.append({
                            "uid": r.get("uid"),
                            "name": r.get("name"),
                            "vendor": r.get("vendor"),
                            "normalised_type": r.get("normalised_type"),
                            "category": r.get("category"),
                            "state": r.get("state"),
                        })

        playlist["resources"] = resources
        return playlist


async def update_playlist(
    pool: AsyncConnectionPool,
    identifier: str,
    updates: dict,
) -> dict | None:
    """Update a playlist's name and/or description."""
    async with pool.connection() as conn:
        # Find the playlist
        if _is_uuid(identifier):
            result = await conn.execute(
                "SELECT * FROM playlist WHERE id = %s", (identifier,)
            )
        else:
            result = await conn.execute(
                "SELECT * FROM playlist WHERE slug = %s", (identifier,)
            )
        row = await result.fetchone()
        if not row:
            return None

        playlist_id = str(row["id"])
        old_name = row["name"]

        set_parts = []
        params = []

        if "name" in updates and updates["name"] is not None:
            new_name = updates["name"]
            new_slug = await _unique_slug(conn, new_name, exclude_id=playlist_id)
            set_parts.append("name = %s")
            params.append(new_name)
            set_parts.append("slug = %s")
            params.append(new_slug)
        if "description" in updates:
            set_parts.append("description = %s")
            params.append(updates["description"])

        if not set_parts:
            # Nothing to update — return current state
            count_result = await conn.execute(
                "SELECT COUNT(*) AS cnt FROM playlist_membership WHERE playlist_id = %s",
                (playlist_id,),
            )
            count_row = await count_result.fetchone()
            return _playlist_row_to_dict(row, member_count=count_row["cnt"])

        set_parts.append("updated_at = NOW()")
        params.append(playlist_id)

        result = await conn.execute(
            f"UPDATE playlist SET {', '.join(set_parts)} WHERE id = %s "
            "RETURNING id, name, slug, description, created_at, updated_at",
            tuple(params),
        )
        updated = await result.fetchone()

        count_result = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM playlist_membership WHERE playlist_id = %s",
            (playlist_id,),
        )
        count_row = await count_result.fetchone()

        # Log rename activity
        if "name" in updates and updates["name"] is not None and updates["name"] != old_name:
            await _record_activity(
                conn,
                playlist_id=playlist_id,
                action="playlist_renamed",
                detail=f"Renamed from '{old_name}' to '{updates['name']}'",
            )

        return _playlist_row_to_dict(updated, member_count=count_row["cnt"])


async def delete_playlist(
    pool: AsyncConnectionPool,
    identifier: str,
) -> bool:
    """Delete a playlist and all its membership/activity records (CASCADE)."""
    async with pool.connection() as conn:
        if _is_uuid(identifier):
            result = await conn.execute(
                "SELECT id, name FROM playlist WHERE id = %s", (identifier,)
            )
        else:
            result = await conn.execute(
                "SELECT id, name FROM playlist WHERE slug = %s", (identifier,)
            )
        row = await result.fetchone()
        if not row:
            return False

        # Log deletion before cascade removes activity table rows
        await _record_activity(
            conn,
            playlist_id=str(row["id"]),
            action="playlist_deleted",
            detail=f"Playlist '{row['name']}' deleted",
        )

        await conn.execute("DELETE FROM playlist WHERE id = %s", (row["id"],))
        return True


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------

async def add_resource(
    pool: AsyncConnectionPool,
    identifier: str,
    resource_uid: str,
    graph_name: str | None = None,
) -> dict | None:
    """Add a resource to a playlist. Returns membership dict or None if playlist not found."""
    async with pool.connection() as conn:
        # Find playlist
        if _is_uuid(identifier):
            result = await conn.execute("SELECT id FROM playlist WHERE id = %s", (identifier,))
        else:
            result = await conn.execute("SELECT id FROM playlist WHERE slug = %s", (identifier,))
        row = await result.fetchone()
        if not row:
            return None

        playlist_id = str(row["id"])

        # Get resource info for activity log
        resource_name = None
        resource_vendor = None
        if graph_name:
            from inventoryview.services.graph import execute_cypher
            safe_uid = resource_uid.replace("'", "\\'")
            cypher = f"MATCH (r:Resource {{uid: '{safe_uid}'}}) RETURN r"
            rows = await execute_cypher(conn, graph_name, cypher)
            if rows:
                resource_name = rows[0].get("name")
                resource_vendor = rows[0].get("vendor")

        # Insert membership
        try:
            ins_result = await conn.execute(
                "INSERT INTO playlist_membership (playlist_id, resource_uid) "
                "VALUES (%s, %s) RETURNING playlist_id, resource_uid, added_at",
                (playlist_id, resource_uid),
            )
            membership = await ins_result.fetchone()
        except Exception as e:
            # Unique constraint violation = already a member
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                return "duplicate"
            raise

        # Update playlist timestamp
        await conn.execute(
            "UPDATE playlist SET updated_at = NOW() WHERE id = %s", (playlist_id,)
        )

        # Log activity
        await _record_activity(
            conn,
            playlist_id=playlist_id,
            action="resource_added",
            resource_uid=resource_uid,
            resource_name=resource_name,
            resource_vendor=resource_vendor,
        )

        return {
            "playlist_id": str(membership["playlist_id"]),
            "resource_uid": membership["resource_uid"],
            "added_at": membership["added_at"].isoformat(),
        }


async def remove_resource(
    pool: AsyncConnectionPool,
    identifier: str,
    resource_uid: str,
    graph_name: str | None = None,
) -> bool:
    """Remove a resource from a playlist. Returns False if not found."""
    async with pool.connection() as conn:
        # Find playlist
        if _is_uuid(identifier):
            result = await conn.execute("SELECT id FROM playlist WHERE id = %s", (identifier,))
        else:
            result = await conn.execute("SELECT id FROM playlist WHERE slug = %s", (identifier,))
        row = await result.fetchone()
        if not row:
            return False

        playlist_id = str(row["id"])

        # Get resource info for activity log before removal
        resource_name = None
        resource_vendor = None
        if graph_name:
            from inventoryview.services.graph import execute_cypher
            safe_uid = resource_uid.replace("'", "\\'")
            cypher = f"MATCH (r:Resource {{uid: '{safe_uid}'}}) RETURN r"
            rows = await execute_cypher(conn, graph_name, cypher)
            if rows:
                resource_name = rows[0].get("name")
                resource_vendor = rows[0].get("vendor")

        del_result = await conn.execute(
            "DELETE FROM playlist_membership "
            "WHERE playlist_id = %s AND resource_uid = %s "
            "RETURNING id",
            (playlist_id, resource_uid),
        )
        deleted = await del_result.fetchone()
        if not deleted:
            return False

        # Update playlist timestamp
        await conn.execute(
            "UPDATE playlist SET updated_at = NOW() WHERE id = %s", (playlist_id,)
        )

        # Log activity
        await _record_activity(
            conn,
            playlist_id=playlist_id,
            action="resource_removed",
            resource_uid=resource_uid,
            resource_name=resource_name,
            resource_vendor=resource_vendor,
        )

        return True


async def get_playlists_for_resource(
    pool: AsyncConnectionPool,
    resource_uid: str,
) -> list[dict]:
    """Get all playlists that contain a given resource."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT p.id, p.name, p.slug, "
            "  (SELECT COUNT(*) FROM playlist_membership pm2 WHERE pm2.playlist_id = p.id) AS member_count "
            "FROM playlist p "
            "INNER JOIN playlist_membership pm ON pm.playlist_id = p.id "
            "WHERE pm.resource_uid = %s "
            "ORDER BY p.name",
            (resource_uid,),
        )
        rows = await result.fetchall()

    return [
        {
            "id": str(r["id"]),
            "name": r["name"],
            "slug": r["slug"],
            "member_count": r["member_count"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------

async def _record_activity(
    conn,
    playlist_id: str,
    action: str,
    resource_uid: str | None = None,
    resource_name: str | None = None,
    resource_vendor: str | None = None,
    detail: str | None = None,
) -> None:
    """Insert an activity log entry."""
    await conn.execute(
        "INSERT INTO playlist_activity "
        "(playlist_id, action, resource_uid, resource_name, resource_vendor, detail) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (playlist_id, action, resource_uid, resource_name, resource_vendor, detail),
    )


async def get_activity(
    pool: AsyncConnectionPool,
    identifier: str,
    filter_date: str | None = None,
    cursor: str | None = None,
    page_size: int = 50,
) -> dict | None:
    """Get activity log for a playlist, optionally filtered to a date."""
    async with pool.connection() as conn:
        # Find playlist
        if _is_uuid(identifier):
            result = await conn.execute("SELECT id FROM playlist WHERE id = %s", (identifier,))
        else:
            result = await conn.execute("SELECT id FROM playlist WHERE slug = %s", (identifier,))
        row = await result.fetchone()
        if not row:
            return None

        playlist_id = str(row["id"])

        params: list = [playlist_id]
        where_parts = ["playlist_id = %s"]

        if filter_date:
            where_parts.append("occurred_at >= %s::date AND occurred_at < %s::date + INTERVAL '1 day'")
            params.extend([filter_date, filter_date])

        if cursor:
            where_parts.append("occurred_at < (SELECT occurred_at FROM playlist_activity WHERE id = %s)")
            params.append(cursor)

        where_clause = " AND ".join(where_parts)
        params.append(page_size + 1)

        result = await conn.execute(
            f"SELECT id, action, resource_uid, resource_name, resource_vendor, detail, occurred_at "
            f"FROM playlist_activity "
            f"WHERE {where_clause} "
            f"ORDER BY occurred_at DESC "
            f"LIMIT %s",
            tuple(params),
        )
        rows = await result.fetchall()

    has_more = len(rows) > page_size
    if has_more:
        rows = rows[:page_size]

    data = [
        {
            "id": str(r["id"]),
            "action": r["action"],
            "resource_uid": r["resource_uid"],
            "resource_name": r["resource_name"],
            "resource_vendor": r["resource_vendor"],
            "detail": r["detail"],
            "occurred_at": r["occurred_at"].isoformat(),
        }
        for r in rows
    ]

    next_cursor = str(rows[-1]["id"]) if has_more and rows else None

    return {
        "data": data,
        "next_cursor": next_cursor,
        "page_size": page_size,
    }


async def get_activity_timeline(
    pool: AsyncConnectionPool,
    identifier: str,
    start: str | None = None,
    end: str | None = None,
) -> dict | None:
    """Get aggregated daily activity counts for a playlist's calendar heatmap."""
    async with pool.connection() as conn:
        # Find playlist
        if _is_uuid(identifier):
            result = await conn.execute("SELECT id FROM playlist WHERE id = %s", (identifier,))
        else:
            result = await conn.execute("SELECT id FROM playlist WHERE slug = %s", (identifier,))
        row = await result.fetchone()
        if not row:
            return None

        playlist_id = str(row["id"])

        end_date = date.fromisoformat(end) if end else date.today()
        start_date = date.fromisoformat(start) if start else end_date - timedelta(days=364)

        result = await conn.execute(
            "SELECT DATE(occurred_at) AS day, "
            "       COUNT(*) AS cnt, "
            "       ARRAY_AGG(DISTINCT action) AS actions "
            "FROM playlist_activity "
            "WHERE playlist_id = %s "
            "  AND occurred_at >= %s::date "
            "  AND occurred_at < %s::date + INTERVAL '1 day' "
            "GROUP BY DATE(occurred_at) "
            "ORDER BY day",
            (playlist_id, start_date.isoformat(), end_date.isoformat()),
        )
        rows = await result.fetchall()

        # Total lifetime count
        total_result = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM playlist_activity WHERE playlist_id = %s",
            (playlist_id,),
        )
        total_row = await total_result.fetchone()

    data = [
        {
            "date": r["day"].isoformat() if hasattr(r["day"], "isoformat") else str(r["day"]),
            "count": r["cnt"],
            "actions": list(r["actions"]) if r["actions"] else [],
        }
        for r in rows
    ]

    return {
        "data": data,
        "total_activity_count": total_row["cnt"] if total_row else 0,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _playlist_row_to_dict(row, member_count: int = 0) -> dict:
    """Convert a database row to a playlist dict."""
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "slug": row["slug"],
        "description": row["description"],
        "member_count": member_count,
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }
