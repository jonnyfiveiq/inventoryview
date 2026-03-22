#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# InventoryView — single-container entrypoint
# Starts PostgreSQL, runs migrations, then launches uvicorn.
# ============================================================

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
IV_DB_NAME="${IV_DB_NAME:-inventoryview}"
IV_DB_USER="${IV_DB_USER:-inventoryview}"
IV_DB_PASSWORD="${IV_DB_PASSWORD:-inventoryview}"

# ----------------------------------------------------------
# 1. Initialise PostgreSQL data directory if empty
# ----------------------------------------------------------
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "[entrypoint] Initialising PostgreSQL data directory..."
    su - postgres -c "initdb -D '$PGDATA'"
fi

# ----------------------------------------------------------
# 2. Start PostgreSQL in the background
# ----------------------------------------------------------
echo "[entrypoint] Starting PostgreSQL..."
su - postgres -c "pg_ctl -D '$PGDATA' -l /var/log/postgresql.log -o '-c listen_addresses=127.0.0.1 -c shared_preload_libraries=age' start"

# ----------------------------------------------------------
# 3. Wait for PostgreSQL to accept connections
# ----------------------------------------------------------
echo "[entrypoint] Waiting for PostgreSQL to be ready..."
until pg_isready -h 127.0.0.1 -U postgres -q; do
    sleep 1
done
echo "[entrypoint] PostgreSQL is ready."

# ----------------------------------------------------------
# 4. Create database and user if they don't exist
# ----------------------------------------------------------
echo "[entrypoint] Ensuring database and user exist..."

su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='${IV_DB_USER}'\"" \
    | grep -q 1 \
    || su - postgres -c "psql -c \"CREATE USER ${IV_DB_USER} WITH PASSWORD '${IV_DB_PASSWORD}';\""

su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='${IV_DB_NAME}'\"" \
    | grep -q 1 \
    || su - postgres -c "psql -c \"CREATE DATABASE ${IV_DB_NAME} OWNER ${IV_DB_USER};\""

su - postgres -c "psql -d '${IV_DB_NAME}' -c 'CREATE EXTENSION IF NOT EXISTS age;'"

# ----------------------------------------------------------
# 5. Run Alembic migrations
# ----------------------------------------------------------
echo "[entrypoint] Running database migrations..."
cd /app
alembic upgrade head

# ----------------------------------------------------------
# 6. Start uvicorn (exec replaces this shell process)
# ----------------------------------------------------------
echo "[entrypoint] Starting InventoryView application server..."
exec uvicorn inventoryview:app --host 0.0.0.0 --port 8080
