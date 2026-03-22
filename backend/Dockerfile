# ============================================================
# InventoryView — single-container image
# PostgreSQL 16 + Apache AGE + Python 3.12 + s6-overlay
# Base: CentOS Stream 9
# ============================================================

# ----------------------------------------------------------
# Stage 1: build Apache AGE extension
# ----------------------------------------------------------
FROM quay.io/centos/centos:stream9 AS age-builder

RUN dnf install -y \
        https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && dnf install -y --nobest \
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
    && make PG_CONFIG=/usr/pgsql-16/bin/pg_config install

# ----------------------------------------------------------
# Stage 2: final runtime image
# ----------------------------------------------------------
FROM quay.io/centos/centos:stream9

# Install PGDG repo, PostgreSQL 16, and Python 3.12
RUN dnf install -y \
        https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && dnf install -y --nobest \
        postgresql16-server \
        postgresql16 \
        python3.12 \
        python3.12-pip \
        tar \
        xz \
        findutils \
    && dnf clean all

# Copy AGE extension artifacts from builder
COPY --from=age-builder /usr/pgsql-16/lib/age.so \
                         /usr/pgsql-16/lib/age.so
COPY --from=age-builder /usr/pgsql-16/share/extension/age* \
                         /usr/pgsql-16/share/extension/

# ----------------------------------------------------------
# Install s6-overlay v3.2.0.2
# ----------------------------------------------------------
ARG S6_OVERLAY_VERSION=3.2.0.2
ARG TARGETARCH=x86_64

ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp/
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${TARGETARCH}.tar.xz /tmp/

RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz \
    && tar -C / -Jxpf /tmp/s6-overlay-${TARGETARCH}.tar.xz \
    && rm -f /tmp/s6-overlay-*.tar.xz

# Ensure postgres user exists
RUN id postgres 2>/dev/null || useradd -r -m -d /var/lib/pgsql -s /bin/bash postgres

# ----------------------------------------------------------
# Application code & Python dependencies
# ----------------------------------------------------------
WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

RUN python3.12 -m pip install --no-cache-dir . \
    && python3.12 -m pip install --no-cache-dir uvicorn[standard]

# ----------------------------------------------------------
# s6 service: postgresql (longrun)
# ----------------------------------------------------------
RUN mkdir -p /etc/s6-overlay/s6-rc.d/postgresql \
    && printf 'longrun\n' > /etc/s6-overlay/s6-rc.d/postgresql/type

RUN printf '#!/bin/sh\nset -e\nexport PATH=/usr/pgsql-16/bin:$PATH\nif [ ! -f /var/lib/pgsql/data/PG_VERSION ]; then\n  su - postgres -c "/usr/pgsql-16/bin/initdb -D /var/lib/pgsql/data"\nfi\nexec su - postgres -c "/usr/pgsql-16/bin/postgres -D /var/lib/pgsql/data -c listen_addresses=* -c shared_preload_libraries=age"\n' \
    > /etc/s6-overlay/s6-rc.d/postgresql/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/postgresql/run

# Register postgresql in the default bundle
RUN mkdir -p /etc/s6-overlay/s6-rc.d/user/contents.d \
    && touch /etc/s6-overlay/s6-rc.d/user/contents.d/postgresql

# ----------------------------------------------------------
# s6 service: inventoryview (longrun, depends on postgresql)
# ----------------------------------------------------------
RUN mkdir -p /etc/s6-overlay/s6-rc.d/inventoryview/dependencies.d \
    && printf 'longrun\n' > /etc/s6-overlay/s6-rc.d/inventoryview/type \
    && touch /etc/s6-overlay/s6-rc.d/inventoryview/dependencies.d/postgresql

RUN printf '#!/bin/sh\nset -e\nexport PATH=/usr/pgsql-16/bin:$PATH\n\nuntil pg_isready -h 127.0.0.1 -U postgres -q; do\n    sleep 1\ndone\n\nsu - postgres -c "psql -tc \\"SELECT 1 FROM pg_database WHERE datname='\''inventoryview'\''\\"\n    | grep -q 1 || psql -c \\"CREATE DATABASE inventoryview;\\""\n\nsu - postgres -c "psql -d inventoryview -c \\"CREATE EXTENSION IF NOT EXISTS age;\\""\n\ncd /app\nalembic upgrade head\n\nexec uvicorn inventoryview.main:app --host 0.0.0.0 --port 8080\n' \
    > /etc/s6-overlay/s6-rc.d/inventoryview/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/inventoryview/run

# Register inventoryview in the default bundle
RUN touch /etc/s6-overlay/s6-rc.d/user/contents.d/inventoryview

# ----------------------------------------------------------
# Environment defaults
# ----------------------------------------------------------
ENV PATH=/usr/pgsql-16/bin:$PATH \
    PGDATA=/var/lib/pgsql/data \
    IV_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/inventoryview

EXPOSE 8080

ENTRYPOINT ["/init"]
