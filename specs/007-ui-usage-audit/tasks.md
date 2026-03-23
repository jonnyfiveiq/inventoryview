# Tasks: UI Usage Analytics & Audit Tracking

**Input**: Design documents from `/specs/007-ui-usage-audit/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema and shared backend plumbing for usage analytics

- [X] T001 Create Alembic migration for `usage_event` and `login_audit` tables in backend/alembic/versions/006_usage_audit.py
- [X] T002 [P] Create Pydantic request/response schemas in backend/src/inventoryview/schemas/usage.py
- [X] T003 [P] Create usage service module with DB helpers and purge logic in backend/src/inventoryview/services/usage.py
- [X] T004 Create usage API router skeleton and register in backend/src/inventoryview/api/v1/usage.py
- [X] T005 Register usage router in backend/src/inventoryview/api/v1/router.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Frontend API client and tracking infrastructure that all stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create frontend API client for usage endpoints in frontend/src/api/usage.ts
- [X] T007 Create `useTracking()` hook with Zustand-backed 2s debounce in frontend/src/hooks/useTracking.ts
- [X] T008 Add "Administration" section with "Usage" sub-menu to sidebar in frontend/src/components/layout/Sidebar.tsx
- [X] T009 Add `/admin/usage` route to frontend router in frontend/src/router/index.tsx

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — View UI Feature Usage Dashboard (Priority: P1) 🎯 MVP

**Goal**: Admin navigates to Administration > Usage and sees feature area cards with totals, unique users, trend arrows, and time-range filtering.

**Independent Test**: Navigate to /admin/usage, verify feature area breakdown cards render with time-range filter working (even with zero data showing informational message).

### Implementation for User Story 1

- [X] T010 [US1] Implement `GET /api/v1/usage/summary` endpoint with time-range params, period comparison for trend, and lazy purge trigger in backend/src/inventoryview/api/v1/usage.py
- [X] T011 [US1] Implement summary aggregation query (GROUP BY feature_area, COUNT, COUNT DISTINCT user_id, trend calculation) in backend/src/inventoryview/services/usage.py
- [X] T012 [P] [US1] Create TimeRangeFilter component with preset buttons (24h, 7d, 30d) and custom date picker in frontend/src/components/usage/TimeRangeFilter.tsx
- [X] T013 [P] [US1] Create FeatureAreaCard component showing total events, unique users, trend arrow/percentage in frontend/src/components/usage/FeatureAreaCard.tsx
- [X] T014 [US1] Create UsageDashboardPage composing TimeRangeFilter + FeatureAreaCard grid with TanStack Query data fetching in frontend/src/pages/UsageDashboardPage.tsx
- [X] T015 [US1] Handle empty state — display informational message when no data exists for selected period in frontend/src/pages/UsageDashboardPage.tsx

**Checkpoint**: User Story 1 fully functional — admin can view usage dashboard with time filtering

---

## Phase 4: User Story 2 — Track UI Feature Interactions (Priority: P1)

**Goal**: Frontend silently records page views and feature interactions via the tracking hook; backend persists events.

**Independent Test**: Perform UI actions (navigate pages, open graph overlay, expand drift timeline), then verify events appear via `GET /api/v1/usage/summary`.

### Implementation for User Story 2

- [X] T016 [US2] Implement `POST /api/v1/usage/events` endpoint (extract user_id from token, server timestamp, validate body) in backend/src/inventoryview/api/v1/usage.py
- [X] T017 [US2] Implement `POST /api/v1/usage/events/batch` endpoint (max 50 items) in backend/src/inventoryview/api/v1/usage.py
- [X] T018 [US2] Implement event insertion service function in backend/src/inventoryview/services/usage.py
- [X] T019 [P] [US2] Instrument page views — add `useTracking()` calls for Resource Browsing page_view events in relevant page components
- [X] T020 [P] [US2] Instrument Graph Visualisation interactions (graph_overlay_opened, node_expanded, depth_changed) in frontend graph components
- [X] T021 [P] [US2] Instrument Drift Detection interactions (drift_timeline_expanded, drift_comparison_viewed) in frontend drift components
- [X] T022 [P] [US2] Instrument Asset Linkages interactions (asset_chain_link_clicked, asset_chain_viewed) in frontend asset chain components
- [X] T023 [P] [US2] Instrument Automation Metrics interactions (metrics_uploaded, correlation_run, review_action_taken) in frontend automation components
- [X] T024 [P] [US2] Instrument Playlist interactions (playlist_created, playlist_edited, playlist_member_added) in frontend playlist components
- [X] T025 [P] [US2] Instrument Navigation tracking (sidebar_section_expanded, page_navigated) in frontend/src/components/layout/Sidebar.tsx

**Checkpoint**: User Story 2 functional — all tracked interactions flow from frontend to backend and appear on dashboard

---

## Phase 5: User Story 3 — Audit Login Activity (Priority: P2)

**Goal**: Backend records every login attempt (success/failure) with IP, username, and outcome; dashboard shows login activity table with pagination.

**Independent Test**: Perform successful and failed login attempts, navigate to Usage dashboard and verify Login Activity section shows entries with correct details.

### Implementation for User Story 3

- [X] T026 [US3] Add login audit recording to auth endpoint — insert into `login_audit` on every login attempt (success and failure) with IP extraction in backend/src/inventoryview/api/v1/auth.py
- [X] T027 [US3] Implement `GET /api/v1/usage/logins` endpoint with pagination (page, page_size) and time-range filtering in backend/src/inventoryview/api/v1/usage.py
- [X] T028 [US3] Implement login audit query service (summary counts + paginated entries) in backend/src/inventoryview/services/usage.py
- [X] T029 [US3] Create LoginAuditTable component with columns (timestamp, username, IP, outcome, failure reason) and pagination controls in frontend/src/components/usage/LoginAuditTable.tsx
- [X] T030 [US3] Integrate LoginAuditTable into UsageDashboardPage as "Login Activity" section with summary bar (successful, failed, unique users) in frontend/src/pages/UsageDashboardPage.tsx

**Checkpoint**: User Story 3 functional — login audit entries captured and displayed

---

## Phase 6: User Story 4 — Feature Usage Detail Drill-Down (Priority: P3)

**Goal**: Admin clicks a feature area card to see action-level breakdown, with back navigation preserving time-range.

**Independent Test**: Click a feature area card on the dashboard, verify action breakdown with counts appears, click back and confirm time-range selection preserved.

### Implementation for User Story 4

- [X] T031 [US4] Implement `GET /api/v1/usage/feature/{feature_area}` endpoint with action-level grouping in backend/src/inventoryview/api/v1/usage.py
- [X] T032 [US4] Implement feature detail aggregation query (GROUP BY action, COUNT, COUNT DISTINCT) in backend/src/inventoryview/services/usage.py
- [X] T033 [US4] Create FeatureDetail component showing action breakdown table (action name, count, unique users) in frontend/src/components/usage/FeatureDetail.tsx
- [X] T034 [US4] Add drill-down navigation — FeatureAreaCard click navigates to detail view, back button returns to dashboard with time-range preserved (URL state or Zustand) in frontend/src/pages/UsageDashboardPage.tsx

**Checkpoint**: All user stories functional — full usage analytics with drill-down

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Data retention, edge cases, and final integration validation

- [X] T035 [P] Implement lazy 90-day purge — on summary endpoint call, check last purge timestamp, DELETE old rows from both tables if >24h since last purge in backend/src/inventoryview/services/usage.py
- [X] T036 [P] Ensure all usage endpoints require authentication (Bearer token) and return 401 for unauthenticated requests in backend/src/inventoryview/api/v1/usage.py
- [X] T037 Run quickstart.md scenarios end-to-end validation (all 6 scenarios)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration must exist, schemas/service created)
- **User Stories (Phase 3–6)**: All depend on Phase 2 completion
  - US1 (Dashboard) and US2 (Tracking) are both P1 and can proceed in parallel
  - US3 (Login Audit) can start after Phase 2 — independent of US1/US2
  - US4 (Drill-Down) depends on US1 (needs dashboard page and FeatureAreaCard to exist)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no other story dependencies
- **US2 (P1)**: After Phase 2 — no other story dependencies (but US1 makes data visible)
- **US3 (P2)**: After Phase 2 — no other story dependencies
- **US4 (P3)**: After Phase 2 + US1 (needs dashboard page and FeatureAreaCard component)

### Within Each User Story

- Backend endpoints before frontend components that consume them
- Service layer before API endpoints
- Components before page composition
- Core implementation before integration

### Parallel Opportunities

- T002 + T003 can run in parallel (different files)
- T012 + T013 can run in parallel (different components)
- T019–T025 can all run in parallel (different feature area instrumentations)
- T035 + T036 can run in parallel (different concerns)
- US1 and US2 can run in parallel after Phase 2
- US1 and US3 can run in parallel after Phase 2

---

## Parallel Example: User Story 2

```bash
# Launch all feature instrumentation tasks together:
Task: "Instrument page views in relevant page components"           [T019]
Task: "Instrument Graph Visualisation interactions"                  [T020]
Task: "Instrument Drift Detection interactions"                      [T021]
Task: "Instrument Asset Linkages interactions"                       [T022]
Task: "Instrument Automation Metrics interactions"                   [T023]
Task: "Instrument Playlist interactions"                             [T024]
Task: "Instrument Navigation tracking in Sidebar.tsx"                [T025]
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (migration, schemas, service, router)
2. Complete Phase 2: Foundational (API client, tracking hook, sidebar, route)
3. Complete Phase 3: US1 — Dashboard with summary view
4. Complete Phase 4: US2 — Instrument tracking across frontend
5. **STOP and VALIDATE**: Dashboard shows real tracked data
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Dashboard visible (MVP with manual/seed data)
3. US2 → Real tracking flowing → Deploy (core value delivered!)
4. US3 → Login audit → Deploy (security audit added)
5. US4 → Drill-down → Deploy (analytics depth added)
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
