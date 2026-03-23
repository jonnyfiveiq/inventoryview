# Implementation Plan: AAP Automation Correlation

**Branch**: `006-aap-automation-correlation` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-aap-automation-correlation/spec.md`

## Summary

Upload AAP metrics utility archives (ZIP/tar.gz), parse 4 CSV types (hosts, job summaries, job events, indirect managed nodes), and store AAP data in relational tables. Correlate AAP hosts to inventory resources using a 6-tier cascading matching strategy (learned mappings → SMBIOS UUID → exact hostname → IP → hostname prefix → partial). Model AAP hosts as graph nodes (`AAPHost` label) with `AUTOMATED_BY` edges to `Resource` nodes. Deduplicate hostnames resolving to the same machine. Surface automation coverage on dashboards, per-resource detail pages, provider drill-downs, and graph visualisations. Support manual review with bulk actions, learned mappings, and exportable reports.

## Technical Context

**Language/Version**: Python 3.12+ (async-first) for backend; TypeScript 5.4+ for frontend
**Primary Dependencies**: FastAPI, psycopg[binary] (v3, async), Pydantic v2, python-multipart (file uploads), zipfile/tarfile (stdlib), csv (stdlib); React 18 + Vite, TanStack Query, Zustand, Cytoscape.js, Axios
**Storage**: PostgreSQL 16+ with Apache AGE extension — relational tables for AAP data (hosts, jobs, pending matches, learned mappings), graph nodes (`AAPHost`) and edges (`AUTOMATED_BY`) for correlation
**Testing**: pytest + httpx (async API tests), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browsers
**Project Type**: Web application (backend API + frontend SPA)
**Performance Goals**: Upload + parse + correlate ≤30s for 10k hosts; dashboard loads ≤2s; graph renders ≤50 automation nodes without degradation
**Constraints**: 200MB max upload; auto-match threshold 80/100; auto-correlate immediately after upload
**Scale/Scope**: Up to 10,000 AAP hosts per import; hundreds of learned mappings; 7 user stories across 3 priority tiers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First | PASS | AAP hosts modelled as `AAPHost` graph nodes with `AUTOMATED_BY` edges to `Resource` nodes. Job executions in relational tables (administrative data — permitted by constitution). |
| II. Normalised Taxonomy | PASS | `AAPHost` is a new node label, not a new resource type. Does not interfere with Category > Type > Subtype hierarchy. AAP hosts reference resources via edges, not by becoming resources themselves. |
| III. Pluggable Collectors | PASS | AAP import is a file upload, not a collector. Does not affect collector pipeline. |
| IV. Scored Intelligence | PASS | Confidence scores (0-100) assigned to every correlation. Match reason and strategy tracked for explainability. |
| V. Adaptive Learning | PASS | Learned mappings improve matching over time. Manual approvals feed back into auto-matching on subsequent imports. |
| VI. Relationship-Centric | PASS | `AUTOMATED_BY` edges carry: source_collector, confidence, established_at, last_confirmed, inference_method, correlation_type. Extends existing edge type vocabulary. |
| VII. Open Boundaries | PASS | AAP correlations work across all vendors — same matching cascade applies to VMware, AWS, Azure, OpenShift resources. No vendor partitioning. |
| VIII. Zero-Friction Deployment | PASS | Feature adds new migration + API routes to existing single-container deployment. No new external services required. |

All gates pass. No complexity tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-aap-automation-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── automation-api.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/inventoryview/
│   ├── models/
│   │   └── automation.py          # AAP host, job execution, pending match, learned mapping models
│   ├── schemas/
│   │   └── automation.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── aap_import.py          # Archive extraction, CSV parsing, data persistence
│   │   ├── aap_correlation.py     # 6-tier matching cascade, deduplication, graph node/edge creation
│   │   └── aap_reports.py         # Coverage stats, report generation, CSV export
│   └── api/v1/
│       └── automations.py         # Upload, review queue, approve/reject, coverage, reports endpoints
├── alembic/versions/
│   └── 005_aap_automation.py      # Migration: aap_host, aap_job_execution, aap_pending_match, aap_learned_mapping tables
└── tests/

frontend/
├── src/
│   ├── api/
│   │   └── types.ts               # Extended with AAP types
│   ├── hooks/
│   │   └── useAutomation.ts       # TanStack Query hooks for automation endpoints
│   ├── pages/
│   │   ├── AutomationUploadPage.tsx    # Upload interface
│   │   ├── AutomationReviewPage.tsx    # Pending match review queue with bulk actions
│   │   └── AutomationDashboardPage.tsx # Coverage dashboard
│   └── components/
│       └── automation/
│           ├── AutomationHistory.tsx   # Timeline component for resource detail page
│           ├── AutomationCoverage.tsx  # Coverage metrics widget
│           └── AutomationBadge.tsx     # Inline badge for provider drill-down
└── tests/
```

**Structure Decision**: Web application — extends existing `backend/` + `frontend/` structure with new automation-specific modules. Backend adds 1 migration, 3 services, 1 route module, 1 model file, 1 schema file. Frontend adds 3 pages, 3 components, 1 hook file, and extends existing types.

## Complexity Tracking

> No violations — all gates pass.
