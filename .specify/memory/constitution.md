<!--
Sync Impact Report
==================
Version change: N/A (initial) -> 1.0.0
Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (8 principles derived from SRS section 3.1)
  - Technology Stack Constraints (derived from SRS sections 15, 13)
  - Development Workflow (derived from SRS sections 13.3, 10.3, 16)
  - Governance
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ no updates needed (Constitution Check
    section is dynamically filled)
  - .specify/templates/spec-template.md: ✅ no updates needed (structure-agnostic)
  - .specify/templates/tasks-template.md: ✅ no updates needed (phase structure
    compatible)
Follow-up TODOs: None
-->

# InventoryView Constitution

## Core Principles

### I. Graph-First

All data MUST be modelled as nodes and edges in the labelled property graph
(Apache AGE). The graph is the source of truth, not a derived view.

- Resources are nodes; relationships are edges. No relational surrogate tables
  for data that belongs in the graph.
- Every query that involves relationships MUST use Cypher traversal, not
  application-level joins.
- Metadata and administrative data (credentials, user accounts, configuration)
  MAY use standard PostgreSQL tables alongside the graph.

**Rationale**: The previous inventory-service used flat relational tables that
could not efficiently express cross-boundary relationships. The graph model
eliminates this limitation.

### II. Normalised Taxonomy

Every discovered resource MUST be classified into the universal taxonomy
hierarchy (Category > Type > Subtype) regardless of vendor origin.

- A VM is a VM whether it comes from VMware, AWS, Azure, GCP, or OpenShift.
- Every resource MUST have exactly one category and one normalised type.
- The original vendor type MUST be preserved in `vendor_type` alongside the
  normalised classification.
- New normalised types proposed by the Scoring Engine MUST be flagged for
  human review before becoming permanent.
- The taxonomy MUST be versioned. Changes are tracked for historical analysis.

**Rationale**: Without normalisation, cross-vendor queries and scoring are
impossible. The taxonomy is the universal language of InventoryView.

### III. Pluggable Collectors

Collectors MUST be independently versioned, independently deployable units
that ship on their own lifecycle, separate from the core application.

- Three collection modes are supported: Python plugins, container collectors
  (gRPC), and MCP server discovery.
- All three modes MUST produce the same `ResourceData` output that enters the
  same taxonomy, scoring, and graph pipeline.
- Collectors MUST NOT share the core application's Python process in
  production (Python plugins MAY run in-process for development convenience).
- Adding a new collector MUST NOT require changes to the core application code.

**Rationale**: The previous inventory-service coupled providers to the
application process and shared its lifecycle. This made independent versioning
and deployment impossible.

### IV. Scored Intelligence

Every inventory item, relationship, and possible action MUST receive a
dynamic, multi-dimensional score. The system MUST rank what matters and
recommend what to do next.

- Scores are computed from defined signals: risk, drift, impact, confidence,
  cost, compliance, freshness, and blast radius.
- Scores MUST include an explainable breakdown showing which signals
  contributed and why.
- Scores MUST use fingerprint-based invalidation -- only recompute when inputs
  change.
- The Scoring Engine MUST use a tiered inference architecture: rules engine
  (Tier 1), local model via Ollama (Tier 2), external API via Claude (Tier 3),
  and human review (Tier 4).

**Rationale**: Traditional inventory systems answer "what exists?" InventoryView
answers "what matters, and what should I do about it?" Scoring is the core
differentiator.

### V. Adaptive Learning

Scores MUST update continuously based on execution outcomes, graph changes,
and human corrections. The system MUST get smarter the more it is used.

- Execution outcomes feed back: successful actions increase confidence for
  similar future scenarios; failures decrease it.
- Human corrections MUST train the rules engine and local model.
- Temporal decay MUST reduce confidence for stale data (applied lazily at
  query time).
- Pattern learning MUST track which action sequences work in practice and
  suggest multi-step plans.

**Rationale**: Static scores lose value over time. A feedback loop creates a
virtuous cycle where the system's recommendations improve with use.

### VI. Relationship-Centric

The primary value of InventoryView is in understanding how resources relate.
Relationships MUST be first-class citizens with their own scores and metadata.

- Edge types include: DEPENDS_ON, HOSTED_ON, MEMBER_OF, CONNECTED_TO,
  ATTACHED_TO, MANAGES, ROUTES_TO, CONTAINS, PEERS_WITH, and their
  inverses.
