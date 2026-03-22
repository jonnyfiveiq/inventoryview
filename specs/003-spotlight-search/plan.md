# Implementation Plan: Spotlight-Style Universal Search

**Branch**: `003-spotlight-search` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-spotlight-search/spec.md`

## Summary

Add a macOS Spotlight-style search overlay to InventoryView that allows users to instantly find resources across all providers. Users activate the overlay via Cmd+K / Ctrl+K or a header search icon, type a query, and see results grouped by normalised taxonomy type. Requires a backend enhancement (new `search` query parameter on `GET /resources`) and a frontend overlay component with debounced search, taxonomy grouping, and keyboard navigation.

## Technical Context

**Language/Version**: TypeScript 5.7 (frontend), Python 3.12 (backend)
**Primary Dependencies**: React 18, TanStack Query v5, Axios, lucide-react (frontend); FastAPI, psycopg3, Apache AGE/Cypher (backend)
**Storage**: PostgreSQL 16 + Apache AGE graph (existing, no schema changes)
**Testing**: Manual testing via quickstart scenarios
**Target Platform**: Web browser (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend SPA + backend API)
**Performance Goals**: Search results within 500ms of typing pause for up to 10,000 resources
**Constraints**: 300ms debounce, minimum 2 character query, case-insensitive substring matching
**Scale/Scope**: Up to 10,000 resources across multiple providers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First | PASS | Search uses Cypher `CONTAINS` on graph node properties — no SQL fallback |
| II. Normalised Taxonomy | PASS | Results grouped by `normalised_type` — reinforces the taxonomy model |
| III. Pluggable Collectors | N/A | No collector changes |
| IV. Scored Intelligence | N/A | No scoring changes |
| V. Adaptive Learning | N/A | No learning changes |
| VI. Relationship-Centric | PASS | Search finds resources; graph overlay remains available from results |
| VII. Open Boundaries | PASS | Search crosses all vendor boundaries — single query, all providers |
| VIII. Zero-Friction Deployment | PASS | No new services or dependencies; single container still works |

**Post-Phase 1 re-check**: All gates still pass. No new persistent entities, no new services, no schema migrations required.

## Project Structure

### Documentation (this feature)

```text
specs/003-spotlight-search/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── search-api.md   # API contract for search parameter
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/inventoryview/
│   ├── api/v1/resources.py        # Added search query parameter
│   └── services/
│       ├── resources.py           # Added search parameter passthrough
│       └── graph.py               # Added Cypher CONTAINS clauses
└── tests/                         # (existing)

frontend/
├── src/
│   ├── api/
│   │   └── resources.ts           # Added search parameter to ListResourcesParams
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx      # Layout route wrapper (Sidebar + SpotlightOverlay + Cmd+K)
│   │   │   └── Sidebar.tsx        # Added search icon trigger with onSearchClick prop
│   │   └── search/                # NEW directory
│   │       ├── SpotlightOverlay.tsx    # Main overlay component (portal, keyboard nav)
│   │       ├── SearchInput.tsx         # Input with auto-focus and ESC hint
│   │       ├── SearchResults.tsx       # Grouped results display + getFlatResults()
│   │       ├── TaxonomyGroup.tsx       # Single group with expand/collapse (5→10→provider page)
│   │       └── SearchResultItem.tsx    # Individual result row with highlight support
│   ├── hooks/
│   │   ├── useSearch.ts           # NEW: TanStack Query hook for search
│   │   └── useDebouncedValue.ts   # NEW: Generic debounce hook
│   ├── router/
│   │   └── index.tsx              # MODIFIED: AppLayout as layout route wrapping protected routes
│   └── utils/
│       └── taxonomyLabels.ts      # NEW: normalised_type → human label map
└── tests/                         # (existing)
```

**Structure Decision**: Web application structure (Option 2). Changes span both backend (API enhancement) and frontend (new overlay component tree). All new frontend code goes under `src/components/search/` following the existing component directory pattern. AppLayout is used as a React Router layout route (with `<Outlet />`) wrapping all authenticated pages to provide the sidebar, search overlay, and keyboard shortcuts globally.

## Complexity Tracking

No constitution violations. No entries required.
