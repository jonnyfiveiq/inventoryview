# Feature Specification: Foundation Core API

**Feature Branch**: `001-foundation-core-api`
**Created**: 2026-03-20
**Status**: Draft
**Input**: M1 Foundation: Core API skeleton with graph database, REST API, authentication, credential vault, and single-container deployment

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start InventoryView with Zero Configuration (Priority: P1)

An infrastructure engineer wants to evaluate InventoryView. They pull and run
a single container image with no prior setup, no configuration files, and no
external dependencies. The system starts up, initialises its own database,
and presents a working web UI and API on the default port. They can
immediately log in and begin exploring.

**Why this priority**: This is the entry point for every user. If the first-run
experience is not frictionless, adoption fails. Everything else depends on a
running system.

**Independent Test**: Can be fully tested by running the container image and
verifying the web UI loads and the API responds to health checks.

**Acceptance Scenarios**:

1. **Given** a machine with Docker installed and no prior InventoryView state,
   **When** the user runs the container image with default settings,
   **Then** the system starts within 60 seconds, the web UI is accessible on
   port 8080, and the API health endpoint returns a successful response.

2. **Given** the system is running for the first time,
   **When** the user navigates to the web UI,
   **Then** they are presented with an initial setup screen to create their
   administrator password.

3. **Given** the system has been stopped and restarted,
   **When** the user accesses the system again,
   **Then** all previously stored data (resources, credentials, settings)
   persists across restarts.

---

### User Story 2 - Authenticate and Manage API Access (Priority: P2)

An administrator logs into InventoryView with their credentials and receives
an API token they can use for programmatic access. They can also revoke
tokens and see when tokens were last used.

**Why this priority**: Authentication is a prerequisite for all other API
operations. Without it, the system is either open (unacceptable for credential
management) or inaccessible.

**Independent Test**: Can be fully tested by logging in via the API, receiving
a token, making an authenticated request, and verifying that unauthenticated
requests are rejected.

**Acceptance Scenarios**:

1. **Given** the administrator has set their password during initial setup,
   **When** they submit valid credentials to the login endpoint,
   **Then** they receive a bearer token that can be used for subsequent API
   requests.

2. **Given** an unauthenticated request is made to a protected API endpoint,
   **When** the request is processed,
   **Then** the system returns a 401 Unauthorized response with a descriptive
   error message.

3. **Given** a valid bearer token,
   **When** the token's configured expiry time passes,
   **Then** requests using that token are rejected with a 401 response
   indicating token expiry.

4. **Given** an authenticated administrator,
   **When** they request token revocation,
   **Then** the revoked token immediately stops working for subsequent
   requests.

---

### User Story 3 - Store and Manage Infrastructure Credentials (Priority: P3)

An administrator stores credentials for their infrastructure sources (cloud
provider keys, vSphere passwords, service tokens) in InventoryView's built-in
encrypted vault. They can list stored credentials (seeing only metadata, never
secret values), update them, delete them, and test whether a credential is
still valid against its target.

**Why this priority**: Collectors cannot run without credentials. The
credential vault is a prerequisite for all collection functionality in future
milestones.

**Independent Test**: Can be fully tested by storing a credential, verifying
it appears in the listing with metadata only, confirming the secret value is
never returned, and deleting it.

**Acceptance Scenarios**:

1. **Given** an authenticated administrator,
   **When** they store a new credential (e.g., an AWS key pair) via the API,
   **Then** the system accepts the credential, encrypts the secret value, and
   returns a credential reference with metadata (ID, type, creation time)
   but never the secret value.

2. **Given** stored credentials exist,
   **When** the administrator lists credentials via the API,
   **Then** each entry shows metadata (ID, name, type, associated collector,
   last used timestamp) but never the secret value.

3. **Given** a stored credential,
   **When** the administrator triggers a connection test for that credential,
   **Then** the system attempts to validate the credential against its target
   infrastructure and returns a success/failure result with an error message
   on failure.

4. **Given** a stored credential,
   **When** the administrator deletes it,
   **Then** the encrypted secret is permanently removed from storage and
   subsequent lookups for that credential ID return a 404 response.

---

### User Story 4 - Browse Resources via the REST API (Priority: P4)

A developer or tool integrating with InventoryView queries the REST API to
list resources, retrieve individual resource details, and filter resources by
vendor, category, region, or state. The API uses cursor-based pagination and
returns descriptive errors for invalid queries.

**Why this priority**: The REST API is the primary interface for all consuming
applications and the frontend. It must be operational before any UI or
collector work begins.

**Independent Test**: Can be fully tested by creating resources via the API,
querying them with various filters and pagination cursors, and verifying
correct results and error handling.

**Acceptance Scenarios**:

