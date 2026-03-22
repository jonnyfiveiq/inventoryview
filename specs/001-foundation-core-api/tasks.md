# Tasks: Foundation Core API

**Input**: Design documents from `/specs/001-foundation-core-api/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-v1.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/inventoryview/`, `backend/tests/`
- **Frontend**: `frontend/src/`
- **Docker**: `docker/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create backend directory structure per plan.md: `backend/src/inventoryview/{api/v1,models,services,middleware,schemas}/`, `backend/tests/{unit,integration,contract}/`, `backend/alembic/versions/` with `__init__.py` files
- [x] T002 Create `backend/pyproject.toml` with Python 3.12+ requirement and all dependencies from research.md (fastapi, uvicorn, psycopg[binary,pool], pyjwt[crypto], cryptography, argon2-cffi, pydantic, pydantic-settings, alembic) plus dev deps (pytest, pytest-asyncio, httpx, ruff)
- [x] T003 [P] Configure ruff linting and formatting in `backend/pyproject.toml` (tool.ruff section)
- [x] T004 [P] Initialize frontend project: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json` with React + TypeScript + Vite dependencies
- [x] T005 [P] Create `Makefile` at repository root with targets: dev, test, lint, build per quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Implement pydantic-settings configuration in `backend/src/inventoryview/config.py` with all env vars from research.md (IV_DATABASE_URL, IV_VAULT_PASSPHRASE, IV_TOKEN_EXPIRY_HOURS, IV_HOST, IV_PORT, IV_GRAPH_NAME, IV_MAX_TRAVERSAL_DEPTH) and validation that vault_passphrase is required
- [x] T007 Implement async PostgreSQL + AGE connection pool in `backend/src/inventoryview/database.py` using psycopg AsyncConnectionPool with configure callback that runs `LOAD 'age'` and `SET search_path` per research.md
- [x] T008 [P] Create standardised error response schemas in `backend/src/inventoryview/schemas/errors.py` matching contract error format (error.code, error.message, error.details) with VALIDATION_ERROR, UNAUTHORIZED, NOT_FOUND, CONFLICT, INTERNAL_ERROR codes
- [x] T009 [P] Create cursor-based pagination schemas and helpers in `backend/src/inventoryview/schemas/pagination.py` with base64-encoded opaque cursors, encode/decode functions, PaginatedResponse model (data, pagination.next_cursor, pagination.has_more, pagination.page_size) per research.md
- [x] T010 Create FastAPI app factory with async lifespan (pool open/close) in `backend/src/inventoryview/main.py` including exception handlers for standard error responses, CORS middleware, and router mounts at `/api/v1`
- [x] T011 Create v1 router aggregator in `backend/src/inventoryview/api/v1/router.py` that includes sub-routers for health, setup, auth, resources, relationships, credentials
- [x] T012 Initialize Alembic in `backend/alembic/` with `alembic.ini` and `env.py` configured for psycopg async driver, reading DATABASE_URL from config.py
- [x] T013 Create initial Alembic migration in `backend/alembic/versions/` for: administrators table, vault_config table (singleton), system_settings table, revoked_tokens table per data-model.md. Include AGE extension creation (`CREATE EXTENSION IF NOT EXISTS age`) and graph creation (`SELECT create_graph('inventory_graph')`)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Start InventoryView with Zero Configuration (Priority: P1) MVP

**Goal**: Single container starts with zero config, health endpoint responds, setup screen for admin password creation, data persists across restarts.

**Independent Test**: Run the container image, verify health endpoint at `/api/v1/health` returns 200, navigate to web UI and see setup screen, create admin password, restart container and verify data persists.

### Implementation for User Story 1

