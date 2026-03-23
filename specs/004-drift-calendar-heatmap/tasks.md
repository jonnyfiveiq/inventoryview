# Tasks: Drift Calendar Heatmap

**Input**: Design documents from `/specs/004-drift-calendar-heatmap/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/drift-calendar-api.md, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/inventoryview/`
- **Frontend**: `frontend/src/`

---

## Phase 1: Setup

**Purpose**: Create new files and directories needed for the drift calendar feature

- [X] T001 Create frontend drift component directory at frontend/src/components/drift/
- [X] T002 [P] Create drift colour utility with two-layer intensity calculation and 5-level colour scale in frontend/src/utils/driftColors.ts — export functions: `computeIntensity(resourceLifetimeCount, fleetAvgLifetime, dayCount, resourceMaxDailyCount)` returning 0.0–1.0, `intensityToColor(intensity)` returning hex colour, `DISCOVERY_COLOR` constant (#38bdf8)
- [X] T003 [P] Add DriftTimeline TypeScript types to frontend/src/api/types.ts — add `DriftTimelineDay` (date, count, fields[]), `DriftTimelineResponse` (data[], total_drift_count, first_seen), `FleetDriftTimelineResponse` (data[], fleet_avg_lifetime, total_resources_with_drift)

---

## Phase 2: Foundational (Backend Timeline API)

**Purpose**: Add drift timeline aggregation endpoints — MUST be complete before any frontend calendar can function

**⚠️ CRITICAL**: No user story work can begin until the backend timeline endpoints exist

- [X] T004 Add `get_drift_timeline()` function to backend/src/inventoryview/services/drift.py — accepts `resource_uid`, optional `start`/`end` date strings, queries `resource_drift` table with `GROUP BY DATE(changed_at)` returning list of `{date, count, fields[]}` dicts, plus `total_drift_count` (all-time count for resource)
- [X] T005 Add `get_fleet_drift_timeline()` function to backend/src/inventoryview/services/drift.py — accepts optional `start`/`end` date strings, queries `resource_drift` table aggregating across ALL resources with `GROUP BY DATE(changed_at)`, also computes `fleet_avg_lifetime` (total events / distinct resource_uids) and `total_resources_with_drift`
- [X] T006 Add `GET /resources/{uid}/drift/timeline` endpoint to backend/src/inventoryview/api/v1/resources.py — accepts optional `start` and `end` query params (YYYY-MM-DD strings, default to 365 days ago and today), calls `get_drift_timeline()`, also fetches `first_seen` from the resource graph node, returns `{data, total_drift_count, first_seen}`
- [X] T007 Add `GET /drift/fleet-timeline` endpoint to backend/src/inventoryview/api/v1/drift.py — accepts optional `start` and `end` query params, calls `get_fleet_drift_timeline()`, returns `{data, fleet_avg_lifetime, total_resources_with_drift}`
- [X] T008 Add drift timeline API functions to frontend/src/api/resources.ts — add `getResourceDriftTimeline(uid, start?, end?)` and `getFleetDriftTimeline(start?, end?)` calling the new endpoints
- [X] T009 Add TanStack Query hooks to frontend/src/hooks/useResources.ts — add `useDriftTimeline(uid, start?, end?)` with query key `["resource", uid, "drift-timeline", start, end]` and `useFleetDriftTimeline(start?, end?)` with query key `["drift", "fleet-timeline", start, end]`, staleTime 60s

**Checkpoint**: Backend timeline API works — `GET /api/v1/resources/{uid}/drift/timeline` and `GET /api/v1/drift/fleet-timeline` return aggregated daily drift data

---

## Phase 3: User Story 1 — Resource Drift Calendar (Priority: P1) 🎯 MVP

**Goal**: Users see a GitHub-style calendar heatmap on each resource's detail page showing drift activity over time with two-layer relative colour intensity

**Independent Test**: Navigate to a resource detail page for a resource with drift history. Verify the calendar grid renders with coloured cells for drift days, a blue cell for discovery day, month labels, and tooltips on hover.

### Implementation for User Story 1

- [X] T010 [US1] Create CalendarCell component in frontend/src/components/drift/CalendarCell.tsx — renders a single SVG `<rect>` with fill colour based on intensity prop, shows tooltip on hover (date, count, fields), calls onDayClick when clicked if count > 0, accepts `isDiscovery` prop to use DISCOVERY_COLOR
- [X] T011 [US1] Create CalendarGrid component in frontend/src/components/drift/CalendarGrid.tsx — renders a 53-column × 7-row SVG grid of CalendarCell components, maps DriftTimelineDay[] data to cells, adds day-of-week labels (Mon/Wed/Fri) on the left, adds month labels along the top, fills empty days with neutral cells
- [X] T012 [US1] Create CalendarLegend component in frontend/src/components/drift/CalendarLegend.tsx — renders a horizontal row of 5 colour swatches (empty → light yellow → yellow → orange → red) with "Less" and "More" labels plus a discovery colour swatch labelled "Discovery"
- [X] T013 [P] [US1] Create CalendarNav component in frontend/src/components/drift/CalendarNav.tsx — previous/next buttons to shift the 365-day window, displays the current date range (e.g., "Mar 2025 – Mar 2026"), emits onPeriodChange(start, end) callback
- [X] T014 [US1] Create DriftCalendar component in frontend/src/components/drift/DriftCalendar.tsx — main component accepting `mode="resource"`, `resourceUid`, `onDayClick` props; uses `useDriftTimeline(uid)` and `useFleetDriftTimeline()` hooks; computes per-cell intensity using `computeIntensity()` from driftColors.ts; marks the `first_seen` date as discovery; renders CalendarNav + CalendarGrid + CalendarLegend; handles loading and empty states
- [X] T015 [US1] Add DriftCalendar to ResourceDetailPage in frontend/src/pages/ResourceDetailPage.tsx — render `<DriftCalendar mode="resource" resourceUid={uid} onDayClick={handleDayClick} />` on the resource detail page, positioned below the resource info section and above the existing drift history button

**Checkpoint**: User Story 1 is fully functional — resource detail page shows calendar heatmap with discovery cell, drift cells, tooltips, and period navigation

---

## Phase 4: User Story 2 — Fleet-Wide Drift Overview (Priority: P2)

**Goal**: A fleet-wide calendar heatmap appears on both the landing page and analytics page showing aggregate daily drift activity across all resources

**Independent Test**: Navigate to the landing page and analytics page. Verify a fleet calendar renders on each page with coloured cells reflecting total daily drift across all resources.

### Implementation for User Story 2

- [X] T016 [US2] Extend DriftCalendar to support `mode="fleet"` in frontend/src/components/drift/DriftCalendar.tsx — when mode is "fleet", use only `useFleetDriftTimeline()` hook, compute intensity using absolute daily count mapped to percentile buckets within the visible window, no discovery cell, tooltip shows fleet-wide totals
- [X] T017 [US2] Add fleet DriftCalendar to LandingPage in frontend/src/pages/LandingPage.tsx — render `<DriftCalendar mode="fleet" />` below the HeatmapStrip and above the VendorCarousel, with a section header "Drift Activity"
- [X] T018 [US2] Add fleet DriftCalendar to AnalyticsPage in frontend/src/pages/AnalyticsPage.tsx — render `<DriftCalendar mode="fleet" />` alongside the existing HeatmapDetail, with a section header "Drift Activity"

**Checkpoint**: User Story 2 is complete — fleet calendar visible on both landing page and analytics page with aggregate drift data

---

## Phase 5: User Story 3 — Click-Through to Drift Detail (Priority: P3)

**Goal**: Clicking a coloured day cell on a resource's drift calendar opens the existing drift modal filtered to that specific day

**Independent Test**: Click a coloured day cell on a resource's drift calendar. Verify the drift modal opens showing only changes from that day. Click an empty cell and verify nothing happens.

### Implementation for User Story 3

- [X] T019 [US3] Extend DriftModal to accept optional `filterDate` prop in frontend/src/components/resource/DriftModal.tsx — when `filterDate` (YYYY-MM-DD string) is provided, filter the drift entries client-side to only show entries where `changed_at` matches that date, update modal title to include the date
- [X] T020 [US3] Wire DriftCalendar onDayClick to DriftModal in frontend/src/pages/ResourceDetailPage.tsx — add state for `selectedDriftDate`, set it when a calendar cell is clicked, pass it as `filterDate` to DriftModal, open the modal when a date is selected, clear the date when modal closes

**Checkpoint**: User Story 3 is complete — clicking a drift day cell opens the filtered drift modal, clicking empty cells does nothing

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Responsive design, edge cases, and final validation

- [X] T021 [P] Add responsive styles to DriftCalendar — ensure the calendar renders without horizontal page scrolling on screens 1024px+, add horizontal scrolling within the calendar container on screens below 1024px, test at 375px width
- [X] T022 [P] Handle edge cases in DriftCalendar — resource with no drift (show only discovery cell), resource discovered today (single cell), fallback to absolute thresholds when fewer than 5 resources have drift (per FR-006)
- [ ] T023 Run quickstart.md validation — manually test all 9 scenarios from specs/004-drift-calendar-heatmap/quickstart.md and verify pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start after Phase 2
  - US2 (Phase 4): Depends on US1 (extends DriftCalendar with fleet mode)
  - US3 (Phase 5): Depends on US1 (needs DriftCalendar onDayClick wiring)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 — extends DriftCalendar component with fleet mode
- **User Story 3 (P3)**: Depends on US1 — needs DriftCalendar and onDayClick mechanism; also modifies DriftModal

### Within Each User Story

- Types/utilities before hooks
- Hooks before components
- Inner components before outer components (CalendarCell → CalendarGrid → DriftCalendar)
- Integration (page wiring) last

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, no dependencies)
- T004 and T005 are sequential (same file but different functions — can be parallelised if careful)
- T010, T012, T013 can be started in parallel once foundational is done (different files)
- T021 and T022 can run in parallel (different concerns)

