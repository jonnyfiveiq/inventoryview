"""Async PostgreSQL + Apache AGE connection pool."""

import logging

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None


async def _configure_age(conn: AsyncConnection) -> None:
    """Configure each connection for Apache AGE.

    If AGE is in shared_preload_libraries, LOAD is unnecessary.
    We set autocommit to avoid transaction state issues in the configure callback.
    """
    await conn.set_autocommit(True)
    try:
        await conn.execute("LOAD 'age';")
    except Exception:
        pass  # AGE already loaded via shared_preload_libraries
    await conn.execute("SET search_path = ag_catalog, \"$user\", public;")
    await conn.set_autocommit(False)


async def init_pool(database_url: str) -> AsyncConnectionPool:
    """Create and open the async connection pool."""
    global _pool
    pool = AsyncConnectionPool(
        conninfo=database_url,
        min_size=2,
        max_size=10,
        configure=_configure_age,
        kwargs={"row_factory": dict_row},
    )
    await pool.open()
    _pool = pool
    logger.info("Database connection pool opened")
    return pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


def get_pool() -> AsyncConnectionPool:
    """Get the current connection pool. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool


async def check_age_extension(pool: AsyncConnectionPool) -> bool:
    """Check if the Apache AGE extension is available."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT 1 FROM pg_extension WHERE extname = 'age'"
        )
        row = await result.fetchone()
        return row is not None


async def ensure_graph_exists(pool: AsyncConnectionPool, graph_name: str) -> None:
    """Create the graph if it doesn't exist."""
    async with pool.connection() as conn:
        result = await conn.execute(
            "SELECT 1 FROM ag_catalog.ag_graph WHERE name = %s",
            [graph_name],
        )
        row = await result.fetchone()
        if row is None:
            await conn.execute("SELECT ag_catalog.create_graph(%s)", [graph_name])
            logger.info("Created graph: %s", graph_name)
