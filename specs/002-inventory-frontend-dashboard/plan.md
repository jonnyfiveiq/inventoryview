# Implementation Plan: InventoryView Frontend Dashboard

**Branch**: `002-inventory-frontend-dashboard` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-inventory-frontend-dashboard/spec.md`

## Summary

Build a React + TypeScript single-page application that consumes the existing InventoryView backend REST API (`/api/v1/`) to provide a Netflix-style infrastructure dashboard. The frontend features taxonomy-based carousels, provider drill-down with filtering/pagination, interactive graph visualization of resource relationships, infrastructure heatmaps, and a dark theme throughout. Deployed as a static web application communicating with the backend over HTTP.

## Technical Context

**Language/Version**: TypeScript 5.7+, React 19
**Primary Dependencies**: Vite 6 (build), React Router (routing), Tailwind CSS v3 (styling), Cytoscape.js (graph visualization), TanStack Query v5 (data fetching/caching), Axios (HTTP client), Zustand (state management), lucide-react (icons)
**Storage**: N/A (all data from backend API; auth token in memory + sessionStorage)
**Testing**: Vitest (unit), React Testing Library (component), Playwright (E2E)
**Target Platform**: Modern desktop browsers (Chrome, Firefox, Safari, Edge) — 1280px to 3840px
**Project Type**: Web application (SPA)
**Performance Goals**: Landing page interactive within 3 seconds, graph with 50 nodes interactive within 2 seconds, smooth 60fps pan/zoom
**Constraints**: Must work against existing `/api/v1/` endpoints without backend changes. Dark theme only. No WebSocket/SSE.
**Scale/Scope**: Low thousands of resources, ~8 pages (Login, Setup, Landing, Provider, Vendor, Resource Detail, Analytics, Graph overlay, 404), single admin user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Graph-First | **PASS** | Frontend consumes graph data via `/api/v1/resources/{uid}/graph` endpoint. No client-side graph storage — all traversal is server-side via Cypher. |
| II. Normalised Taxonomy | **PASS** | Carousels grouped by `normalised_type`. Resource cards display both `normalised_type` and `vendor_type`. |
| III. Pluggable Collectors | **N/A** | Frontend does not interact with collectors. |
| IV. Scored Intelligence | **N/A** | Scoring not yet implemented in backend. Frontend can display scores when available. |
| V. Adaptive Learning | **N/A** | Not applicable to frontend. |
| VI. Relationship-Centric | **PASS** | Graph overlay visualizes all edge types with colour coding. Relationships accessible from both resource table and detail page. |
| VII. Open Boundaries | **PASS** | No vendor-partitioned views — graph traversal crosses all boundaries. Provider views are a filter, not a partition. |
| VIII. Zero-Friction Deployment | **PASS** | Frontend is a static build artifact. Can be served from the same container or standalone. `npm install && npm run dev` for development. |

**Technology Stack Compliance**: React + TypeScript + Vite, Shadcn/UI + Tailwind CSS — all mandated by constitution. Cytoscape.js selected over D3.js (see research.md).

**GATE RESULT**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-inventory-frontend-dashboard/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-client.md    # Backend API contract for frontend consumption
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── components.json          # shadcn/ui config
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx             # App entry point
│   ├── App.tsx              # Router + layout
│   ├── index.css            # Tailwind directives + dark theme vars
│   ├── lib/
│   │   └── utils.ts         # cn() helper from shadcn
│   ├── api/
│   │   ├── client.ts        # Axios instance with auth interceptor
│   │   ├── resources.ts     # Resource API calls
│   │   ├── relationships.ts # Relationship API calls
│   │   ├── auth.ts          # Auth API calls
│   │   └── types.ts         # API response types
│   ├── stores/
│   │   └── auth.ts          # Zustand auth store (token, user)
│   ├── hooks/
│   │   ├── useResources.ts  # TanStack Query hooks for resources
│   │   ├── useGraph.ts      # TanStack Query hooks for graph data
│   │   └── useAuth.ts       # Auth hooks
│   ├── components/
│   │   ├── ui/              # Shadcn/UI components (button, card, etc.)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx       # Collapsible left sidebar nav
│   │   │   ├── AppLayout.tsx     # Main layout wrapper
│   │   │   └── ErrorBanner.tsx   # Connection error banner
│   │   ├── carousel/
│   │   │   ├── ResourceCarousel.tsx  # Horizontal scrollable carousel
│   │   │   ├── ResourceCard.tsx      # Card within carousel
│   │   │   └── VendorCarousel.tsx   # Vendor navigation carousel
│   │   ├── heatmap/
│   │   │   ├── HeatmapStrip.tsx      # Compact landing page strip
│   │   │   └── HeatmapDetail.tsx     # Full analytics page heatmaps
│   │   ├── graph/
│   │   │   ├── GraphOverlay.tsx      # Full-screen overlay/modal
│   │   │   ├── GraphCanvas.tsx       # Cytoscape.js canvas
│   │   │   └── GraphControls.tsx     # Depth slider, legend
│   │   ├── provider/
│   │   │   ├── ResourceTable.tsx     # Filterable resource table
│   │   │   └── FilterBar.tsx         # Category/state/region filters
│   │   └── resource/
│   │       ├── ResourceProperties.tsx # Full property display
│   │       └── DriftModal.tsx        # Drift history modal
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── SetupPage.tsx
│   │   ├── LandingPage.tsx
│   │   ├── ProviderPage.tsx
│   │   ├── VendorPage.tsx           # Vendor drill-down by type
│   │   ├── ResourceDetailPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   └── NotFoundPage.tsx
│   └── router/
│       ├── index.tsx         # Route definitions
│       └── ProtectedRoute.tsx # Auth guard
└── tests/
    ├── unit/
    ├── component/
    └── e2e/
```

**Structure Decision**: Single `frontend/` directory at repository root, alongside existing `backend/`. Standard Vite + React project layout with feature-based component organization.

## Complexity Tracking

> No constitution violations. No complexity tracking entries needed.
