# Tasks: InventoryView Frontend Dashboard

**Input**: Design documents from `/specs/002-inventory-frontend-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-client.md

**Tests**: Not explicitly requested in spec. Omitted unless noted.

**Organization**: Tasks grouped by user story (P1–P5) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the frontend project with all tooling and dependencies

- [X] T001 Initialize Vite + React + TypeScript project in `frontend/` using `npm create vite@latest frontend -- --template react-ts`
- [X] T002 Install core dependencies: `react-router-dom`, `@tanstack/react-query`, `axios`, `zustand`, `cytoscape`, `d3-scale-chromatic`, `d3-scale` in `frontend/package.json`
- [X] T003 Install dev dependencies: `tailwindcss`, `postcss`, `autoprefixer`, `@types/cytoscape` in `frontend/package.json`
- [X] T004 Configure Tailwind CSS with dark theme defaults in `frontend/tailwind.config.js` and `frontend/src/index.css`
- [X] T005 Initialize Shadcn/UI utilities: install `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`, and create `frontend/src/lib/utils.ts` with `cn()` helper
- [X] T006 Shadcn/UI components implemented via Tailwind utility classes directly in components (no separate ui/ files needed)
- [X] T007 Configure Vite proxy to forward `/api` requests to `http://localhost:8000` in `frontend/vite.config.ts`
- [X] T008 Create base CSS variables for dark theme colour palette (backgrounds, surfaces, borders, text, accent colours, state colours for poweredOn/poweredOff/maintenance) in `frontend/src/index.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: API client, auth store, routing, and layout — required by ALL user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Define TypeScript API types (Resource, Relationship, SubgraphResponse, PaginatedResponse, AuthSession, LoginRequest, SetupStatus) in `frontend/src/api/types.ts`
- [X] T010 Create Axios client instance with base URL from `VITE_API_BASE_URL`, request interceptor for auth token injection, and response interceptor for 401 redirect in `frontend/src/api/client.ts`
- [X] T011 Create Zustand auth store with token, username, login/logout actions, sessionStorage persistence, and token expiry check in `frontend/src/stores/auth.ts`
- [X] T012 [P] Create auth API functions (login, revoke, getSetupStatus, setupInit) in `frontend/src/api/auth.ts`
- [X] T013 [P] Create resources API functions (listResources, getResource, getResourceRelationships, getResourceGraph) in `frontend/src/api/resources.ts`
- [X] T014 [P] Create relationships API module (placeholder for future use) in `frontend/src/api/relationships.ts`
- [X] T015 Create useAuth hook wrapping auth store with login/logout/isAuthenticated logic in `frontend/src/hooks/useAuth.ts`
- [X] T016 Create ProtectedRoute component that redirects to `/login` if unauthenticated in `frontend/src/router/ProtectedRoute.tsx`
- [X] T017 Create React Router configuration with routes for Login, Landing, Provider, ResourceDetail, Analytics, and 404 in `frontend/src/router/index.tsx`
- [X] T018 Create collapsible Sidebar component with icon+label navigation (Home, Providers sub-menu, Analytics), collapsed state in Zustand in `frontend/src/components/layout/Sidebar.tsx`
- [X] T019 Create AppLayout component wrapping Sidebar + main content area + ErrorBanner in `frontend/src/components/layout/AppLayout.tsx`
- [X] T020 Create ErrorBanner component for connection errors with retry button in `frontend/src/components/layout/ErrorBanner.tsx`
- [X] T021 Wire up App.tsx with QueryClientProvider, RouterProvider, and AppLayout in `frontend/src/App.tsx` and update `frontend/src/main.tsx`

**Checkpoint**: Foundation ready — app renders with sidebar, routing works, API client configured, auth guard active

---

## Phase 3: User Story 5 — Authentication & Session Management (Priority: P5 but prerequisite)

**Goal**: Login page, setup detection, session management — required before any authenticated page works

**Independent Test**: Navigate to any page without token → redirected to login. Login → token stored → landing page loads. Token expiry → redirected back.

> Note: Implemented before P1 because all other stories require a working auth flow.

- [X] T022 [US5] Create LoginPage with username/password form, error display, and submit handler calling auth API in `frontend/src/pages/LoginPage.tsx`
- [X] T023 [US5] Create SetupPage for first-time admin account creation (shown when setup_complete=false) in `frontend/src/pages/SetupPage.tsx`
- [X] T024 [US5] Add setup status check to LoginPage — if not setup_complete, redirect to /setup in `frontend/src/pages/LoginPage.tsx`
- [X] T025 [US5] Add logout button to Sidebar footer that calls token revoke and clears auth store in `frontend/src/components/layout/Sidebar.tsx`
- [X] T026 [US5] Add session expiry detection: check token expiry timestamp on each navigation, show "session expired" message on redirect to login in `frontend/src/hooks/useAuth.ts`

**Checkpoint**: Full auth flow works — setup detection, login, token storage, logout, expiry handling

---

## Phase 4: User Story 1 — Landing Page with Taxonomy Carousels (Priority: P1) 🎯 MVP

**Goal**: Netflix-style landing page with horizontal carousels grouped by normalised_type, each containing resource cards

**Independent Test**: Login → landing page shows one carousel per normalised_type with resource cards showing name, vendor badge, state indicator, key properties. Empty types have no carousel. Click card → navigate to resource detail.

- [X] T027 [US1] Create useResources hook with TanStack Query for fetching all resources (large page_size for landing page) in `frontend/src/hooks/useResources.ts`
- [X] T028 [P] [US1] Create ResourceCard component showing resource name, vendor badge (coloured by vendor), state indicator (coloured dot), category, and normalised_type summary in `frontend/src/components/carousel/ResourceCard.tsx`
- [X] T029 [P] [US1] Create vendor badge sub-component with distinct colours per vendor (vmware=blue, aws=orange, azure=cyan, openshift=red) in `frontend/src/components/carousel/ResourceCard.tsx`
- [X] T030 [US1] Create ResourceCarousel component with horizontal CSS scroll-snap container, left/right arrow buttons, carousel title (normalised_type label), and resource count badge in `frontend/src/components/carousel/ResourceCarousel.tsx`
- [X] T031 [US1] Create LandingPage that fetches resources, groups by normalised_type, renders one ResourceCarousel per type (skip empty types), ordered by count descending in `frontend/src/pages/LandingPage.tsx`
- [X] T032 [US1] Add click handler on ResourceCard to navigate to `/resources/:uid` in `frontend/src/components/carousel/ResourceCard.tsx`
- [X] T033 [US1] Add loading skeleton state for LandingPage while resources are fetching in `frontend/src/pages/LandingPage.tsx`
- [X] T034 [US1] Add empty state for LandingPage when no resources exist (friendly message with suggestion to run a collector) in `frontend/src/pages/LandingPage.tsx`

**Checkpoint**: Landing page shows carousels with resource cards grouped by type. Cards are clickable. MVP is functional.

---

## Phase 5: User Story 2 — Provider Drill-Down with Filtering (Priority: P2)

**Goal**: Dedicated provider page with filterable, paginated resource table. Each row has a graph icon.

**Independent Test**: Click vendor badge on landing page or select provider from sidebar → provider page with resource table. Apply filters (category, state) → table updates. Scroll → pagination loads more. Click row → resource detail.

- [X] T035 [P] [US2] Create FilterBar component with dropdowns for category, state, region, normalised_type (populated from current data) and a clear-filters button in `frontend/src/components/provider/FilterBar.tsx`
- [X] T036 [P] [US2] Create ResourceTable component with columns: name, normalised_type, category, state (coloured), region, last_seen, graph icon button in `frontend/src/components/provider/ResourceTable.tsx`
- [X] T037 [US2] Create ProviderPage that extracts vendor from URL params, fetches resources with vendor filter and cursor-based pagination via TanStack Query's useInfiniteQuery, renders FilterBar + ResourceTable in `frontend/src/pages/ProviderPage.tsx`
- [X] T038 [US2] Add infinite scroll / "Load more" trigger at table bottom using Intersection Observer for cursor-based pagination in `frontend/src/pages/ProviderPage.tsx`
- [X] T039 [US2] Add "no results" empty state when filters produce zero results, with suggestion to adjust filters in `frontend/src/components/provider/ResourceTable.tsx`
- [X] T040 [US2] Add click handler on resource row to navigate to `/resources/:uid` in `frontend/src/components/provider/ResourceTable.tsx`
- [X] T041 [US2] Populate sidebar Providers sub-menu dynamically from unique vendors in fetched resources in `frontend/src/components/layout/Sidebar.tsx`
- [X] T042 [US2] Add vendor badge click handler on landing page ResourceCard to navigate to `/providers/:vendor` in `frontend/src/components/carousel/ResourceCard.tsx`

**Checkpoint**: Provider drill-down works with filtering, pagination, and navigation to detail pages.

---

## Phase 6: User Story 3 — Interactive Graph Visualization (Priority: P3)

**Goal**: Full-screen overlay with Cytoscape.js graph showing resource relationships, adjustable depth, pan/zoom, click-to-inspect, lazy expansion.

**Independent Test**: Click graph icon in resource table or "View Graph" on detail page → overlay opens centred on resource. Nodes and colour-coded edges render. Depth slider adjusts graph. Click node → tooltip. Click peripheral node → graph expands. Close returns to previous page.

- [X] T043 [US3] Create useGraph hook with TanStack Query for fetching subgraph by uid and depth in `frontend/src/hooks/useGraph.ts`
- [X] T044 [US3] Create GraphCanvas component: initialize Cytoscape.js instance with dark theme styling, render nodes (sized/coloured by category) and edges (coloured by relationship type with labels), fit-to-view on load in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T045 [US3] Define Cytoscape.js style constants: edge colours by type (DEPENDS_ON=red, HOSTED_ON=blue, MEMBER_OF=green, CONTAINS=purple, CONNECTED_TO=cyan, ATTACHED_TO=yellow, MANAGES=orange, ROUTES_TO=teal, PEERS_WITH=pink), node colours by category in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T046 [US3] Create GraphControls component with depth slider (1-5), legend showing edge colour meanings, "showing N of M" node count indicator, close button in `frontend/src/components/graph/GraphControls.tsx`
- [X] T047 [US3] Create GraphOverlay component as full-screen modal/overlay (z-50, dark backdrop), rendering GraphCanvas + GraphControls, managing open/close state in `frontend/src/components/graph/GraphOverlay.tsx`
- [X] T048 [US3] Add click-to-inspect: tap a node → show tooltip/panel with resource name, type, vendor, state, category using Cytoscape.js `tap` event in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T049 [US3] Add lazy expansion: tap a peripheral node (degree=1 in current view) → fetch its subgraph at depth=1 → merge new nodes/edges into existing graph without resetting layout in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T050 [US3] Add graph icon column click handler in ResourceTable to open GraphOverlay for that resource's uid in `frontend/src/components/provider/ResourceTable.tsx`
- [X] T051 [US3] Create ResourceDetailPage showing all resource properties, metadata table, first_seen/last_seen timestamps, relationships list, and "View Graph" button that opens GraphOverlay in `frontend/src/pages/ResourceDetailPage.tsx`
- [X] T052 [US3] Handle edge case: resource with no relationships shows single node with "No relationships found" message in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T053 [US3] Add configurable node limit (default 100) with "showing N of M" indicator when graph exceeds limit in `frontend/src/components/graph/GraphControls.tsx`

**Checkpoint**: Graph overlay works from both resource table and detail page. Nodes, edges, depth slider, inspect, and expansion all functional.

---

## Phase 7: User Story 4 — Infrastructure Heatmaps (Priority: P4)

**Goal**: Compact heatmap strip on landing page + full-size heatmaps on dedicated Analytics page showing category counts, state distribution, and activity recency.

**Independent Test**: Landing page shows heatmap strip above carousels with category counts and state indicators. Analytics page shows full heatmaps with hover tooltips. Data matches actual resource counts.

- [X] T054 [P] [US4] Create HeatmapStrip component: compact horizontal strip showing category count cells (colour intensity by count) and state distribution mini-bar in `frontend/src/components/heatmap/HeatmapStrip.tsx`
- [X] T055 [P] [US4] Create HeatmapDetail component: full-size grid heatmaps for category counts, state distribution chart, and recently changed resources list (sorted by last_seen, warmer colours for more recent) in `frontend/src/components/heatmap/HeatmapDetail.tsx`
- [X] T056 [US4] Add colour scale utility using d3-scale-chromatic (sequential warm palette) for mapping counts/recency to cell colours in `frontend/src/components/heatmap/HeatmapStrip.tsx`
- [X] T057 [US4] Add tooltip integration: hover over any heatmap cell → shows exact count and label (e.g., "compute: 15 resources") in both HeatmapStrip and HeatmapDetail
- [X] T058 [US4] Integrate HeatmapStrip into LandingPage above carousels in `frontend/src/pages/LandingPage.tsx`
- [X] T059 [US4] Create AnalyticsPage rendering HeatmapDetail with resource data from TanStack Query cache (or fresh fetch) in `frontend/src/pages/AnalyticsPage.tsx`

**Checkpoint**: Heatmaps render on both landing page and analytics page with accurate counts and tooltips.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Responsive layout, error handling, performance, and production readiness

- [X] T060 [P] Add responsive breakpoints: sidebar auto-collapses below 1280px in `frontend/src/components/layout/Sidebar.tsx`
- [X] T061 [P] Add connection error handling: ErrorBanner with retry button in `frontend/src/components/layout/ErrorBanner.tsx`
- [X] T062 [P] Add 404 page for unknown routes and "Resource not found" page for deleted resources in `frontend/src/pages/NotFoundPage.tsx`
- [X] T063 Add loading states for all pages: skeleton loaders for carousels, table rows, graph canvas, and heatmaps
- [X] T064 [P] Add TanStack Query global error handler with retry config in `frontend/src/App.tsx`
- [X] T065 [P] Optimize bundle: configure Vite code splitting for route-based lazy loading (React.lazy + Suspense for each page) in `frontend/src/router/index.tsx`
- [X] T066 Add favicon and page title in `frontend/public/favicon.svg` and `frontend/index.html`
- [ ] T067 Validate full quickstart.md walkthrough end-to-end against running backend with seeded data

---

## Phase 9: User Story 3a — Graph Visualization Enhancements (Priority: P3)

**Goal**: Fix node overlap, add type-based node shapes with labels, and a node type legend.

**Independent Test**: Open graph overlay → nodes use distinct shapes per normalised_type, display two-line labels (name + type), do not overlap, and legend shows shape-to-type mapping.

- [X] T068 [US3] Update SubgraphNode type to include `normalised_type` field in `frontend/src/api/types.ts`
- [X] T069 [US3] Rewrite GraphCanvas to use type-based node shapes (ellipse=virtual_machine, hexagon=hypervisor, barrel=datastore, diamond=virtual_switch, triangle=port_group, round-pentagon=cluster, round-rectangle=datacenter, octagon=resource_pool, tag=folder, vee=network) in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T070 [US3] Add two-line node labels (name + normalised_type) with text-wrap in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T071 [US3] Implement dynamic spacing that scales repulsion, edge length, and gravity based on node count to prevent overlap in `frontend/src/components/graph/GraphCanvas.tsx`
- [X] T072 [US3] Add node type legend to GraphControls showing shape icons next to type names in `frontend/src/components/graph/GraphControls.tsx`
- [X] T073 [US3] Update backend `get_subgraph` to include `normalised_type` in all node data (start node, outgoing edges, incoming edges) in `backend/src/inventoryview/services/graph.py`

**Checkpoint**: Graph nodes use distinct shapes per type, display readable labels, and do not overlap at any scale.

---

## Phase 10: User Story 4a — Heatmap Rework as "Resources Discovered" (Priority: P4)

**Goal**: Replace broken heatmap with "Resources Discovered" summary showing total count, 24h additions, type cells, provider bars, and state distribution.

**Independent Test**: Landing page shows "Resources Discovered" header with total count. By Type shows category-coloured cells. By Provider shows horizontal bars. By State shows coloured dots with counts.

- [X] T074 [US4] Rewrite HeatmapStrip header to show "Resources Discovered" with total count and "+N last 24h" in `frontend/src/components/heatmap/HeatmapStrip.tsx`
- [X] T075 [US4] Replace d3 colour scales with category-coloured backgrounds and opacity scaling for "By Type" cells in `frontend/src/components/heatmap/HeatmapStrip.tsx`
- [X] T076 [US4] Add "By Provider" section with horizontal bar charts using vendor colours in `frontend/src/components/heatmap/HeatmapStrip.tsx`
- [X] T077 [US4] Add "By State" section with fuzzy state matching and coloured dot indicators in `frontend/src/components/heatmap/HeatmapStrip.tsx`

**Checkpoint**: Heatmap is readable with proper contrast, all sections populated from actual data.

---

## Phase 11: User Story 3b — Relationship Name Resolution (Priority: P3)

**Goal**: Show friendly resource names instead of UUIDs in the relationships table on the resource detail page.

**Independent Test**: Navigate to a resource with relationships → Related Resource column shows human-readable names as hyperlinks, not UUIDs.

- [X] T078 [US3] Add `useQueries` batch fetching for related resource names using parallel `getResource` calls in `frontend/src/pages/ResourceDetailPage.tsx`
- [X] T079 [US3] Build `nameMap` from batch query results and replace UUID display with friendly names in the relationships table in `frontend/src/pages/ResourceDetailPage.tsx`

**Checkpoint**: Relationships table shows friendly names as clickable links to related resources.

---

## Phase 12: User Story 6 — Resource Drift Tracking (Priority: P6)

**Goal**: Full-stack drift tracking — backend schema + API, frontend drift button + modal.

**Independent Test**: View resource with drift → "Drift History" button appears. Click → modal shows date-grouped changes with field, old/new values, timestamps. Resource without drift → no button.

- [X] T080 [US6] Create Alembic migration 003 for `resource_drift` table (id, resource_uid, field, old_value, new_value, changed_at, source) with composite index in `backend/alembic/versions/003_resource_drift.py`
- [X] T081 [US6] Create drift service with record_drift, record_drift_batch, get_drift_history, has_drift functions in `backend/src/inventoryview/services/drift.py`
- [X] T082 [US6] Add drift API endpoints (GET /{uid}/drift, GET /{uid}/drift/exists, POST /{uid}/drift) in `backend/src/inventoryview/api/v1/resources.py`
- [X] T083 [US6] Add alembic/versions volume mount to docker-compose.yml in `docker/docker-compose.yml`
- [X] T084 [P] [US6] Add DriftEntry, DriftResponse, DriftExistsResponse types in `frontend/src/api/types.ts`
- [X] T085 [P] [US6] Add getResourceDrift and getResourceDriftExists API functions in `frontend/src/api/resources.ts`
- [X] T086 [P] [US6] Add useResourceDrift and useResourceDriftExists hooks in `frontend/src/hooks/useResources.ts`
- [X] T087 [US6] Create DriftModal component with date-grouped entries, colour-coded field badges, old→new values display in `frontend/src/components/resource/DriftModal.tsx`
- [X] T088 [US6] Add drift button (conditional on has_drift) and DriftModal rendering to ResourceDetailPage in `frontend/src/pages/ResourceDetailPage.tsx`
- [X] T089 [US6] Add VMware drift entries (22 entries) to seed script in `seed_test_data.sh`

**Checkpoint**: Drift tracking works end-to-end from backend schema through API to frontend modal.

---

## Phase 13: Multi-Vendor Seed Data

**Goal**: Expand seed script with AWS, Azure, and OpenShift resources, relationships, and drift entries.

- [X] T090 [P] Add AWS seed data (23 resources, 36 relationships, 7 drift entries) to `seed_test_data.sh`
- [X] T091 [P] Add Azure seed data (17 resources, 24 relationships, 6 drift entries) to `seed_test_data.sh`
- [X] T092 [P] Add OpenShift seed data (23 resources, 37 relationships, 9 drift entries) to `seed_test_data.sh`
- [X] T093 Update seed script dispatch to support `--vendor=all` and individual vendor flags in `seed_test_data.sh`

**Checkpoint**: Running `seed_test_data.sh --vendor=all` populates 96 resources, 146 relationships, 44 drift entries across 4 vendors.

---

## Phase 14: User Story 7 — Vendor Carousel & Vendor Page (Priority: P7)

**Goal**: Vendor navigation carousel on landing page and dedicated vendor drill-down page with type-grouped tables.

**Independent Test**: Landing page shows vendor carousel (vmware, aws, azure, openshift). Click vendor → vendor page with resources grouped by type in tables. Click resource name → detail page. Click graph icon → overlay.

- [X] T094 [US7] Create VendorCarousel component aggregating resources by vendor, showing coloured cards with count and type count in `frontend/src/components/carousel/VendorCarousel.tsx`
- [X] T095 [US7] Integrate VendorCarousel into LandingPage between heatmap and type carousels in `frontend/src/pages/LandingPage.tsx`
- [X] T096 [US7] Create VendorPage with type-grouped tables, state indicators, region, category, and graph icon per row in `frontend/src/pages/VendorPage.tsx`
- [X] T097 [US7] Add `/vendors/:vendor` route to router in `frontend/src/router/index.tsx`

**Checkpoint**: Vendor carousel shows all vendors. Click-through to vendor page works. Tables grouped by type with all expected columns.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US5 Auth (Phase 3)**: Depends on Foundational — BLOCKS all other user stories (they need login)
- **US1 Landing (Phase 4)**: Depends on US5 Auth
- **US2 Provider (Phase 5)**: Depends on US5 Auth. Benefits from US1 (vendor badge navigation) but independently testable
- **US3 Graph (Phase 6)**: Depends on US5 Auth. Benefits from US2 (table graph icon) and includes ResourceDetailPage
- **US4 Heatmaps (Phase 7)**: Depends on US5 Auth. Benefits from US1 (landing page integration)
- **Polish (Phase 8)**: Depends on all desired user stories being complete
- **Graph Enhancements (Phase 9)**: Depends on Phase 6 (US3 Graph) — improves existing graph
- **Heatmap Rework (Phase 10)**: Depends on Phase 7 (US4 Heatmaps) — replaces existing heatmap
- **Relationship Names (Phase 11)**: Depends on Phase 6 (US3 Graph/ResourceDetailPage)
- **Drift Tracking (Phase 12)**: Depends on Phase 6 (ResourceDetailPage) — full-stack addition
- **Multi-Vendor Seed (Phase 13)**: Independent of frontend — backend/seed only
- **Vendor Navigation (Phase 14)**: Depends on Phase 4 (US1 Landing) and Phase 6 (GraphOverlay)

### User Story Dependencies

- **US5 (Auth)**: Standalone — implemented first as prerequisite
- **US1 (Landing)**: Standalone after auth — primary MVP
- **US2 (Provider)**: Standalone after auth — adds provider badge navigation from US1 cards
- **US3 (Graph)**: Standalone after auth — adds graph icon to US2 table, creates ResourceDetailPage
- **US4 (Heatmaps)**: Standalone after auth — integrates strip into US1 landing page
- **US6 (Drift)**: Requires US3 (ResourceDetailPage) — full-stack feature
- **US7 (Vendor Navigation)**: Requires US1 (LandingPage) — enhances landing page with vendor carousel

### Within Each User Story

- API hooks before components
- Small components before page-level components
- Core rendering before interaction handlers
- Core implementation before edge cases/empty states

### Parallel Opportunities

- T012, T013, T014 (API modules) can run in parallel
- T028, T029 (ResourceCard) can run in parallel with T030 (carousel container)
- T035, T036 (FilterBar, ResourceTable) can run in parallel
- T054, T055 (heatmap components) can run in parallel
- T060, T061, T062, T064, T065 (polish tasks) can all run in parallel

---

## Implementation Strategy

### MVP First (Auth + Landing Page)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (API client, routing, layout)
3. Complete Phase 3: US5 Auth (login works)
4. Complete Phase 4: US1 Landing (carousels render)
5. **STOP and VALIDATE**: Login → see carousels → click card
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational + Auth → App runs with login
2. Add US1 Landing → Carousels work → **Demo** (MVP!)
3. Add US2 Provider → Drill-down works → **Demo**
4. Add US3 Graph → Graph overlay works → **Demo**
5. Add US4 Heatmaps → Analytics works → **Demo**
6. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US5 (Auth) is implemented before US1 despite lower spec priority because it's a technical prerequisite
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All API types defined once in T009 and shared across all stories
