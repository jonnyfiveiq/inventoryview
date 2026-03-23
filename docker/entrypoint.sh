#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# InventoryView — single-container entrypoint
# Starts PostgreSQL, runs migrations, seeds data, launches app
# ============================================================

PGDATA="${PGDATA:-/var/lib/pgsql/data}"
IV_DB_NAME="${IV_DB_NAME:-inventoryview}"
IV_DB_USER="${IV_DB_USER:-inventoryview}"
IV_DB_PASSWORD="${IV_DB_PASSWORD:-inventoryview}"
IV_SEED_ON_BOOT="${IV_SEED_ON_BOOT:-false}"
SEED_PASSWORD="${SEED_PASSWORD:-SuperSecretPass123}"
PGBIN="/usr/pgsql-16/bin"
export PATH="${PGBIN}:${PATH}"

green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

# ----------------------------------------------------------
# 1. Initialise PostgreSQL data directory if empty
# ----------------------------------------------------------
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    green "[inventoryview] Initialising PostgreSQL data directory..."
    su - postgres -c "${PGBIN}/initdb -D '$PGDATA'"

    # Allow local trust and network md5 auth
    cat > "$PGDATA/pg_hba.conf" <<'HBA'
local all all trust
host all all 127.0.0.1/32 trust
host all all 0.0.0.0/0 md5
host all all ::0/0 md5
HBA
fi

# ----------------------------------------------------------
# 2. Start PostgreSQL in the background
# ----------------------------------------------------------
green "[inventoryview] Starting PostgreSQL..."
touch /var/log/postgresql.log
chown postgres:postgres /var/log/postgresql.log
su - postgres -c "${PGBIN}/pg_ctl -D '$PGDATA' -l /var/log/postgresql.log -o '-c listen_addresses=127.0.0.1 -c shared_preload_libraries=age' start"

# ----------------------------------------------------------
# 3. Wait for PostgreSQL to accept connections
# ----------------------------------------------------------
dim "[inventoryview] Waiting for PostgreSQL..."
until pg_isready -h 127.0.0.1 -U postgres -q; do
    sleep 1
done
green "[inventoryview] PostgreSQL is ready."

# ----------------------------------------------------------
# 4. Create database and AGE extension if needed
# ----------------------------------------------------------
dim "[inventoryview] Ensuring database exists..."

su - postgres -c "${PGBIN}/psql -tc \"SELECT 1 FROM pg_database WHERE datname='${IV_DB_NAME}'\"" \
    | grep -q 1 \
    || su - postgres -c "${PGBIN}/psql -c \"CREATE DATABASE ${IV_DB_NAME};\""

su - postgres -c "${PGBIN}/psql -d '${IV_DB_NAME}' -c 'CREATE EXTENSION IF NOT EXISTS age;'"

# ----------------------------------------------------------
# 5. Run Alembic migrations
# ----------------------------------------------------------
green "[inventoryview] Running database migrations..."
cd /app
alembic upgrade head

# ----------------------------------------------------------
# 6. Seed demo data on first boot (if enabled)
# ----------------------------------------------------------
SEED_MARKER="/var/lib/pgsql/.seeded"
if [ "$IV_SEED_ON_BOOT" = "true" ] && [ ! -f "$SEED_MARKER" ]; then
    green "[inventoryview] Seeding demo data (first boot)..."

    # Start uvicorn briefly in the background for the seed script
    uvicorn inventoryview.main:app --host 127.0.0.1 --port 8080 &
    UVICORN_PID=$!

    # Wait for the app to be ready
    for i in $(seq 1 30); do
        if curl -sf http://127.0.0.1:8080/api/v1/health > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Create admin account via setup endpoint
    curl -sf -X POST http://127.0.0.1:8080/api/v1/setup/init \
        -H 'Content-Type: application/json' \
        -d "{\"username\":\"admin\",\"password\":\"${SEED_PASSWORD}\"}" \
        > /dev/null 2>&1 || dim "[inventoryview] Admin account may already exist"

    # Run the seed script
    export SEED_BASE_URL="http://127.0.0.1:8080/api/v1"
    export SEED_PASSWORD
    if /app/seed_test_data.sh --vendor=all; then
        touch "$SEED_MARKER"
        green "[inventoryview] Demo data seeded successfully."
    else
        dim "[inventoryview] Seeding encountered errors — will retry on next boot"
    fi

    # Stop the temporary uvicorn
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
else
    if [ -f "$SEED_MARKER" ]; then
        dim "[inventoryview] Demo data already seeded (skipping)."
    fi
fi

# ----------------------------------------------------------
# 7. Start uvicorn (exec replaces this shell process)
# ----------------------------------------------------------
green "[inventoryview] InventoryView is starting on port 8080..."
green "[inventoryview] Open http://localhost:8080 in your browser"
if [ "$IV_SEED_ON_BOOT" = "true" ]; then
    dim "[inventoryview] Login: admin / ${SEED_PASSWORD}"
fi
exec uvicorn inventoryview.main:app --host 0.0.0.0 --port 8080
