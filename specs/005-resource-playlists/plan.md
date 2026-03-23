# Implementation Plan: Resource Playlists

**Branch**: `005-resource-playlists` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-resource-playlists/spec.md`

## Summary

Implement a Spotify/Apple Music-style playlist system that lets administrators curate bounded resource collections. Playlists are CRUD-managed from the sidebar, resources are added from detail pages, and the collection is exposed via authenticated REST endpoints for external clients (Ansible Automation Platform, Nexus). Includes activity audit logging with calendar heatmap visualisation and infrastructure donut chart analytics — both reusing existing components.

Storage uses standard PostgreSQL tables (not the graph) per constitution principle I ("metadata and administrative data MAY use standard PostgreSQL tables"). Three new tables: `playlist`, `playlist_membership`, `playlist_activity`.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.4+ (frontend)
**Primary Dependencies**: FastAPI, React 18, TanStack Query, Shadcn/UI + Tailwind CSS
**Storage**: PostgreSQL 16+ (standard relational tables, not Apache AGE graph)
**Testing**: Manual testing via seed data and UI verification
**Target Platform**: Docker containers (Linux), browser frontend
**Project Type**: Web application (full-stack)
**Performance Goals**: <2s response for playlists with 500 resources; <3s page render for 1,000 members
**Constraints**: Reuse existing DriftCalendar sub-components and DonutChart component
**Scale/Scope**: ~50-100 playlists, up to 1,000 resources per playlist

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First | **PASS** | Playlists are administrative metadata, not graph relationships. Constitution explicitly permits PostgreSQL tables for "metadata and administrative data." |
| II. Normalised Taxonomy | **PASS** | Playlists consume existing classified resources; no new types introduced. |
| III. Pluggable Collectors | **PASS** | Not applicable — no collector changes. |
| IV. Scored Intelligence | **PASS** | Not applicable — playlists don't generate scores. |
| V. Adaptive Learning | **PASS** | Not applicable. |
| VI. Relationship-Centric | **PASS** | Playlist membership is administrative grouping, not a discovered relationship. No graph edges needed. |
| VII. Open Boundaries | **PASS** | Constitution mentions "Resource Lists provide scoped access boundaries for consuming applications" — this feature implements exactly that concept. |
| VIII. Zero-Friction Deployment | **PASS** | No new external dependencies. Alembic migration auto-applies on startup. |

**Post-design re-check**: All gates remain PASS. No graph pollution, no new dependencies, schema created via existing Alembic migration pattern.

## Project Structure

### Documentation (this feature)

```text
specs/005-resource-playlists/
├── plan.md              # This file
├── research.md          # Phase 0: storage, slug, activity, calendar reuse decisions
├── data-model.md        # Phase 1: playlist, membership, activity tables
├── quickstart.md        # Phase 1: integration scenarios
├── contracts/
│   └── playlists-api.md # Phase 1: REST API contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 004_playlists.py                    # NEW: migration for 3 tables
├── src/inventoryview/
│   ├── api/v1/
│   │   ├── playlists.py                    # NEW: playlist CRUD + member + activity endpoints
│   │   └── router.py                       # MODIFY: register playlists router
│   ├── schemas/
│   │   └── playlists.py                    # NEW: Pydantic request/response models
│   └── services/
│       └── playlists.py                    # NEW: playlist business logic + slug generation

frontend/
├── src/
│   ├── api/
│   │   ├── playlists.ts                    # NEW: API client functions
│   │   └── types.ts                        # MODIFY: add playlist types
│   ├── hooks/
│   │   └── usePlaylists.ts                 # NEW: TanStack Query hooks
│   ├── components/
│   │   ├── layout/
│   │   │   └── Sidebar.tsx                 # MODIFY: add Playlists section
│   │   ├── playlist/
│   │   │   ├── AddToPlaylistButton.tsx     # NEW: dropdown for resource detail page
│   │   │   ├── PlaylistJsonPreview.tsx     # NEW: modal with formatted JSON + copy
│   │   │   └── PlaylistActivityLog.tsx     # NEW: activity list with date filter
│   │   └── drift/
│   │       └── DriftCalendar.tsx           # MODIFY: support playlist activity mode
│   ├── pages/
│   │   └── PlaylistDetailPage.tsx          # NEW: playlist detail with members table,
│   │                                       #       donuts, calendar, activity, JSON preview
│   └── router/
│       └── index.tsx                       # MODIFY: add /playlists/:identifier route

seed_test_data.sh                           # MODIFY: add sample playlists + membership + activity
```

**Structure Decision**: Follows the existing web application pattern (backend/ + frontend/) established by features 001 and 002. Backend adds one new service module, one API module, one schema module, and one migration. Frontend adds one new page, three new components, one API module, and one hooks module. Modifications to existing sidebar, router, calendar, and types.

## Complexity Tracking

> No constitution violations detected. No complexity tracking entries needed.