- [x] T014 [US1] Create Administrator pydantic model in `backend/src/inventoryview/models/admin.py` with fields from data-model.md (id, username, password_hash, created_at, updated_at, setup_complete)
- [x] T015 [P] [US1] Create auth/setup request/response schemas in `backend/src/inventoryview/schemas/auth.py`: SetupStatusResponse, SetupInitRequest (password min 12 chars), SetupInitResponse, LoginRequest, LoginResponse, TokenRevokeRequest per api-v1.md contract
- [x] T016 [US1] Implement health check endpoint `GET /api/v1/health` in `backend/src/inventoryview/api/v1/health.py` returning status, version, database connectivity, timestamp per contract. No auth required (FR-017)
- [x] T017 [US1] Implement setup endpoints in `backend/src/inventoryview/api/v1/setup.py`: `GET /api/v1/setup/status` (returns setup_complete bool) and `POST /api/v1/setup/init` (creates admin with Argon2id-hashed password, returns 409 if already set up) per contract. No auth required
- [x] T018 [US1] Add startup validation in `backend/src/inventoryview/main.py` lifespan: refuse to start if IV_VAULT_PASSPHRASE not set (clear error message), detect missing AGE extension on connected PostgreSQL (FR-019) and report clear error
- [x] T019 [US1] Create Dockerfile at `backend/Dockerfile` based on `postgres:16-bookworm` with: AGE compiled from source, s6-overlay for process supervision, Python 3.12 + app dependencies installed, s6 service definitions for postgresql and inventoryview (uvicorn)
- [x] T020 [US1] Create `docker/docker-compose.yml` for development stack with backend service (hot-reload via uvicorn --reload), PostgreSQL 16 + AGE service, volume for PG data, environment variables
- [x] T021 [US1] Create `docker/entrypoint.sh` for container startup: init PG data directory if empty, create database and user, run Alembic migrations, derive vault key from passphrase
- [x] T022 [P] [US1] Create `frontend/src/pages/SetupPage.tsx` - initial admin password creation form (password input, confirm, submit to POST /api/v1/setup/init)
- [x] T023 [P] [US1] Create `frontend/src/pages/LandingPage.tsx` - system status landing page showing system is running, link to API docs
- [x] T024 [P] [US1] Create `frontend/src/main.tsx` with router: show SetupPage if setup_complete is false, otherwise LandingPage

**Checkpoint**: User Story 1 complete - system starts, health check works, admin can set password via UI, data persists

---

## Phase 4: User Story 2 - Authenticate and Manage API Access (Priority: P2)

**Goal**: Admin logs in with credentials, receives JWT bearer token, can use token for API access, can revoke tokens. Unauthenticated requests rejected with 401.

**Independent Test**: POST valid credentials to `/api/v1/auth/login`, receive token, use token to access protected endpoint (200), try without token (401), revoke token, try revoked token (401).

### Implementation for User Story 2

- [x] T025 [US2] Create JWT token model in `backend/src/inventoryview/models/auth.py` with fields for RevokedToken (jti, revoked_at, expires_at) per data-model.md
- [x] T026 [US2] Implement JWT auth service in `backend/src/inventoryview/services/auth.py`: create_token (HS256, sub/iat/exp/jti claims, configurable expiry from IV_TOKEN_EXPIRY_HOURS), decode_token (validate signature, check expiry), check_revoked (query revoked_tokens table), revoke_token (insert jti into revoked_tokens) per research.md
- [x] T027 [US2] Implement bearer token authentication middleware in `backend/src/inventoryview/middleware/auth.py` as FastAPI dependency: extract Bearer token from Authorization header, decode and validate JWT, check revocation, return 401 with descriptive message for missing/invalid/expired/revoked tokens (FR-005)
- [x] T028 [US2] Implement login endpoint `POST /api/v1/auth/login` in `backend/src/inventoryview/api/v1/auth.py`: validate credentials against admin password_hash (Argon2id verify), return JWT token with expiry per contract. Return 401 for invalid credentials
- [x] T029 [US2] Implement token revocation endpoint `POST /api/v1/auth/revoke` in `backend/src/inventoryview/api/v1/auth.py`: decode provided token, insert jti into revoked_tokens table, return success per contract. Auth required (FR-006)
- [x] T030 [US2] Wire auth dependency into all protected routes in `backend/src/inventoryview/api/v1/router.py`: resources, relationships, credentials endpoints require auth; health, setup, docs do not

