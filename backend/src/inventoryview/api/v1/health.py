"""Health-check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from inventoryview.database import get_pool

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Return service health status including database connectivity."""
    database = "disconnected"
    try:
        pool = get_pool()
        async with pool.connection() as conn:
            await conn.execute("SELECT 1")
        database = "connected"
    except Exception:
        database = "disconnected"

    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": database,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
