# ============================================================
# InventoryView — single-container image
# PostgreSQL 16 + Apache AGE + Python 3.12 + Frontend SPA
# Base: CentOS Stream 9
# ============================================================

# ----------------------------------------------------------
# Stage 1: build frontend static files
# ----------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

# ----------------------------------------------------------
# Stage 2: build Apache AGE extension
# ----------------------------------------------------------
FROM quay.io/centos/centos:stream9 AS age-builder

RUN dnf install -y --nogpgcheck \
        https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
        https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && dnf config-manager --set-enabled crb \
    && dnf install -y --nobest --nogpgcheck \
        postgresql16-server \
        postgresql16-devel \
        gcc \
        make \
        git \
        readline-devel \
        zlib-devel \
        flex \
        bison \
        perl \
    && dnf clean all

RUN git clone --branch release/PG16/1.5.0 --depth 1 \
        https://github.com/apache/age.git /tmp/age \
    && cd /tmp/age \
    && make PG_CONFIG=/usr/pgsql-16/bin/pg_config -j"$(nproc)" \
    && ( make PG_CONFIG=/usr/pgsql-16/bin/pg_config install 2>/dev/null \
         || ( cp age.so /usr/pgsql-16/lib/ \
              && cp age.control age--*.sql /usr/pgsql-16/share/extension/ ) )

# ----------------------------------------------------------
# Stage 3: final runtime image
# ----------------------------------------------------------
FROM quay.io/centos/centos:stream9

# Install PGDG repo, PostgreSQL 16, Python 3.12, and curl (for seed script)
RUN dnf install -y --nogpgcheck \
        https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && dnf install -y --nobest --nogpgcheck --allowerasing \
        postgresql16-server \
        postgresql16 \
        python3.12 \
        python3.12-pip \
        curl \
        jq \
    && dnf clean all \
    && ln -sf /usr/bin/python3.12 /usr/bin/python3

# Copy AGE extension artifacts from builder
COPY --from=age-builder /usr/pgsql-16/lib/age.so \
                         /usr/pgsql-16/lib/age.so
COPY --from=age-builder /usr/pgsql-16/share/extension/age* \
                         /usr/pgsql-16/share/extension/

# Ensure postgres user exists
RUN id postgres 2>/dev/null || useradd -r -m -d /var/lib/pgsql -s /bin/bash postgres

# ----------------------------------------------------------
# Application code & Python dependencies
# ----------------------------------------------------------
WORKDIR /app

COPY backend/pyproject.toml ./
COPY backend/src/ ./src/
COPY backend/alembic.ini ./
COPY backend/alembic/ ./alembic/

RUN python3.12 -m pip install --no-cache-dir . \
    && python3.12 -m pip install --no-cache-dir uvicorn[standard]

# ----------------------------------------------------------
# Frontend static files (served by FastAPI)
# ----------------------------------------------------------
COPY --from=frontend-builder /build/dist /app/ui

# ----------------------------------------------------------
# Seed script (runs on first boot)
# ----------------------------------------------------------
COPY seed_test_data.sh /app/seed_test_data.sh
RUN chmod +x /app/seed_test_data.sh

# ----------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ----------------------------------------------------------
# Environment defaults
# ----------------------------------------------------------
ENV PATH=/usr/pgsql-16/bin:$PATH \
    PGDATA=/var/lib/pgsql/data \
    IV_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/inventoryview \
    IV_VAULT_PASSPHRASE=default-dev-passphrase \
    IV_UI_DIR=/app/ui \
    IV_SEED_ON_BOOT=true

EXPOSE 8080

CMD ["/entrypoint.sh"]
