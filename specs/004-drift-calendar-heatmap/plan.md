# Implementation Plan: Drift Calendar Heatmap

**Branch**: `004-drift-calendar-heatmap` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-drift-calendar-heatmap/spec.md`

## Summary

Add a GitHub-style calendar heatmap to InventoryView that visualises infrastructure drift over time. Each resource's detail page gets a 365-day calendar grid where cells are coloured by drift activity using a two-layer intensity model: (1) lifetime drift count relative to the fleet average sets the base warmth, and (2) per-day event spikes overlay for additional contrast. Discovery day appears in a cool colour (blue/green), drift days progress from yellow through orange to red. The fleet-wide aggregate calendar appears on both the landing page and analytics page. Clicking a day cell opens the existing drift modal filtered to that day. Requires a new backend aggregation endpoint and a new frontend calendar component.

## Technical Context

**Language/Version**: TypeScript 5.7 (frontend), Python 3.12 (backend)
**Primary Dependencies**: React 18, TanStack Query v5, Axios, lucide-react (frontend); FastAPI, psycopg3 (backend)
**Storage**: PostgreSQL 16 + Apache AGE graph (existing `resource_drift` table, no schema changes)
**Testing**: Manual testing via quickstart scenarios
**Target Platform**: Web browser (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend SPA + backend API)
**Performance Goals**: Calendar renders within 2 seconds for resources with up to 1,000 drift events; fleet calendar handles 10,000+ events
**Constraints**: Two-layer colour intensity (lifetime base + daily spike); responsive from 375px to 2560px
**Scale/Scope**: Up to 10,000 resources, 100,000+ drift events across the fleet

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First | PASS | Drift data is in a relational table (resource_drift) by design — drift is metadata, not graph topology. Resource `first_seen` is a graph node property accessed via Cypher. No violation. |
| II. Normalised Taxonomy | N/A | No taxonomy changes |
| III. Pluggable Collectors | N/A | No collector changes |
| IV. Scored Intelligence | N/A | No scoring changes (future: drift frequency could feed into scoring signals) |
| V. Adaptive Learning | N/A | No learning changes |
| VI. Relationship-Centric | PASS | Calendar links back to resource detail and drift modal — relationships remain accessible from the resource page |
| VII. Open Boundaries | PASS | Fleet calendar aggregates across all vendors — no vendor partitioning |
| VIII. Zero-Friction Deployment | PASS | No new services or dependencies; new endpoint uses existing psycopg3 pool; frontend component uses only React + existing theme tokens |

**Post-Phase 1 re-check**: All gates still pass. No new persistent entities, no new services, no schema migrations required. The new backend endpoint queries the existing `resource_drift` table with date-range aggregation.

## Project Structure

### Documentation (this feature)

```text
specs/004-drift-calendar-heatmap/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── drift-calendar-api.md  # API contract for drift timeline endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/inventoryview/
│   ├── api/v1/resources.py          # Add drift timeline endpoints
│   └── services/
│       └── drift.py                 # Add timeline aggregation queries
└── tests/                           # (existing)

frontend/
├── src/
│   ├── api/
│   │   ├── resources.ts             # Add drift timeline API functions
│   │   └── types.ts                 # Add DriftTimeline types
│   ├── components/
│   │   ├── drift/                   # NEW directory
│   │   │   ├── DriftCalendar.tsx        # Main calendar heatmap component
│   │   │   ├── CalendarGrid.tsx         # SVG/DOM grid rendering (weeks × days)
│   │   │   ├── CalendarCell.tsx         # Single day cell with tooltip + click handler
│   │   │   ├── CalendarLegend.tsx       # Colour scale legend
│   │   │   └── CalendarNav.tsx          # Previous/next period navigation
│   │   └── resource/
│   │       └── DriftModal.tsx       # MODIFIED: accept optional date filter prop
│   ├── hooks/
│   │   └── useResources.ts         # Add useDriftTimeline and useFleetDriftTimeline hooks
│   ├── pages/
│   │   ├── ResourceDetailPage.tsx   # Add DriftCalendar component
│   │   ├── LandingPage.tsx          # Add fleet DriftCalendar
│   │   └── AnalyticsPage.tsx        # Add fleet DriftCalendar
│   └── utils/
│       └── driftColors.ts           # NEW: two-layer colour intensity calculation
└── tests/                           # (existing)
```

**Structure Decision**: Web application structure (Option 2). Backend gets a new aggregation query and endpoint. Frontend gets a new `drift/` component directory for the calendar, plus modifications to 4 existing files (DriftModal, ResourceDetailPage, LandingPage, AnalyticsPage). Colour intensity calculation is extracted to a utility for testability.

## Complexity Tracking

No constitution violations. No entries required.