1. **Given** resources exist in the system,
   **When** a client queries the resources endpoint with no filters,
   **Then** the system returns a paginated list of resources with cursor-based
   navigation links.

2. **Given** resources from multiple vendors exist,
   **When** a client queries with a vendor filter (e.g., `?vendor=aws`),
   **Then** only resources from that vendor are returned.

3. **Given** a valid resource UID,
   **When** a client requests the individual resource endpoint,
   **Then** the system returns the full resource detail including normalised
   properties and raw vendor properties.

4. **Given** an invalid filter parameter value,
   **When** a client submits the query,
   **Then** the system returns a 400 error with a descriptive message
   explaining the invalid parameter, never silently ignoring it.

---

### User Story 5 - Store Resources as a Graph (Priority: P5)

Resources ingested into InventoryView are stored as nodes in a labelled
property graph. Relationships between resources are stored as edges.
An operator can query the graph to find connected resources and traverse
relationships across boundaries.

**Why this priority**: The graph data model is foundational to InventoryView's
architecture, but it is exercised indirectly through the API layer. This story
validates that the underlying storage is graph-native.

**Independent Test**: Can be fully tested by creating resources with
relationships via the API and querying the graph endpoint to verify nodes,
edges, and traversal results.

**Acceptance Scenarios**:

1. **Given** a resource is created in the system,
   **When** the resource is stored,
   **Then** it exists as a node in the graph with the Resource base label plus
   its category label (e.g., Resource:Compute).

2. **Given** two resources exist,
   **When** a relationship is created between them (e.g., HOSTED_ON),
   **Then** the relationship is stored as a directed edge in the graph with
   the specified type and metadata properties.

3. **Given** a resource with relationships,
   **When** a client queries the resource's graph endpoint with a depth of 2,
   **Then** the system returns the resource, its direct relationships, and
   the connected resources up to the specified depth.

---

### Edge Cases

- What happens when the embedded database fails to initialise on first startup
  (e.g., disk full, permissions issue)? The system MUST report a clear error
  and exit cleanly rather than running in a degraded state.
- What happens when the administrator attempts to store a credential with an
  unsupported type? The system MUST reject it with a 400 error listing
  supported credential types.
- What happens when the user provides an external DATABASE_URL that points to
  a PostgreSQL instance without the Apache AGE extension? The system MUST
  detect the missing extension on startup and report a clear error.
- What happens when two API requests attempt to create resources with the same
  vendor_id from the same vendor simultaneously? The system MUST handle the
  conflict via upsert semantics, not duplicate creation.
- What happens when the vault passphrase is not provided on startup? The
  system MUST refuse to start and display a clear message explaining that the
  passphrase is required.
- What happens when a bearer token is used after the system restarts? Tokens
  MUST remain valid across restarts if they have not expired.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST start from a single container image with zero
  mandatory configuration, initialising its own embedded database on first run.
- **FR-002**: System MUST persist all data across container restarts using a
  volume-mounted storage location.
- **FR-003**: System MUST create a single built-in administrator account
  during initial setup, with the password set interactively or via an
  environment variable.
- **FR-004**: System MUST authenticate API requests using bearer tokens (JWT)
  with configurable expiry (default: 24 hours).
- **FR-005**: System MUST reject unauthenticated requests to protected
  endpoints with a 401 response and descriptive error message.
- **FR-006**: System MUST support token revocation, immediately invalidating
  revoked tokens.
- **FR-007**: System MUST store infrastructure credentials in an encrypted
  vault using AES-256-GCM encryption with a master key derived from a
  user-provided passphrase via Argon2id.
- **FR-008**: System MUST NOT return credential secret values in any API
  response. Only metadata (ID, name, type, associated collector, timestamps)
  is returned.
- **FR-009**: System MUST NOT log credential secret values under any
  circumstances.
- **FR-010**: System MUST support credential testing -- validating that a
  stored credential can connect to its target infrastructure without running a
  full collection.
- **FR-011**: System MUST log all credential access operations (create, read,
  update, delete, use) with timestamp and actor, excluding the secret value.
- **FR-012**: System MUST store all infrastructure resources as nodes in a
  labelled property graph, with each node carrying the Resource base label
  plus one or more category labels.
- **FR-013**: System MUST store all relationships between resources as
  directed edges in the graph with type, metadata, and confidence properties.
- **FR-014**: System MUST expose a REST API with cursor-based pagination on
  all list endpoints, explicit query parameter filtering with validation, and
  descriptive 400 errors for invalid inputs (never silently ignored).
- **FR-015**: System MUST expose resource endpoints: list, create, retrieve,
  update, delete individual resources; list relationships for a resource;
  return the subgraph around a resource at a specified depth. Graph traversal
  depth MUST default to a maximum of 5. This limit MUST be configurable via
  a system-level setting to allow operators to increase it for environments
  with deeper relationship chains.