**Checkpoint**: User Story 2 complete - full auth flow works, protected endpoints reject unauthenticated requests

---

## Phase 5: User Story 3 - Store and Manage Infrastructure Credentials (Priority: P3)

**Goal**: Admin stores encrypted credentials (AES-256-GCM), lists metadata (never secrets), updates credentials, deletes them, tests connectivity. All access audited.

**Independent Test**: POST a credential, verify response contains metadata but never secret, GET list shows metadata only, PATCH updates metadata/secret, DELETE removes it (404 on subsequent GET), verify audit log entries.

### Implementation for User Story 3

- [x] T031 [US3] Implement vault service in `backend/src/inventoryview/services/vault.py`: Argon2id key derivation from passphrase + salt (hash_secret_raw, 32-byte key), AES-256-GCM encrypt/decrypt using cryptography AESGCM, VaultKeyHolder class that holds derived key in memory only per research.md
- [x] T032 [US3] Create Alembic migration for credentials table and credential_audit_log table in `backend/alembic/versions/` per data-model.md (including CHECK constraint on credential_type for supported types)
- [x] T033 [US3] Create credential model in `backend/src/inventoryview/models/credential.py` with fields from data-model.md (id, name, credential_type, encrypted_secret, nonce, auth_tag, metadata, associated_collector, timestamps)
- [x] T034 [P] [US3] Create credential request/response schemas in `backend/src/inventoryview/schemas/credentials.py`: CredentialCreateRequest (name, credential_type with enum validation, secret dict, metadata), CredentialResponse (never includes secret), CredentialUpdateRequest (partial), CredentialTestResponse per api-v1.md contract
- [x] T035 [US3] Implement credential service in `backend/src/inventoryview/services/credentials.py`: create (encrypt secret via vault, store), list (paginated, metadata only), get (metadata only), update (re-encrypt if secret changed), delete (permanent removal), test (decrypt and attempt connection) with audit logging for all operations (FR-011)
- [x] T036 [US3] Implement credential CRUD endpoints in `backend/src/inventoryview/api/v1/credentials.py`: POST /credentials, GET /credentials (paginated, filterable by credential_type), GET /credentials/{id}, PATCH /credentials/{id}, DELETE /credentials/{id} per contract. Ensure secret values NEVER in responses (FR-008)
- [x] T037 [US3] Implement credential test endpoint `POST /api/v1/credentials/{id}/test` in `backend/src/inventoryview/api/v1/credentials.py`: decrypt credential, attempt connection based on type, return success/failure per contract (FR-010)
- [x] T038 [US3] Add secret value filtering: audit all response serialization paths to ensure encrypted_secret/nonce/auth_tag never leak; configure logging to exclude secret fields (FR-009); add credential audit log writes for create/read/update/delete/use operations

**Checkpoint**: User Story 3 complete - credentials stored encrypted, metadata-only API, audit trail, connection testing

---

## Phase 6: User Story 4 - Browse Resources via the REST API (Priority: P4)

**Goal**: Resources created via API, listed with cursor-based pagination, filtered by vendor/category/region/state, individual detail with raw properties, descriptive 400 errors for invalid filters.

**Independent Test**: POST multiple resources with different vendors/categories, GET list with no filters (paginated), GET with vendor filter (subset returned), GET individual resource (full detail + raw_properties), GET with invalid filter (400 with descriptive message).

### Implementation for User Story 4

