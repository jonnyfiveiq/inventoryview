# Tasks: Resource Playlists

**Input**: Design documents from `/specs/005-resource-playlists/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/playlists-api.md, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted. Manual validation via seed data and UI.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Database migration and backend scaffolding shared by all user stories

- [X] T001 Create Alembic migration for playlist, playlist_membership, and playlist_activity tables in backend/alembic/versions/004_playlists.py — include all columns, constraints, indexes, and CHECK constraint on activity action field per data-model.md
- [X] T002 Create Pydantic request/response schemas for playlists in backend/src/inventoryview/schemas/playlists.py — PlaylistCreateRequest, PlaylistUpdateRequest, PlaylistResponse (with member_count), PlaylistMembershipResponse, PlaylistActivityResponse, PlaylistActivityTimelineDay
- [X] T003 [P] Add playlist TypeScript types to frontend/src/api/types.ts — Playlist, PlaylistMembership, PlaylistActivity, PlaylistActivityTimelineDay, PlaylistDetailResponse interfaces

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core service layer and API registration that MUST complete before any user story

- [X] T004 Implement playlist service with slug generation and CRUD operations in backend/src/inventoryview/services/playlists.py — create_playlist (with slugify + collision handling), get_playlist (by slug or UUID), list_playlists, update_playlist (re-slug on rename), delete_playlist, add_resource, remove_resource, get_playlists_for_resource, record_activity, get_activity, get_activity_timeline. All functions async, using pool pattern from existing services.
- [X] T005 Create playlist API endpoints in backend/src/inventoryview/api/v1/playlists.py — all endpoints per contracts/playlists-api.md: list, create, get detail (slug or UUID), update, delete, add member, remove member, get activity log, get activity timeline. Include require_auth dependency on all routes.
- [X] T006 Register playlists router in backend/src/inventoryview/api/v1/router.py — add `router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])`
- [X] T007 Create playlist API client functions in frontend/src/api/playlists.ts — listPlaylists, createPlaylist, getPlaylist, updatePlaylist, deletePlaylist, addResourceToPlaylist, removeResourceFromPlaylist, getPlaylistsForResource, getPlaylistActivity, getPlaylistActivityTimeline
- [X] T008 Create TanStack Query hooks in frontend/src/hooks/usePlaylists.ts — usePlaylists, usePlaylist, usePlaylistsForResource, usePlaylistActivity, usePlaylistActivityTimeline, plus mutation hooks useCreatePlaylist, useUpdatePlaylist, useDeletePlaylist, useAddToPlaylist, useRemoveFromPlaylist

**Checkpoint**: Backend API fully functional. Frontend data layer ready. All subsequent UI work can proceed.

---

## Phase 3: User Story 1 — Create and Manage Playlists (Priority: P1)

**Goal**: Playlists appear in sidebar with full CRUD (create, rename, delete)

**Independent Test**: Create a playlist via sidebar, verify it appears alphabetically, rename it, delete it.

- [X] T009 [US1] Add "Playlists" section to sidebar in frontend/src/components/layout/Sidebar.tsx — add collapsible Playlists section below Providers with "+" new playlist button, list playlists alphabetically using usePlaylists hook, each playlist links to /playlists/:slug, include inline rename and delete actions via context menu or icon buttons
- [X] T010 [US1] Add /playlists/:identifier route to frontend/src/router/index.tsx — lazy-load PlaylistDetailPage as a protected route child

**Checkpoint**: Playlists can be created, listed, renamed, and deleted from the sidebar. Clicking navigates to playlist detail route (page built in US3).

---

## Phase 4: User Story 2 — Add Resources to Playlists (Priority: P1)

**Goal**: Any resource can be added to or removed from playlists via the resource detail page

**Independent Test**: Navigate to a resource, add it to a playlist, verify membership via API.

- [X] T011 [US2] Create AddToPlaylistButton component in frontend/src/components/playlist/AddToPlaylistButton.tsx — dropdown button showing all playlists with checkboxes indicating current membership (via usePlaylistsForResource), toggling adds/removes resource using mutation hooks, shows toast confirmation on success
- [X] T012 [US2] Wire AddToPlaylistButton into ResourceDetailPage in frontend/src/pages/ResourceDetailPage.tsx — add the button to the header actions area next to "View Graph" and "Drift History" buttons, passing the current resource UID
- [X] T013 [US2] Add resource endpoint for playlist lookup in backend/src/inventoryview/api/v1/resources.py — add GET /resources/{uid}/playlists endpoint that returns playlists containing this resource, using get_playlists_for_resource service function

**Checkpoint**: Resources can be added to and removed from playlists. Membership state reflected in checkbox UI.

---

## Phase 5: User Story 3 — View Playlist Members (Priority: P1)

**Goal**: Clicking a playlist shows its member resources in a detail page with table

**Independent Test**: Click a populated playlist in sidebar, verify all members listed with correct attributes.

- [X] T014 [US3] Create PlaylistDetailPage in frontend/src/pages/PlaylistDetailPage.tsx — page header with playlist name (editable), description, member count, and action buttons. Members table with columns: name, vendor, normalised type, category, state. Each row clickable to navigate to /resources/:uid. Remove button per row. Empty state with guidance when no members. Use usePlaylist hook for data.

**Checkpoint**: Full P1 MVP complete — playlists can be created, populated, viewed, and managed.

---

## Phase 6: User Story 4 — REST API for External Clients (Priority: P2)

**Goal**: External clients can GET a playlist's resources as JSON with configurable detail level

**Independent Test**: curl the playlist endpoint by slug, verify JSON response shape matches contract.

- [X] T015 [US4] Add ?detail=full query parameter support to get playlist detail endpoint in backend/src/inventoryview/api/v1/playlists.py and backend/src/inventoryview/services/playlists.py — when detail=full, join full resource data including raw_properties from the graph; when detail=summary (default), return only summary fields per contracts/playlists-api.md
- [X] T016 [US4] Add copyable endpoint URL display to PlaylistDetailPage in frontend/src/pages/PlaylistDetailPage.tsx — show the REST endpoint URL (e.g., /api/v1/playlists/{slug}) with a copy-to-clipboard button, positioned near the page header

**Checkpoint**: External clients can consume playlists via REST. Admins can copy the endpoint URL.

---

## Phase 7: User Story 5 — JSON Preview in UI (Priority: P2)

**Goal**: JSON button on playlist page shows exact REST response in a modal

**Independent Test**: Click JSON button, verify displayed JSON matches what curl returns.

- [X] T017 [US5] Create PlaylistJsonPreview component in frontend/src/components/playlist/PlaylistJsonPreview.tsx — modal/panel that fetches the playlist detail endpoint (summary mode) and displays formatted, syntax-highlighted JSON. Include "Copy to Clipboard" button and a toggle to switch between summary and full detail views.
- [X] T018 [US5] Wire JSON preview button into PlaylistDetailPage in frontend/src/pages/PlaylistDetailPage.tsx — add a "JSON" button to the header actions that opens the PlaylistJsonPreview modal

**Checkpoint**: All P2 user stories complete. External integration workflow fully functional.

---

## Phase 8: User Story 6 — Playlist Activity Log and Calendar Heatmap (Priority: P3)

**Goal**: Activity audit trail with calendar heatmap visualisation on playlist page

**Independent Test**: Add/remove resources from a playlist, verify activity entries appear, calendar days highlight.

- [X] T019 [US6] Extend DriftCalendar to support playlist activity mode in frontend/src/components/drift/DriftCalendar.tsx — add mode "playlist" alongside existing "resource" and "fleet" modes. When mode is "playlist", accept a playlistId prop and use usePlaylistActivityTimeline hook instead of drift hooks. Calendar grid, cells, nav, and legend sub-components remain unchanged.
- [X] T020 [US6] Create PlaylistActivityLog component in frontend/src/components/playlist/PlaylistActivityLog.tsx — paginated list of activity entries showing timestamp, action type (with icon/color coding: green for added, red for removed, amber for system deletion), resource name (as link if resource still exists), and detail text. Support date filtering via prop (for calendar day click integration).
- [X] T021 [US6] Wire activity log and calendar heatmap into PlaylistDetailPage in frontend/src/pages/PlaylistDetailPage.tsx — add "Activity" section with DriftCalendar in playlist mode and PlaylistActivityLog below it. Clicking a calendar day filters the activity log to that date.

**Checkpoint**: Full audit trail with visual calendar heatmap operational.

---

## Phase 9: User Story 7 — Infrastructure Donut Charts on Playlist (Priority: P3)

**Goal**: Donut charts showing infrastructure type breakdown of playlist members

**Independent Test**: Create playlist with mixed infrastructure resources, verify donuts show correct proportions.

- [X] T022 [US7] Wire infrastructure donut charts into PlaylistDetailPage in frontend/src/pages/PlaylistDetailPage.tsx — reuse existing DonutChart component from frontend/src/components/heatmap/DonutChart.tsx. Compute vendor-to-infrastructure-type mapping (same grouping as HeatmapDetail: vmware/openshift/kubernetes → Private Cloud, aws/azure/gcp → Public Cloud, cisco/juniper/paloalto/fortinet → Networking, netapp/pure/dell/emc → Storage) from the playlist's member resources. Display donut charts grouped by infrastructure type. Hide section when playlist is empty.

**Checkpoint**: All P3 user stories complete. Full feature implemented.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Seed data, cleanup, and validation

- [X] T023 Update seed_test_data.sh to create sample playlists, add resources to them, and generate activity log entries spanning multiple days for testing calendar heatmap and activity log
- [X] T024 Restart backend container and verify all new endpoints return correct responses — test playlist CRUD, membership operations, activity timeline, and ?detail=full parameter
- [X] T025 Run through quickstart.md scenarios end-to-end in the browser — verify all 4 scenarios work as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration must exist before service layer)
- **US1 (Phase 3)**: Depends on Phase 2 — sidebar + route
- **US2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1/US2 but practically benefits from US1 (sidebar links to this page)
- **US4 (Phase 6)**: Depends on Phase 2 — backend already has the endpoint from foundational; this phase adds detail level control
- **US5 (Phase 7)**: Depends on US4 (needs the REST response shape to preview)
- **US6 (Phase 8)**: Depends on Phase 2 (activity data flows from foundational service layer)
- **US7 (Phase 9)**: Depends on US3 (needs the PlaylistDetailPage to exist)
- **Polish (Phase 10)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational
- **US2 (P1)**: Independent after Foundational — parallel with US1
- **US3 (P1)**: Independent after Foundational — parallel with US1/US2
- **US4 (P2)**: Independent after Foundational — can parallel with P1 stories
- **US5 (P2)**: Depends on US4 (JSON preview needs the endpoint response shape)
- **US6 (P3)**: Independent after Foundational
- **US7 (P3)**: Depends on US3 (page must exist to add donuts to it)

### Parallel Opportunities

- T002 and T003 can run in parallel (backend schemas + frontend types)
- T009 and T011 can run in parallel (sidebar vs resource detail button — different files)
- T019 and T020 can run in parallel (calendar extension vs activity log — different files)
- US1, US2, US3 can all start in parallel after Phase 2

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup (migration + schemas)
2. Complete Phase 2: Foundational (service + API + frontend data layer)
3. Complete Phase 3-5: All P1 stories (sidebar, add-to-playlist, view members)
4. **STOP and VALIDATE**: Playlists fully functional in the UI
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Backend API fully functional
2. Add US1 + US2 + US3 → Full UI CRUD (MVP!)
3. Add US4 + US5 → External client integration + JSON preview
4. Add US6 + US7 → Activity tracking + analytics
5. Polish → Seed data + end-to-end validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Slug generation logic (slugify + collision suffix) is critical — see research.md R2
- Activity logging happens inside the service layer on every membership change — not as a separate step
- DriftCalendar reuse: add "playlist" mode, don't fork the component — see research.md R4
- DonutChart reuse: same vendor grouping as HeatmapDetail — see spec FR-014
