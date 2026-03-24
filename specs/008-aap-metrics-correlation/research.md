# Research: AAP Metrics Correlation Engine

**Feature Branch**: `008-aap-metrics-correlation`
**Date**: 2026-03-23

## Decision 1: Background Job Approach

**Decision**: Use FastAPI `BackgroundTasks` for async correlation execution.

**Rationale**: The existing codebase has no task queue infrastructure (no Celery, no Redis). FastAPI's built-in `BackgroundTasks` runs in the same process and requires zero new dependencies. The correlation workload (1,000 hosts x 5,000 resources in <30s per SC-002) fits within a single-process async model. A lightweight in-memory job tracker (dict of job_id → status/progress) is sufficient for progress reporting.

**Alternatives considered**:
- **Celery + Redis**: Production-grade but violates Constitution VIII (Zero-Friction Deployment) by adding mandatory external services. Overkill for current scale.
- **APScheduler**: Better for scheduled jobs than one-off background tasks.
- **asyncio.create_task**: Too low-level — no built-in progress tracking or error isolation.

**Implementation notes**:
- Store job state in a module-level dict: `{job_id: {status, progress, total, errors, started_at, completed_at}}`
- Job state is ephemeral (lost on restart) — acceptable since correlation re-runs on next upload
- Expose `GET /api/v1/automations/correlation-jobs/{job_id}` for polling

## Decision 2: Enhance Existing Correlation vs. Rewrite

**Decision**: Enhance the existing `aap_correlation.py` service, not rewrite.

**Rationale**: The existing correlation engine already implements a 6-tier matching system with learned mappings, SMBIOS UUID, hostname, IP, FQDN, and fuzzy matching. E-01 adds:
1. Expanded fact extraction (ansible_product_serial, ansible_product_uuid, MAC addresses)
2. Explicit confidence scores (0.0-1.0 instead of integer 0-100)
3. Multi-tier reinforcement boosting
4. Audit logging (FR-014)
5. Delta correlation on collection completion

The existing structure (`correlate_hosts()`, `_try_*` helper functions) maps cleanly to the E-01 tier hierarchy. Refactor existing tiers to match E-01 naming, add new fact extraction, normalise scores to 0.0-1.0.

**Alternatives considered**:
- **Full rewrite**: Higher risk, loses learned mapping logic and battle-tested edge cases.
- **Separate engine alongside old**: Confusing dual paths, migration headache.

## Decision 3: Multi-Tier Confidence Boost Formula

**Decision**: Use additive boost with cap at the next tier's base confidence.

**Formula**: When multiple tiers match the same resource, boost = `max(individual_confidences) + 0.15 * count(additional_matches)`, capped at the next-higher tier's base confidence.

**Examples**:
- IP (0.75) + Hostname (0.30) → 0.75 + 0.15 = 0.90 (capped at Tier 2 base 0.95)
- FQDN (0.50) + IP (0.75) → 0.75 + 0.15 = 0.90
- FQDN (0.50) + Hostname (0.30) → 0.50 + 0.15 = 0.65

**Rationale**: Additive with a cap is simple, predictable, and matches the worked example in E-01 (IP 0.75 + hostname boost → 0.90). Cap prevents lower tiers from exceeding deterministic hardware matches.

## Decision 4: ansible_facts Storage

**Decision**: Store ansible_facts as a JSONB column on the existing `aap_host` relational table.

**Rationale**: ansible_facts is operational metadata used for correlation lookups, not a graph relationship. Per Constitution I, administrative/metadata data MAY use standard PostgreSQL tables. JSONB enables efficient GIN-indexed lookups on nested fact fields (serial, UUID, MAC, IP).

**Alternatives considered**:
- **Separate facts table**: Unnecessary normalisation — facts are always accessed with their host.
- **Graph node property**: AGE property values don't support efficient JSON path queries.

## Decision 5: Reconciliation Queue Implementation

**Decision**: Extend the existing `aap_pending_match` table and review endpoints.

**Rationale**: The existing system already has:
- `aap_pending_match` table with status, match_score, match_reason
- `POST /api/v1/automations/review` endpoint for approve/reject/ignore
- `AutomationReviewPage` frontend with bulk actions

E-01 additions:
- Add `tier` column to `aap_pending_match`
- Add `matched_fields` JSONB column
- Add `correlation_exclusion` table for NOT_CORRELATED rules (FR-008)
- Extend review endpoint to support "dismiss" action and exclusion persistence
- Add `correlation_audit` table for FR-014 logging

## Decision 6: Temperature Gauge UI Component

**Decision**: SVG-based vertical thermometer component with CSS transitions.

**Rationale**: A thermometer-style gauge is specified in E-01. SVG provides resolution-independent rendering and smooth colour transitions between bands. The component renders:
- Compact dot variant for list views (colour-coded circle + percentage)
- Full thermometer variant for resource detail view
- Large aggregate variant for dashboard

**Alternatives considered**:
- **CSS-only progress bar**: Doesn't match thermometer visual language from E-01.
- **Canvas**: Overkill for a static gauge, harder to style with Tailwind.
- **Third-party chart library**: Unnecessary dependency for a custom gauge.

## Decision 7: Delta Correlation on Collection Completion

**Decision**: Track collection runs via a `last_correlated_at` timestamp on resources.

**Rationale**: When a provider collection completes, it updates `last_seen` on affected resources. The delta correlation query filters for resources where `last_seen > last_correlated_at` (or `last_correlated_at IS NULL`). This avoids maintaining a separate change-tracking table and leverages the existing collection flow.

After correlation completes for a resource, update `last_correlated_at` to the current timestamp.
