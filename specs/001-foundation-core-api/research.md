# Research: Foundation Core API

**Feature**: 001-foundation-core-api
**Date**: 2026-03-21
**Status**: Complete

## 1. Apache AGE Python Driver & Async Access

### Decision
Use **psycopg 3** (async mode) with raw SQL/Cypher queries via AGE's `ag_catalog` functions. No dedicated AGE Python wrapper needed.

### Rationale
- The official `apache-age-python` package on PyPI wraps psycopg2 (sync only) and has limited maintenance. It provides helper functions for Cypher query construction but no async support.
- psycopg v3 (`psycopg[binary]`) provides native async support via `AsyncConnection` and `AsyncConnectionPool`, which integrates naturally with FastAPI's async-first design.
- Apache AGE queries are executed as standard SQL: `SELECT * FROM ag_catalog.cypher('graph_name', $$ MATCH (n) RETURN n $$) AS (v agtype);`. This works directly through any PostgreSQL driver.
- The `agtype` result type maps to JSON-like structures that psycopg can parse with a custom type adapter.

### Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| `apache-age-python` (PyPI) | psycopg2-only, no async, limited maintenance |
| `age` wrapper library | Thin wrapper over psycopg2, adds dependency without value |
| Neo4j + Bolt driver | Violates constitution (PostgreSQL + AGE mandated) |

### Implementation Pattern
```python
async with pool.connection() as conn:
    result = await conn.execute(
        "SELECT * FROM ag_catalog.cypher(%s, %s) AS (v agtype)",
        ["inventory_graph", "MATCH (n:Resource) RETURN n LIMIT 10"]
    )
    rows = await result.fetchall()
```

### Key Setup
- `CREATE EXTENSION IF NOT EXISTS age;`
- `LOAD 'age';`
- `SET search_path = ag_catalog, "$user", public;`
- `SELECT create_graph('inventory_graph');`

---

## 2. JWT Authentication

### Decision
Use **PyJWT** (`pyjwt[crypto]`) for JWT token creation and validation. Token revocation via a database-backed blocklist table.

### Rationale
- PyJWT is the most widely used Python JWT library, lightweight, well-maintained, and supports RS256/HS256.
- For MVP single-admin, HS256 with a server-side secret is sufficient. RS256 can be adopted later for multi-service architectures.
- Token revocation requires server-side state. A `revoked_tokens` PostgreSQL table is the simplest approach that persists across restarts (satisfying the spec requirement that tokens survive restarts).
- Default expiry: 24 hours (configurable via `TOKEN_EXPIRY_HOURS` env var).

### Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| `python-jose` | Heavier dependency, JOSE features not needed for MVP |
| `authlib` | Full OAuth2 framework, overkill for single-admin JWT |
| In-memory revocation set | Tokens wouldn't survive restarts (violates spec edge case) |
| Redis-backed blocklist | External dependency violates zero-friction deployment |

### Token Flow
1. Admin POSTs credentials to `/api/v1/auth/login`
2. Server validates password (Argon2id hash comparison)
3. Server issues JWT with `sub` (admin ID), `iat`, `exp`, `jti` (unique token ID)
4. On each request, middleware validates JWT signature, checks expiry, checks `jti` against revocation table
5. Revocation: POST to `/api/v1/auth/revoke` adds `jti` to blocklist

---

## 3. Encrypted Credential Vault

### Decision
Use Python's **`cryptography`** library for AES-256-GCM encryption and **`argon2-cffi`** for Argon2id key derivation.

### Rationale
- `cryptography` is the standard Python cryptography library, well-audited, and provides low-level AES-GCM primitives.
- `argon2-cffi` wraps the reference Argon2 C implementation with a clean Python API.
- The vault passphrase (from `VAULT_PASSPHRASE` env var) is run through Argon2id to derive a 256-bit master key. The salt is generated once on first startup and stored in the database (not secret, only adds uniqueness).
- Each credential secret is encrypted with AES-256-GCM using a unique nonce (96-bit, randomly generated per encryption). The nonce and authentication tag are stored alongside the ciphertext.
- The derived master key is held in memory only -- never written to disk or logged.

### Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| `Fernet` (from cryptography) | Uses AES-CBC, spec mandates AES-256-GCM |
| `PyCryptodome` | `cryptography` is more widely adopted and better maintained |
| HashiCorp Vault | External dependency, opt-in for enterprise (not MVP) |
| KMS (AWS/Azure/GCP) | External dependency, violates zero-friction deployment |

### Storage Schema
```
credentials table:
  id (UUID PK)
  name (text)
  credential_type (text)  -- aws_key_pair, azure_sp, gcp_sa, etc.
  encrypted_secret (bytea) -- AES-256-GCM ciphertext
  nonce (bytea)            -- 96-bit GCM nonce
  auth_tag (bytea)         -- GCM authentication tag
  salt (bytea)             -- Argon2id salt (per-vault, not per-credential)
  metadata (jsonb)         -- non-secret fields
  created_at, updated_at, last_used_at (timestamptz)
```

