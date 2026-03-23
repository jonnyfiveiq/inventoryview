# Research: AAP Automation Correlation

**Feature**: 006-aap-automation-correlation
**Date**: 2026-03-22

## R1: Metrics Utility Archive Format & CSV Parsing Strategy

**Decision**: Use Python stdlib `zipfile`/`tarfile` for archive extraction, `csv.DictReader` for parsing. Strip 2-line metadata headers by skipping the first 2 lines of each CSV before handing to DictReader.

**Rationale**: The metrics-utility export produces archives with a `data/YYYY/MM/DD/` directory hierarchy. Each CSV has a 2-line metadata header (line 1: collection timestamp, line 2: AAP version info), followed by the actual CSV header row and data. Python stdlib handles both ZIP and tar.gz natively with no extra dependencies. `csv.DictReader` provides named column access which maps cleanly to Pydantic models.

**Alternatives considered**:
- pandas `read_csv`: Heavier dependency, overkill for simple row-by-row parsing. Would add ~30MB to container image.
- polars: Fast but adds complexity for a straightforward CSV pipeline. No async benefit.
- Manual line splitting: Fragile with quoted fields containing commas.

**Key CSV types**:
| CSV filename pattern | Key columns | Purpose |
|---------------------|-------------|---------|
| `main_host_*` | host_id, hostname, canonical_facts (JSON), inventory_id, org_id | Host inventory with SMBIOS UUIDs |
| `job_host_summary_*` | host_id, job_id, job_name, ok, changed, failures, dark, skipped, created, modified | Per-job execution results |
| `main_jobevent_*` | host_id, job_id, event, event_data, created | Task-level events (for event count only) |
| `main_indirectmanagednodeaudit_*` | hostname, managed_type, unique_identifier, job_id, org_id | Cloud/API targets (VMware moid, Azure resource ID) |

## R2: Graph Modelling — AAPHost Nodes & AUTOMATED_BY Edges

**Decision**: Create `AAPHost` as a new graph node label in Apache AGE. Create `AUTOMATED_BY` as a new edge type from `AAPHost` to `Resource`. Job executions, pending matches, and learned mappings remain in relational tables.

**Rationale**: Constitution Principle I (Graph-First) requires relationships in the graph. AAP hosts are external entities that relate to inventory resources — they belong in the graph as nodes. However, job execution history is high-volume administrative data (thousands of rows per host) better suited to relational tables with pagination. This hybrid approach satisfies Graph-First for relationships while keeping operational data queryable via SQL.

**AAPHost node properties**:
- `host_id` (string, unique): AAP host identifier
- `hostname` (string): Display name
- `canonical_facts` (string, JSON): Raw canonical_facts from CSV
- `smbios_uuid` (string, nullable): Extracted from canonical_facts
- `org_id` (string): AAP organisation
- `inventory_id` (string): AAP inventory
- `first_seen` (string, ISO): First automation date
- `last_seen` (string, ISO): Last automation date
- `total_jobs` (int): Aggregated job count
- `correlation_type` (string): "direct" or "indirect"

**AUTOMATED_BY edge properties**:
- `confidence` (float, 0-1): Match confidence normalised to 0-1
- `correlation_key` (string): e.g., "smbios:abc-123" or "hostname:webserver01"
- `correlation_type` (string): "direct" or "indirect"
- `inference_method` (string): Matching strategy that produced the link
- `established_at` (string, ISO): When correlation was created
- `last_confirmed` (string, ISO): When last re-validated
- `source_collector` (string): "aap_metrics_import"

**Alternatives considered**:
- Pure relational: Violates Principle I. Graph visualisation (US6) would require application-level joins.
- Pure graph (jobs as nodes too): Excessive graph bloat. 10k hosts × 10 jobs = 100k job nodes. Graph queries would degrade.

## R3: 6-Tier Cascading Matching Strategy