---

## Parallel Example: Phase 1 Setup

```bash
# These can run in parallel:
Task T002: "Create drift colour utility in frontend/src/utils/driftColors.ts"
Task T003: "Add DriftTimeline types to frontend/src/api/types.ts"
```

## Parallel Example: Phase 6 Polish

```bash
# These can run in parallel:
Task T021: "Add responsive styles to DriftCalendar"
Task T022: "Handle edge cases in DriftCalendar"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational — backend timeline API (T004-T009)
3. Complete Phase 3: User Story 1 — resource drift calendar (T010-T015)
4. **STOP and VALIDATE**: View resource detail page, verify calendar with coloured cells
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Timeline API works
2. Add User Story 1 → Resource calendar with relative colouring → Deploy/Demo (MVP!)
3. Add User Story 2 → Fleet calendar on landing + analytics pages → Deploy/Demo
4. Add User Story 3 → Click-through to filtered drift modal → Deploy/Demo
5. Polish → Responsive, edge cases, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 both depend on US1 — cannot be worked in parallel
- Backend changes (Phase 2) are moderate — 2 new service functions + 2 new endpoints in existing files
- Frontend is the bulk of the work — 5 new files, 1 new utility, 4 modified files
- No database schema migrations required — queries existing resource_drift table
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
