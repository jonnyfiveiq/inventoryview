# Tasks: Spotlight-Style Universal Search

**Input**: Design documents from `/specs/003-spotlight-search/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/search-api.md

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

**Purpose**: Create new files and directories needed for the search feature

- [X] T001 Create frontend search component directory at frontend/src/components/search/
- [X] T002 [P] Create taxonomy label utility with normalised_type-to-human-readable mapping in frontend/src/utils/taxonomyLabels.ts
- [X] T003 [P] Create useDebouncedValue hook in frontend/src/hooks/useDebouncedValue.ts

---

## Phase 2: Foundational (Backend Search API)

**Purpose**: Add the `search` query parameter to the existing GET /resources endpoint — MUST be complete before any frontend search UI can function

**⚠️ CRITICAL**: No user story work can begin until the backend search capability exists

- [X] T004 Add `search` query parameter to the Cypher query builder in backend/src/inventoryview/services/graph.py — extend `query_resource_nodes()` to accept an optional `search` string and add OR-chained `toLower(r.field) CONTAINS toLower($search)` WHERE clauses for name, vendor_id, state, vendor, and normalised_type
- [X] T005 Add `search` parameter passthrough in backend/src/inventoryview/services/resources.py — pass the search string from the service layer to the graph query function
- [X] T006 Add `search` query parameter to the GET /resources route handler in backend/src/inventoryview/api/v1/resources.py — accept optional `search: str = None` query param with minimum 2 character validation, pass to service layer
- [X] T007 Add `search` parameter to the frontend API client in frontend/src/api/resources.ts — extend ListResourcesParams interface with optional `search: string` field and include it in the request query params

**Checkpoint**: Backend search works — `GET /api/v1/resources?search=john` returns matching resources across all fields and providers

---

## Phase 3: User Story 1 - Real-Time Search with Taxonomy Grouping (Priority: P1) 🎯 MVP

**Goal**: Users can open a Spotlight-style overlay, type a query, and see results grouped by normalised taxonomy type across all providers

**Independent Test**: Open search overlay with Cmd+K, type a query, verify grouped results appear with taxonomy headers, counts, resource names, providers, and states

### Implementation for User Story 1

- [X] T008 [US1] Create useSearch hook in frontend/src/hooks/useSearch.ts — TanStack Query hook that calls listResources({ search: query, page_size: 50 }) with query key ["resources", "search", query], enabled only when query.length >= 2
- [X] T009 [US1] Create SearchResultItem component in frontend/src/components/search/SearchResultItem.tsx — displays a single result row with resource name, provider badge, state indicator, and onClick handler for navigation
- [X] T010 [US1] Create TaxonomyGroup component in frontend/src/components/search/TaxonomyGroup.tsx — displays a group header (human-readable type name + count), renders up to 5 SearchResultItems initially, "Show more" button to expand to 10, "View all X on provider page" link when more than 10 exist
- [X] T011 [US1] Create SearchResults component in frontend/src/components/search/SearchResults.tsx — takes Resource[] from useSearch, groups by normalised_type using reduce(), renders TaxonomyGroup for each group, handles loading spinner, empty state ("Start typing to search..."), and no-results state ("No results found")
- [X] T012 [US1] Create SearchInput component in frontend/src/components/search/SearchInput.tsx — text input with search icon, uses useDebouncedValue(300ms), auto-focuses on mount, calls onChange with debounced value
- [X] T013 [US1] Create SpotlightOverlay component in frontend/src/components/search/SpotlightOverlay.tsx — React portal rendering a centered modal with backdrop blur/dim, contains SearchInput and SearchResults, manages isOpen state, closes on click-outside, passes debounced query to useSearch and feeds results to SearchResults
- [X] T014 [US1] Add global Cmd+K / Ctrl+K keyboard listener to open SpotlightOverlay — add useEffect in frontend/src/components/layout/AppLayout.tsx that listens for the keyboard shortcut and toggles the overlay open state, render SpotlightOverlay component in AppLayout

**Checkpoint**: User Story 1 is fully functional — Cmd+K opens overlay, typing shows grouped results, clicking a result navigates to resource detail page

---

## Phase 4: User Story 2 - Keyboard Navigation and Selection (Priority: P2)

**Goal**: Users can navigate search results entirely via keyboard (Up/Down arrows, Enter to select, Escape to close)

**Independent Test**: Open overlay, type query, press Down arrow to highlight results, press Enter to navigate to resource detail, press Escape to close

### Implementation for User Story 2

- [X] T015 [US2] Add keyboard navigation state management to SpotlightOverlay in frontend/src/components/search/SpotlightOverlay.tsx — track highlightedIndex state, handle ArrowDown (increment, wrap at end), ArrowUp (decrement, wrap at start), Enter (navigate to highlighted result's /resources/{uid}), Escape (close overlay)
- [X] T016 [US2] Add visual highlight styling to SearchResultItem in frontend/src/components/search/SearchResultItem.tsx — accept isHighlighted prop, apply distinct background/border style when highlighted, ensure highlighted item scrolls into view
- [X] T017 [US2] Pass keyboard navigation props through SearchResults and TaxonomyGroup — thread highlightedIndex and flat result list through SearchResults in frontend/src/components/search/SearchResults.tsx and TaxonomyGroup in frontend/src/components/search/TaxonomyGroup.tsx so each item knows if it's highlighted

**Checkpoint**: User Story 2 is complete — full keyboard navigation works across taxonomy groups with visual highlighting

---

## Phase 5: User Story 3 - Search Activation via Header Icon (Priority: P3)

**Goal**: A visible search icon in the sidebar/header provides discoverability and mouse-based activation of the search overlay

**Independent Test**: Click the search icon in the sidebar, verify overlay opens with input focused, hover to see keyboard shortcut tooltip

### Implementation for User Story 3

- [X] T018 [US3] Add search icon button to Sidebar in frontend/src/components/layout/Sidebar.tsx — add a Search icon (from lucide-react) as a clickable NavItem-style button near the top of the sidebar, with tooltip showing "Search (⌘K)", onClick triggers the same overlay open handler from AppLayout
- [X] T019 [US3] Wire search icon click to SpotlightOverlay open state — lift the overlay open state to a shared location (props callback or context) so both the Cmd+K shortcut in AppLayout and the Sidebar search icon can trigger it, update frontend/src/components/layout/AppLayout.tsx accordingly

**Checkpoint**: User Story 3 is complete — search icon visible in sidebar, click opens overlay, tooltip shows shortcut

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Responsive design, edge cases, and final integration

- [X] T020 [P] Add responsive styles to SpotlightOverlay in frontend/src/components/search/SpotlightOverlay.tsx — full-width on screens below 640px, centered modal (max-width ~600px) on larger screens
- [X] T021 [P] Handle special characters and error states in SearchInput — ensure special characters are passed as-is without breaking, display error banner in overlay if backend request fails in frontend/src/components/search/SearchResults.tsx
- [ ] T022 Run quickstart.md validation — manually test all 9 scenarios from specs/003-spotlight-search/quickstart.md and verify pass
- [X] T023 Wire AppLayout into React Router as a layout route in frontend/src/router/index.tsx — wrap all protected routes as children of AppLayout so Sidebar, SpotlightOverlay, and Cmd+K shortcut render on every authenticated page

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start after Phase 2
  - US2 (Phase 4): Depends on US1 (extends SpotlightOverlay with keyboard nav)
  - US3 (Phase 5): Depends on US1 (needs overlay open state to wire into)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 — extends SpotlightOverlay with keyboard navigation
- **User Story 3 (P3)**: Depends on US1 — needs the overlay open state mechanism to wire icon click

### Within Each User Story

- Models/utilities before hooks
- Hooks before components
- Inner components before outer components (SearchResultItem → TaxonomyGroup → SearchResults → SpotlightOverlay)
- Integration (AppLayout wiring) last

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, no dependencies)
- T004, T005, T006 are sequential (graph.py → resources.py → resources route)
- T009 and T010 can be started in parallel once T008 is done
- T020 and T021 can run in parallel (different concerns)

---

## Parallel Example: Phase 1 Setup

```bash
# These can run in parallel:
Task T002: "Create taxonomy label utility in frontend/src/utils/taxonomyLabels.ts"
Task T003: "Create useDebouncedValue hook in frontend/src/hooks/useDebouncedValue.ts"
```

## Parallel Example: Phase 6 Polish

```bash
# These can run in parallel:
Task T020: "Add responsive styles to SpotlightOverlay"
Task T021: "Handle special characters and error states"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational — backend search API (T004-T007)
3. Complete Phase 3: User Story 1 — overlay with grouped results (T008-T014)
4. **STOP and VALIDATE**: Test search overlay with Cmd+K, verify grouping works
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Backend search works
2. Add User Story 1 → Overlay with grouped results → Deploy/Demo (MVP!)
3. Add User Story 2 → Keyboard navigation → Deploy/Demo
4. Add User Story 3 → Header icon discoverability → Deploy/Demo
5. Polish → Responsive, error handling, quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 and US3 both depend on US1 — cannot be worked in parallel
- Backend changes (Phase 2) are small — 3 files modified, no schema migration
- Frontend is the bulk of the work — 8 new files, 2 modified files
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