- All edges MUST carry: source_collector, confidence, established_at,
  last_confirmed, and inference_method.
- Cross-boundary relationships (e.g., OpenShift pod to AWS RDS to on-prem
  VMware network) MUST be expressible without artificial boundaries.
- Relationship discovery works via collector-reported hints AND LLM-inferred
  analysis.

**Rationale**: Isolated resource inventories are commodity. The graph of
relationships is where operational insight lives.

### VII. Open Boundaries

Users MUST be able to follow a relationship chain across vendor and platform
boundaries without restriction.

- The graph MUST NOT partition resources by vendor or infrastructure type.
- Queries MUST be able to traverse from any resource to any related resource
  regardless of origin.
- Resource Lists provide scoped access boundaries for consuming applications,
  but the underlying graph remains unified.

**Rationale**: Real infrastructure spans multiple vendors and platforms.
Artificial boundaries hide critical dependencies.

### VIII. Zero-Friction Deployment

A single `docker pull && docker run` MUST produce a working system. Complexity
is opt-in, not mandatory.

- The single-container image MUST include: FastAPI application, embedded
  PostgreSQL with Apache AGE, rules-based Scoring Engine, and web UI.
- Zero configuration MUST be required to start. Sensible defaults for
  everything.
- A built-in sample collector with synthetic data MUST be included so the
  system is immediately explorable.
- External services (managed PostgreSQL, Ollama, HashiCorp Vault) are opt-in
  via environment variables.
- Scale when you need to, not before. Kubernetes/OpenShift operator is
  available but never required.

**Rationale**: The previous inventory-service required a full AAP deployment.
InventoryView MUST be independently deployable with zero prerequisites.

## Technology Stack Constraints

The following technology choices are binding for all implementation work:

- **API**: Python 3.12+ with FastAPI. Async-first. Auto-generated OpenAPI docs.
- **Graph Database**: PostgreSQL 16+ with Apache AGE extension. One database
  for graph (Cypher) and relational (SQL) data.
- **Frontend**: React + TypeScript + Vite. Shadcn/UI + Tailwind CSS for
  components.
- **Graph Visualisation**: D3.js or Cytoscape.js (to be determined by spike).
- **Collector Communication**: gRPC with Protocol Buffers for container
  collectors.
- **Local LLM**: Ollama for Tier 2 scoring inference.
- **External LLM**: Claude API (Anthropic) for Tier 3 scoring inference.
- **Secrets**: Built-in AES-256-GCM encrypted vault (MVP); HashiCorp Vault
  (enterprise).
- **Observability**: OpenTelemetry + Prometheus + Grafana.
- **CI/CD**: GitHub Actions + ArgoCD.
- **Containerisation**: OCI-compliant images. Docker Compose for development.
  Kubernetes operator for production HA.

Deviations from this stack MUST be documented in a Complexity Tracking table
with justification and rejected alternatives.

## Development Workflow

- **API design**: fail loudly on invalid input (400 with descriptive messages,
  never silently ignored). Cursor-based pagination on all list endpoints.
  Explicit query parameter names with documented allowed values. `/api/v1/`
  versioned prefix.
- **Credentials**: MUST NOT be stored in the graph database, logged, or
  returned in API responses. Decrypted in memory at moment of use only.
- **Docker-first development**: `docker compose up -d` MUST launch the full
  development stack with hot-reloading.
- **Collector SDK**: MUST include a local testing harness that simulates the
  Core API so collector developers do not need a running InventoryView
  instance.
- **Makefile targets**: `make dev`, `make test`, `make lint`,
  `make build-collector NAME=<name>`.
- **Milestone delivery**: implementation follows the phased milestone plan
  (M1-M14) where each milestone builds on its dependencies.

## Governance

This constitution supersedes all other development practices for InventoryView.

- All pull requests and code reviews MUST verify compliance with the Core
  Principles.
- Amendments to this constitution MUST be documented with a version bump,
  rationale, and migration plan for any affected code.
- Version bumps follow semantic versioning: MAJOR for principle
  removals/redefinitions, MINOR for new principles or material expansions,
  PATCH for clarifications and wording fixes.
- Complexity MUST be justified. Any violation of a principle requires an entry
  in the Complexity Tracking table explaining why it is necessary and what
  simpler alternative was rejected.

**Version**: 1.0.0 | **Ratified**: 2026-03-20 | **Last Amended**: 2026-03-20