**Decision**: Implement matching as an ordered pipeline of strategy functions. Each tier returns a list of `(resource_uid, score, reason)` tuples. First match above threshold 80 wins. Below-threshold matches become pending.

**Rationale**: The existing `asset_correlation.py` already demonstrates hardware ID matching via `raw_properties`. We extend this pattern with additional tiers. The cascade ensures the most reliable match type is tried first, falling through to fuzzier strategies only when needed.

**Matching tiers**:

| Tier | Strategy | Score range | Auto-match? |
|------|----------|-------------|-------------|
| 1 | Learned mapping (prior admin approval) | 100 | Yes |
| 2 | SMBIOS UUID / machine_id match | 92-98 | Yes |
| 3 | Exact hostname or FQDN match | 95 | Yes |
| 4 | IP address match | 85-90 | Yes |
| 5 | Hostname prefix / FQDN short name | 60-70 | No (review) |
| 6 | Partial / fuzzy hostname | 25-40 | No (review) |

**Integration with existing `asset_correlation.py`**: The existing service matches resources to each other via hardware IDs in `raw_properties`. The new `aap_correlation.py` matches AAP hosts to resources. These are complementary — `asset_correlation.py` creates `SAME_ASSET` edges between resources; `aap_correlation.py` creates `AUTOMATED_BY` edges from `AAPHost` to `Resource`. The existing `_extract_hw_ids()` function can be reused for Tier 2 matching.

**Deduplication approach**: Before creating `AUTOMATED_BY` edges, group AAP hosts by their resolved `smbios_uuid`. All hosts in the same group point to the same `Resource` node. Coverage counts query distinct `Resource` nodes with at least one `AUTOMATED_BY` incoming edge.

**Alternatives considered**:
- Single-pass matching: Simpler but misses lower-confidence matches that could still be valid.
- ML-based matching: Overkill for structured identifiers. Rule-based cascade is deterministic and explainable.

## R4: Relational Schema for AAP Data

**Decision**: 4 new relational tables: `aap_host`, `aap_job_execution`, `aap_pending_match`, `aap_learned_mapping`. Single Alembic migration `005_aap_automation.py`.

**Rationale**: Job executions need efficient pagination and filtering (by date, status, resource). Pending matches need state management (pending/approved/rejected). Learned mappings need fast lookup by hostname. All are operational concerns better served by indexed relational tables than graph properties.

**Alternatives considered**:
- Store in graph properties: Graph nodes with hundreds of JSON properties degrade query performance. Pagination is not natural in Cypher.
- Separate database: Violates Zero-Friction Deployment (Principle VIII). Same PostgreSQL instance is correct.

## R5: Frontend Upload & Review UX

**Decision**: File upload via drag-and-drop zone on a dedicated "Automations" page accessible from the sidebar. Review queue as a paginated table with bulk action toolbar. Coverage dashboard as a new analytics sub-page with donut charts reusing existing `DonutChart` component.

**Rationale**: The existing UI patterns (sidebar navigation, paginated tables, donut charts) provide consistency. The upload page follows the same layout as other management pages. Bulk actions (select-all, filter-by-score, approve/reject selected) enable efficient processing of large review queues.

**Alternatives considered**:
- Modal upload: Too constrained for showing import progress and results. Dedicated page is better.
- Inline review on resource pages: Loses the centralised view of all pending matches. Dedicated review page is essential for admin workflow.

## R6: AUTOMATED_BY Edge Type Registration

**Decision**: Add `AUTOMATED_BY` and `AUTOMATING` (inverse) to the existing `EdgeType` enum in `models/relationship.py`. This follows the established pattern where all edge types are registered centrally.

**Rationale**: The existing `EdgeType` enum (15 types including `SAME_ASSET`) is the authoritative list. Adding `AUTOMATED_BY` maintains consistency. The inverse `AUTOMATING` supports bidirectional graph traversal per Principle VI.

**Alternatives considered**:
- Separate edge type registry: Fragments the edge vocabulary. Centralised enum is simpler.
