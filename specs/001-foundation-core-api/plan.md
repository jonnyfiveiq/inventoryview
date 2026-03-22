# Implementation Plan: Foundation Core API

**Branch**: `001-foundation-core-api` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-foundation-core-api/spec.md`

## Summary

Build the InventoryView M1 foundation: a single-container deployment bundling
FastAPI (async Python 3.12+), embedded PostgreSQL 16 with Apache AGE, JWT
authentication for a single admin user, an AES-256-GCM encrypted credential
vault, and a REST API for managing resources as a labelled property graph.
Zero configuration required to start.

## Technical Context

**Language/Version**: Python 3.12+ (async-first)
**Primary Dependencies**: FastAPI, uvicorn, psycopg[binary] (v3, async), PyJWT, cryptography (AES-256-GCM), argon2-cffi, pydantic, pydantic-settings, alembic
**Storage**: PostgreSQL 16+ with Apache AGE extension (embedded in container; external via DATABASE_URL opt-in)
**Testing**: pytest, pytest-asyncio, httpx (async client), testcontainers-python
**Target Platform**: Linux container (OCI-compliant Docker image)
**Project Type**: web-service (REST API + minimal web UI)
**Performance Goals**: 50 concurrent API requests without degradation (SC-008), startup < 60 seconds (SC-002)
**Constraints**: Single container, zero mandatory config, data persistence via volume mount, vault passphrase required via env var
**Scale/Scope**: Single admin user (MVP), resources stored as graph nodes, cursor-based pagination on all list endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Applies to M1? | Status | Notes |
|---|-----------|----------------|--------|-------|
| I | Graph-First | YES | PASS | Resources are nodes, relationships are edges in AGE. Cypher for traversal. Metadata (credentials, admin account) in standard PostgreSQL tables. |
| II | Normalised Taxonomy | PARTIAL | PASS | Resources carry `category` and `normalised_type` fields. Full taxonomy engine deferred to M3/M4. Storing vendor_type alongside normalised fields satisfies the principle for M1 scope. |
| III | Pluggable Collectors | NO | N/A | Collectors out of scope for M1. API endpoints accept resource data directly. No collector coupling introduced. |
| IV | Scored Intelligence | NO | N/A | Scoring out of scope for M1. No scoring fields or engine included. |
| V | Adaptive Learning | NO | N/A | Feedback loops out of scope for M1. |
| VI | Relationship-Centric | YES | PASS | Relationships stored as directed edges with type, source_collector, confidence, established_at, last_confirmed, inference_method. |
| VII | Open Boundaries | YES | PASS | Graph is unified with no vendor partitions. Resources from any vendor coexist. |
| VIII | Zero-Friction Deployment | YES | PASS | Single container, zero config, embedded PostgreSQL, sensible defaults. |

**Gate Result**: PASS -- no violations. All applicable principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-foundation-core-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── inventoryview/
│       ├── __init__.py
│       ├── main.py              # FastAPI app factory, lifespan, startup
│       ├── config.py            # pydantic-settings configuration
│       ├── database.py          # PostgreSQL + AGE connection pool (async)
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py        # Top-level v1 router
│       │       ├── health.py        # Health check endpoint
│       │       ├── auth.py          # Login, token revocation
│       │       ├── setup.py         # Initial admin setup
│       │       ├── resources.py     # Resource CRUD + graph queries
│       │       ├── relationships.py # Relationship CRUD
│       │       └── credentials.py   # Credential vault endpoints
│       ├── models/
│       │   ├── __init__.py
│       │   ├── admin.py         # Administrator model
│       │   ├── resource.py      # Resource node schema
│       │   ├── relationship.py  # Relationship edge schema
│       │   ├── credential.py    # Credential metadata + vault
│       │   └── auth.py          # JWT token models
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth.py          # JWT creation, validation, revocation
│       │   ├── vault.py         # AES-256-GCM encrypt/decrypt, Argon2id KDF
│       │   ├── graph.py         # AGE Cypher query execution, traversal
│       │   ├── resources.py     # Resource business logic
│       │   ├── relationships.py # Relationship business logic
│       │   └── credentials.py   # Credential CRUD with vault integration
│       ├── middleware/
│       │   ├── __init__.py
│       │   └── auth.py          # Bearer token authentication middleware
│       └── schemas/
│           ├── __init__.py
│           ├── pagination.py    # Cursor-based pagination schemas
│           ├── errors.py        # Standardised error response schemas
│           ├── resources.py     # Request/response schemas for resources
│           ├── relationships.py # Request/response schemas for relationships
│           ├── credentials.py   # Request/response schemas for credentials
│           └── auth.py          # Login/token schemas
├── alembic/
│   ├── alembic.ini
│   └── versions/               # Database migrations
├── tests/
│   ├── conftest.py
│   ├── contract/               # API contract tests
│   ├── integration/            # Integration tests (DB, vault)
│   └── unit/                   # Unit tests (services, models)
├── pyproject.toml
└── Dockerfile

frontend/
├── src/
│   ├── pages/
│   │   ├── SetupPage.tsx       # Initial admin password creation
│   │   └── LandingPage.tsx     # System status landing page
│   └── main.tsx
├── package.json
└── vite.config.ts

docker/
├── docker-compose.yml          # Development stack
├── supervisord.conf            # Process manager for embedded PG + uvicorn
└── entrypoint.sh               # Container entrypoint (init DB, start services)
```

**Structure Decision**: Web application structure (backend + frontend) selected.
Backend is the primary deliverable with full API. Frontend is minimal for M1
(setup screen + landing page only). Docker directory holds container orchestration.

## Complexity Tracking

> No constitution violations detected. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