- **FR-016**: System MUST expose credential endpoints: create, list, update,
  delete credentials; test a stored credential. Update supports changing both
  secret values and metadata without breaking collector associations.
- **FR-017**: System MUST expose a health check endpoint that does not require
  authentication.
- **FR-018**: System MUST allow connection to an external PostgreSQL instance
  (with Apache AGE) via a DATABASE_URL environment variable, bypassing the
  embedded database.
- **FR-019**: System MUST detect and report clearly on startup if the
  connected PostgreSQL instance is missing the Apache AGE extension.
- **FR-020**: System MUST generate auto-generated API documentation accessible
  via the running application.
- **FR-021**: System MUST handle concurrent resource upserts using upsert
  semantics with the composite key `(vendor_id, vendor)`, preventing duplicate
  node creation. The same vendor_id from different vendors creates separate
  resource nodes.

### Key Entities

- **Administrator**: The single built-in user account that has full access to
  all system capabilities. Identified by username, authenticated by password,
  associated with JWT tokens.
- **Resource**: A discovered infrastructure item stored as a graph node.
  Carries normalised properties (uid, name, normalised_type, vendor_type,
  category, vendor, region, state), classification metadata
  (classification_confidence, classification_method), lifecycle timestamps
  (first_seen, last_seen), and raw vendor-specific properties.
- **Relationship**: A directed connection between two resources stored as a
  graph edge. Carries a type (DEPENDS_ON, HOSTED_ON, MEMBER_OF, etc.),
  source_collector, confidence score, establishment and confirmation
  timestamps, and inference method.
- **Credential**: An encrypted secret used by collectors to access
  infrastructure sources. Stored in the vault with metadata (ID, name, type,
  associated collector, timestamps) separate from the encrypted secret value.
  Supported types include: AWS Key Pair, Azure Service Principal, GCP Service
  Account, vSphere Credentials, OpenShift/Kubernetes, Bearer Token,
  Username/Password, SSH Key.
- **Bearer Token (JWT)**: An authentication token issued to the administrator
  on login. Has a configurable expiry and can be revoked. Used for all
  authenticated API requests.

## Clarifications

### Session 2026-03-21

- Q: Should credential update (PATCH) be in scope for FR-016? US3 mentions "update" but FR-016 only listed create/list/delete. → A: Yes, add full credential update (secret values and metadata) to FR-016.
- Q: Is resource uniqueness scoped to vendor_id alone or the composite (vendor_id, vendor)? → A: Composite key (vendor_id, vendor). Same ID from different vendors creates separate nodes.
- Q: Should graph traversal depth have a maximum limit? → A: Default max depth of 5 for performance, configurable via a system-level override setting.

## Assumptions

- The MVP targets a single administrator user. Multi-user and enterprise
  authentication (OIDC, SAML, LDAP, RBAC) are explicitly out of scope and
  planned for future milestones.
- The embedded PostgreSQL with Apache AGE is bundled inside the container
  image. The data directory is volume-mounted for persistence.
- The vault passphrase is provided via the VAULT_PASSPHRASE environment
  variable or an interactive prompt on first startup. The derived master key
  is held in memory only and never written to disk.
- Collectors are out of scope for this milestone. The resource and
  relationship API endpoints exist for creating and querying graph data, but
  no automated discovery occurs yet.
- The web UI for this milestone is limited to the initial setup screen
  (password creation) and a minimal landing page confirming the system is
  running. The full Netflix-style UI is a separate milestone (M7).
- Scoring, taxonomy normalisation, and drift detection are out of scope for
  this milestone. Resources are stored as-is; scoring comes in M3/M4.
- Resource List functionality is out of scope for this milestone (M9).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with Docker installed can go from zero to a running,
  accessible InventoryView instance in under 2 minutes with a single command.
- **SC-002**: The system starts and becomes fully operational (API responding,
  UI accessible) within 60 seconds of container launch.
- **SC-003**: All data persists across container stop/start cycles with zero
  data loss.
- **SC-004**: Unauthenticated requests to protected endpoints are rejected
  100% of the time with appropriate error responses.
- **SC-005**: Credential secret values are never exposed in any API response,
  log output, or error message -- verifiable by automated audit of all API
  responses and log files.
- **SC-006**: Invalid API query parameters produce descriptive 400 errors in
  100% of cases, with zero instances of silently ignored invalid input.
- **SC-007**: Resources and relationships stored via the API are queryable as
  a graph with traversal returning correct results at depths of 1, 2, and 3
  hops.
- **SC-008**: The system handles at least 50 concurrent API requests without
  degradation or errors.