- [x] T039 [US4] Create resource node model in `backend/src/inventoryview/models/resource.py` with all properties from data-model.md (uid, name, vendor_id, vendor, vendor_type, normalised_type, category, region, state, classification fields, timestamps, raw_properties)
- [x] T040 [P] [US4] Create resource request/response schemas in `backend/src/inventoryview/schemas/resources.py`: ResourceCreateRequest, ResourceResponse, ResourceDetailResponse (includes raw_properties), ResourceUpdateRequest (partial) per api-v1.md contract
- [x] T041 [US4] Implement graph service with AGE Cypher helpers in `backend/src/inventoryview/services/graph.py`: execute_cypher (wraps ag_catalog.cypher call), parse_agtype (parse AGE return values into Python objects per research.md), create_node, update_node, delete_node, query_nodes with filter/pagination support
- [x] T042 [US4] Implement resource service in `backend/src/inventoryview/services/resources.py`: create_or_upsert (MERGE on vendor_id+vendor composite key per data-model.md, FR-021), list (with filter params + cursor pagination), get_by_uid, update, delete (remove node + all edges)
- [x] T043 [US4] Implement resource CRUD endpoints in `backend/src/inventoryview/api/v1/resources.py`: POST /resources (201 create, 200 upsert), GET /resources (paginated list with vendor/category/region/state filters), GET /resources/{uid}, PATCH /resources/{uid}, DELETE /resources/{uid} per contract
- [x] T044 [US4] Implement query parameter filter validation in `backend/src/inventoryview/api/v1/resources.py`: validate filter values, return descriptive 400 errors for invalid parameters (FR-014) - never silently ignore invalid input

**Checkpoint**: User Story 4 complete - resource CRUD, filtered listing, pagination, descriptive errors

---

## Phase 7: User Story 5 - Store Resources as a Graph (Priority: P5)

**Goal**: Resources stored as graph nodes with dual labels (Resource + category), relationships as directed edges with metadata, graph traversal at configurable depth returns subgraph.

**Independent Test**: Create two resources via API, create a relationship between them, query graph endpoint at depth 1 (returns both nodes + edge), query at depth 2 (returns extended subgraph), verify multi-label nodes.

### Implementation for User Story 5

- [x] T045 [US5] Create relationship edge model in `backend/src/inventoryview/models/relationship.py` with all properties from data-model.md (type, source_collector, confidence, established_at, last_confirmed, inference_method, metadata) and supported edge type enum
- [x] T046 [P] [US5] Create relationship request/response schemas in `backend/src/inventoryview/schemas/relationships.py`: RelationshipCreateRequest, RelationshipResponse, RelationshipDeleteRequest, SubgraphResponse (nodes + edges) per api-v1.md contract
- [x] T047 [US5] Implement relationship service in `backend/src/inventoryview/services/relationships.py`: create_relationship (verify both resource UIDs exist, create directed edge with properties), delete_relationship, list_for_resource (with direction and type filters, paginated)
- [x] T048 [US5] Implement graph traversal in `backend/src/inventoryview/services/graph.py`: get_subgraph(uid, depth) using variable-length Cypher path query `MATCH path = (n)-[*1..depth]-(m)`, respect max_traversal_depth from SystemSetting (FR-015, default 5)
- [x] T049 [US5] Implement relationship endpoints in `backend/src/inventoryview/api/v1/relationships.py`: POST /relationships (create directed edge, 404 if source/target not found), DELETE /relationships (remove edge by source+target+type) per contract
- [x] T050 [US5] Implement graph query endpoints in `backend/src/inventoryview/api/v1/resources.py`: GET /resources/{uid}/relationships (paginated, filterable by direction and type) and GET /resources/{uid}/graph (subgraph at specified depth, default 1, max from system setting) per contract
- [x] T051 [US5] Add SystemSetting read/write for max_traversal_depth in `backend/src/inventoryview/services/graph.py` with default value of 5 and validation that requested depth does not exceed setting

**Checkpoint**: User Story 5 complete - graph-native storage, relationship CRUD, traversal queries

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, hardening, and validation across all stories

