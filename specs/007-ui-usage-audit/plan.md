# Implementation Plan: UI Usage Analytics & Audit Tracking

**Branch**: `007-ui-usage-audit` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md) | **Status**: ✅ Implemented
**Input**: Feature specification from `/specs/007-ui-usage-audit/spec.md`

## Summary

Add UI usage analytics and login audit tracking to InventoryView. The backend receives usage events from the frontend and login audit entries from the auth endpoint, stores them in PostgreSQL relational tables, and exposes aggregate statistics via new API endpoints. The frontend instruments key user interactions with a lightweight tracking hook, adds an "Administration" sidebar section with a "Usage" dashboard page, and displays feature-area breakdowns with time-range filtering. A scheduled purge removes data older than 90 days.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.4+ (frontend)
**Primary Dependencies**: FastAPI, psycopg (async), React 18, TanStack Query, Zustand, Tailwind CSS, Shadcn/UI
**Storage**: PostgreSQL 16+ (relational tables — usage events and login audit are metadata, not graph data per Constitution Principle I)
**Testing**: pytest (backend), TypeScript type-checking (frontend)
**Target Platform**: Linux server (containerised), modern web browser
**Project Type**: Web application (full-stack)
**Performance Goals**: Tracking adds <50ms perceived latency; dashboard loads in <10s; 10,000+ events/day
**Constraints**: Fire-and-forget tracking (no blocking), 90-day data retention, client-side 2s debounce
**Scale/Scope**: Single-tenant, all authenticated users tracked, single admin role

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First | PASS | Usage events and login audit are administrative metadata, not resource/relationship data. Constitution explicitly allows standard PostgreSQL tables for metadata and administrative data. |
| II. Normalised Taxonomy | N/A | No new resource types introduced. |
| III. Pluggable Collectors | N/A | No collector changes. |
| IV. Scored Intelligence | N/A | No scoring changes. |
| V. Adaptive Learning | N/A | No learning changes. |
| VI. Relationship-Centric | N/A | No new relationship types. |
| VII. Open Boundaries | N/A | No graph partitioning. |
| VIII. Zero-Friction Deployment | PASS | No new external dependencies. Tables auto-created via Alembic migration. |

All gates pass. No violations to track.

## Project Structure

### Documentation (this feature)

```text
specs/007-ui-usage-audit/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── usage-events-api.md
│   └── usage-dashboard-api.md
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 006_usage_audit.py          # New migration
├── src/inventoryview/
│   ├── api/v1/
│   │   ├── usage.py                # New: usage event ingestion + dashboard endpoints
│   │   └── auth.py                 # Modified: add login audit recording
│   ├── schemas/
│   │   └── usage.py                # New: request/response schemas
│   ├── services/
│   │   └── usage.py                # New: usage aggregation + purge logic
│   └── api/v1/router.py            # Modified: register usage router

frontend/
├── src/
│   ├── api/
│   │   └── usage.ts                # New: API client for usage endpoints
│   ├── hooks/
│   │   └── useTracking.ts          # New: tracking hook with debounce
│   ├── pages/
│   │   └── UsageDashboardPage.tsx   # New: admin usage dashboard
│   ├── components/
│   │   ├── layout/
│   │   │   └── Sidebar.tsx          # Modified: add Administration section
│   │   └── usage/
│   │       ├── FeatureAreaCard.tsx   # New: feature area summary card
│   │       ├── FeatureDetail.tsx     # New: drill-down action breakdown
│   │       ├── LoginAuditTable.tsx   # New: login activity table
│   │       └── TimeRangeFilter.tsx   # New: time range selector
│   └── router/
│       └── index.tsx                # Modified: add /admin/usage route
```

**Structure Decision**: Web application structure following existing patterns. New backend module `usage` parallel to existing `automations`, `playlists`, etc. New frontend page and components following existing patterns.

## Complexity Tracking

> No constitution violations. Table not needed.
