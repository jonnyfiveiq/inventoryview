"""Alembic migration environment."""

import os
import re
from logging.config import fileConfig

from psycopg.adapt import Loader
from psycopg.pq import Format

from alembic import context
from sqlalchemy import create_engine, event, pool
from sqlalchemy.dialects.postgresql import base as pg_base


# psycopg-binary (C extension) + AGE shared_preload_libraries returns all text
# as bytes. Override with Python loaders that always decode to str.
class _StrLoader(Loader):
    format = Format.TEXT

    def load(self, data):
        if isinstance(data, memoryview):
            data = bytes(data)
        return data.decode("utf-8") if isinstance(data, bytes) else str(data)


class _StrBinaryLoader(Loader):
    format = Format.BINARY

    def load(self, data):
        if isinstance(data, memoryview):
            data = bytes(data)
        return data.decode("utf-8") if isinstance(data, bytes) else str(data)


_TEXT_OIDS = (19, 25, 1042, 1043)  # name, text, bpchar, varchar

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url() -> str:
    """Get database URL from env or alembic config."""
    url = os.environ.get("IV_DATABASE_URL")
    if not url:
        url = config.get_main_option("sqlalchemy.url", "")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


# Monkeypatch: psycopg3 + AGE returns version as bytes, SQLAlchemy expects str
_orig_get_server_version_info = pg_base.PGDialect._get_server_version_info


def _patched_get_server_version_info(self, connection):
    try:
        return _orig_get_server_version_info(self, connection)
    except TypeError:
        v = connection.exec_driver_sql("show server_version").scalar()
        if isinstance(v, (bytes, memoryview)):
            v = bytes(v).decode("utf-8")
        m = re.match(r"(\d+)\.?(\d+)?\.?(\d+)?", str(v))
        if m:
            return tuple(int(x) for x in m.groups() if x)
        return (16, 0)


pg_base.PGDialect._get_server_version_info = _patched_get_server_version_info


def _fix_text_decoding(dbapi_conn, connection_record):
    """Register Python text loaders to override C extension's broken AGE handling."""
    for oid in _TEXT_OIDS:
        dbapi_conn.adapters.register_loader(oid, _StrLoader)
        dbapi_conn.adapters.register_loader(oid, _StrBinaryLoader)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(url=url, target_metadata=None, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()
    engine = create_engine(url, poolclass=pool.NullPool)
    event.listen(engine, "connect", _fix_text_decoding)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