- [x] T052 [P] Validate auto-generated OpenAPI docs at /docs and /redoc are complete and accurate (FR-020)
- [x] T053 [P] Add structured logging configuration in `backend/src/inventoryview/main.py`: JSON format, ensure credential secrets are never logged (FR-009), log credential access operations (FR-011)
- [x] T054 Edge case: handle DB init failure on startup (disk full, permissions) - report clear error and exit cleanly per spec edge cases
- [x] T055 Edge case: handle external DATABASE_URL without AGE extension - detect and report clear error on startup (FR-019)
- [x] T056 Edge case: handle concurrent resource upserts with same (vendor_id, vendor) via Cypher MERGE atomic semantics (FR-021)
- [x] T057 Edge case: reject unsupported credential types with 400 listing supported types per spec edge cases
- [x] T058 Edge case: ensure bearer tokens remain valid across system restarts (DB-backed revocation, no in-memory-only state) per spec edge cases
- [x] T059 Run quickstart.md validation: verify all commands in quickstart.md execute successfully end-to-end
- [x] T060 Verify 50 concurrent API request handling without degradation (SC-008) - basic load test

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start immediately after Phase 2
  - US2 (Phase 4): Can start after Phase 2. US1 creates the admin account that US2 authenticates against, but US2 can be developed independently using test fixtures
  - US3 (Phase 5): Depends on US2 (auth required for all credential endpoints)
  - US4 (Phase 6): Depends on US2 (auth required). Independent of US3
  - US5 (Phase 7): Depends on US4 (needs resource CRUD to create nodes before relationships)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```text
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ▼
Phase 3 (US1: Zero Config) ──────────────────────┐
    │                                              │
    ▼                                              │
Phase 4 (US2: Authentication)                      │
    │                                              │
    ├──────────────────┐                           │
    ▼                  ▼                           │
Phase 5 (US3)    Phase 6 (US4)  ◄── can parallel  │
                       │                           │
                       ▼                           │
                 Phase 7 (US5)                     │
                       │                           │
                       ▼                           │
                 Phase 8 (Polish) ◄────────────────┘
```

### Within Each User Story

- Models before services
- Services before endpoints
- Schemas can be parallel with models (different files)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1**: T003, T004, T005 can run in parallel after T001+T002
**Phase 2**: T008, T009 can run in parallel; T006 parallel with T008/T009 but T010 depends on all
**Phase 3**: T022, T023, T024 (frontend) parallel with T14-T18 (backend)
**Phase 5**: T034 (schemas) parallel with T031-T033
**Phase 6**: T040 (schemas) parallel with T039 (model)
**Phase 7**: T046 (schemas) parallel with T045 (model)
**Phase 8**: T052, T053 parallel; T054-T058 can be parallel (different edge cases)

---

## Parallel Example: User Story 1

```bash
# After T013 (migration) completes, launch in parallel:
Task: "T014 [US1] Create Administrator model in backend/src/inventoryview/models/admin.py"
Task: "T015 [US1] Create auth/setup schemas in backend/src/inventoryview/schemas/auth.py"

# After backend setup tasks, frontend tasks are fully parallel:
Task: "T022 [US1] Create SetupPage.tsx in frontend/src/pages/SetupPage.tsx"
Task: "T023 [US1] Create LandingPage.tsx in frontend/src/pages/LandingPage.tsx"
Task: "T024 [US1] Create main.tsx router in frontend/src/main.tsx"
```

## Parallel Example: User Story 3 + 4

```bash
# After US2 complete, US3 and US4 can start in parallel:
# Developer A works on US3 (credentials):
Task: "T031 [US3] Implement vault service in backend/src/inventoryview/services/vault.py"

# Developer B works on US4 (resources) simultaneously:
Task: "T041 [US4] Implement graph service in backend/src/inventoryview/services/graph.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run container, verify health check, create admin password via UI
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational -> Foundation ready
2. Add US1 -> Test: container starts, health works, setup screen -> **MVP!**
3. Add US2 -> Test: login, get token, auth works, 401 on unauthed
4. Add US3 -> Test: store/list/update/delete credentials, secrets never exposed
5. Add US4 -> Test: create/list/filter/paginate resources
6. Add US5 -> Test: create relationships, traverse graph at depth
7. Polish -> Edge cases, load test, docs validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Zero Config) -> US2 (Auth)
   - Developer B: Can start US3/US4 schemas and models in parallel
3. After US2 merges:
   - Developer A: US5 (Graph)
   - Developer B: US3 (Credentials) and US4 (Resources) in parallel
4. Polish phase: all developers

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Total tasks: 60 (Setup: 5, Foundational: 8, US1: 11, US2: 6, US3: 8, US4: 6, US5: 7, Polish: 9)