---

## 4. Single-Container Deployment

### Decision
Use **s6-overlay** as the process supervisor inside the Docker container to manage PostgreSQL and uvicorn processes. Base image: `postgres:16-bookworm` with AGE compiled from source.

### Rationale
- s6-overlay is lightweight, designed for containers, handles process supervision, readiness checks, and graceful shutdown.
- Starting from the official PostgreSQL image ensures correct PG configuration. AGE is compiled and installed as an extension during the Docker build.
- uvicorn runs as the ASGI server for FastAPI with `--workers 1` (single process, async handles concurrency).
- The entrypoint script initialises the database on first run (creates AGE extension, graph, schema) and starts both services.

### Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| `supervisord` | Heavier, Python dependency inside container |
| `tini` + bash | tini is only an init, no process supervision for multiple services |
| Separate containers | Violates zero-friction single-container requirement |
| `dumb-init` | Same as tini -- init only, not a supervisor |

### Container Layout
```
/app/                    -- FastAPI application
/var/lib/postgresql/data -- PG data directory (volume mount point)
/etc/s6-overlay/         -- Service definitions
  s6-rc.d/
    postgresql/          -- PG service
    inventoryview/       -- uvicorn service (depends on postgresql)
```

### Volume Mount
- Users mount a volume to `/var/lib/postgresql/data` for persistence.
- If no volume is mounted, data lives in the container's ephemeral filesystem (acceptable for evaluation).

---

## 5. Project Structure & Framework Patterns

### Decision
Standard FastAPI project with `pydantic-settings` for configuration, `alembic` for migrations, and layered architecture (API routes -> services -> database).

### Rationale
- FastAPI's dependency injection naturally supports layered architecture.
- `pydantic-settings` reads from environment variables with type validation and defaults -- ideal for zero-config with opt-in overrides.
- `alembic` provides migration versioning for the relational schema (credentials, admin, tokens). AGE graph schema is managed via Cypher DDL in migrations.
- Cursor-based pagination implemented as a reusable dependency.

### Key Dependencies (pyproject.toml)
```
[project]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "psycopg[binary,pool]>=3.2",
    "pyjwt[crypto]>=2.9",
    "cryptography>=44.0",
    "argon2-cffi>=23.1",
    "pydantic>=2.10",
    "pydantic-settings>=2.7",
    "alembic>=1.14",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "httpx>=0.28",
    "ruff>=0.8",
]
```

### Configuration (pydantic-settings)
```python
class Settings(BaseSettings):
    database_url: str = "postgresql://inventoryview:inventoryview@localhost:5432/inventoryview"
    vault_passphrase: str  # Required, no default
    token_expiry_hours: int = 24
    host: str = "0.0.0.0"
    port: int = 8080
    graph_name: str = "inventory_graph"
    max_traversal_depth: int = 5

    model_config = SettingsConfigDict(env_prefix="IV_")
```

---

## 6. Testing Strategy

### Decision
Use **pytest** + **pytest-asyncio** + **httpx** for async API testing. Use **testcontainers** for integration tests with real PostgreSQL + AGE.

### Rationale
- `httpx.AsyncClient` with FastAPI's `TestClient` pattern enables async endpoint testing.
- `testcontainers-python` spins up a real PostgreSQL container with AGE for integration tests, ensuring graph queries are tested against the real engine.
- Unit tests mock the database layer for speed; integration tests use testcontainers for correctness.
- Contract tests validate API response schemas against the OpenAPI spec.

### Test Organisation
```
tests/
├── conftest.py          -- Shared fixtures (async client, test DB)
├── unit/
│   ├── test_vault.py    -- Encryption/decryption without DB
│   ├── test_auth.py     -- JWT creation/validation without DB
│   └── test_models.py   -- Pydantic schema validation
├── integration/
│   ├── test_graph.py    -- AGE Cypher operations
│   ├── test_resources.py -- Resource CRUD via API
│   ├── test_credentials.py -- Vault + DB integration
│   └── test_auth_flow.py -- Full login/revoke flow
└── contract/
    ├── test_resource_api.py -- Response schema conformance
    └── test_error_responses.py -- Error format conformance
```

---

## 7. Cursor-Based Pagination

### Decision
Use opaque base64-encoded cursors containing the sort key + ID of the last item.

### Rationale
- Cursor-based pagination is required by the spec (FR-014).
- Opaque cursors prevent clients from constructing arbitrary offsets (more performant than OFFSET/LIMIT for large datasets).
- Cursor encodes `(last_seen_sort_value, last_seen_id)` so the next page query uses `WHERE (sort_col, id) > (cursor_sort_val, cursor_id)`.
- Default page size: 50, max: 200.

### API Pattern
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6IC...",
    "has_more": true,
    "page_size": 50
  }
}
```
