# Tasks: AAP Automation Correlation

**Input**: Design documents from `/specs/006-aap-automation-correlation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/automation-api.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization — new files, dependencies, migration

- [X] T001 Add python-multipart dependency to backend/pyproject.toml (needed for file upload endpoints)
- [X] T002 Create Alembic migration for AAP tables (aap_host, aap_job_execution, aap_pending_match, aap_learned_mapping) in backend/alembic/versions/005_aap_automation.py per data-model.md schema
- [X] T003 Create Pydantic models for AAP entities (AAPHost, AAPJobExecution, PendingMatch, LearnedMapping) in backend/src/inventoryview/models/automation.py per data-model.md
- [X] T004 Create Pydantic request/response schemas (UploadResponse, HostListResponse, PendingMatchResponse, CoverageResponse, HistoryResponse, ReviewRequest, ReportResponse, AutomationGraphResponse) in backend/src/inventoryview/schemas/automation.py per contracts/automation-api.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Add AUTOMATED_BY and AUTOMATING edge types to EdgeType enum in backend/src/inventoryview/models/relationship.py per research.md R6
- [X] T006 Register the automations API router in backend/src/inventoryview/api/v1/router.py with prefix "/automations" and create the empty route module at backend/src/inventoryview/api/v1/automations.py
- [X] T007 Add AAP TypeScript types (AAPHost, AAPJobExecution, PendingMatch, LearnedMapping, CoverageStats, AutomationHistory, AutomationGraphData) to frontend/src/api/types.ts per contracts/automation-api.md response schemas

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Upload AAP Metrics Data (Priority: P1) MVP

**Goal**: Administrator uploads a metrics utility archive (ZIP/tar.gz), system extracts CSVs, parses 2-line metadata headers, persists AAP host and job data, and shows import summary.

**Independent Test**: Upload a metrics utility ZIP via the sidebar, verify import summary shows correct counts, confirm AAP host and job data is persisted in aap_host and aap_job_execution tables.

### Implementation for User Story 1

- [X] T008 [US1] Implement archive extraction and CSV parsing service in backend/src/inventoryview/services/aap_import.py — extract ZIP/tar.gz, walk data/YYYY/MM/DD/ hierarchy, identify 4 CSV types by filename pattern (main_host_*, job_host_summary_*, main_jobevent_*, main_indirectmanagednodeaudit_*), strip 2-line metadata headers, parse with csv.DictReader, return structured data per research.md R1
- [X] T009 [US1] Implement data persistence in backend/src/inventoryview/services/aap_import.py — upsert aap_host rows (keyed on host_id+org_id), insert aap_job_execution rows (keyed on aap_host_id+job_id), extract smbios_uuid from canonical_facts JSON, compute first_seen/last_seen/total_jobs/total_events aggregates, handle re-imports by merging without duplicates per FR-017
- [X] T010 [US1] Implement POST /api/v1/automations/upload endpoint in backend/src/inventoryview/api/v1/automations.py — accept multipart file upload (max 200MB), validate file extension (.zip/.tar.gz), call aap_import service, return UploadResponse with counts per contracts/automation-api.md
- [X] T011 [US1] Create TanStack Query hooks for upload in frontend/src/hooks/useAutomation.ts — useUploadMetrics mutation (POST multipart/form-data to /api/v1/automations/upload), return import summary
- [X] T012 [US1] Create AutomationUploadPage in frontend/src/pages/AutomationUploadPage.tsx — drag-and-drop file zone, file type validation (.zip/.tar.gz), upload progress indicator, import summary display (hosts imported, jobs processed, events counted, auto-matched, pending review), error state for invalid files
- [X] T013 [US1] Add "Automations" section to sidebar navigation in frontend/src/components/layout/Sidebar.tsx — new NavItem with Upload, Review Queue, Coverage, and Reports sub-items, following existing Providers/Playlists pattern
- [X] T014 [US1] Add routes for automation pages in frontend/src/App.tsx (or router config) — /automations/upload, /automations/review, /automations/coverage, /automations/reports

**Checkpoint**: User Story 1 fully functional — can upload metrics utility files, parse CSVs, persist data, and see import summary

---

## Phase 4: User Story 2 — Automatic Host-to-Resource Correlation (Priority: P1)

**Goal**: After upload, system automatically correlates AAP hosts to inventory resources using 6-tier cascading matching, creates AAPHost graph nodes and AUTOMATED_BY edges, deduplicates hostnames resolving to the same machine.

**Independent Test**: Import AAP data, verify high-confidence matches (SMBIOS UUID) create AUTOMATED_BY graph edges automatically, low-confidence matches appear in aap_pending_match table.

**Depends on**: US1 (data must be imported first)

### Implementation for User Story 2

- [X] T015 [US2] Implement 6-tier cascading matching engine in backend/src/inventoryview/services/aap_correlation.py — Tier 1: lookup aap_learned_mapping by hostname+org_id (score 100), Tier 2: match smbios_uuid against Resource raw_properties using existing _extract_hw_ids() from asset_correlation.py (score 92-98), Tier 3: exact hostname/FQDN match against Resource name (score 95), Tier 4: IP address match (score 85-90), Tier 5: hostname prefix matching (score 60-70), Tier 6: partial/fuzzy (score 25-40). Return list of (resource_uid, score, reason) per research.md R3
- [X] T016 [US2] Implement graph node/edge creation in backend/src/inventoryview/services/aap_correlation.py — create AAPHost nodes in Apache AGE graph with properties per data-model.md, create AUTOMATED_BY edges from AAPHost to Resource for matches scoring ≥80, update aap_host.correlation_status to 'auto_matched' and set correlated_resource_uid
- [X] T017 [US2] Implement deduplication logic in backend/src/inventoryview/services/aap_correlation.py — group AAP hosts by smbios_uuid before creating edges, ensure multiple hostnames (john, john.redhat, john.redhat.com) all resolve to the same Resource node, each hostname gets its own AAPHost node but all point to the same Resource via AUTOMATED_BY edges per FR-007
- [X] T018 [US2] Implement pending match creation in backend/src/inventoryview/services/aap_correlation.py — for matches scoring <80, insert into aap_pending_match table with suggested_resource_uid, match_score, match_reason, status='pending'. For unmatched hosts (no candidates), create pending_match with null suggested_resource_uid per FR-006
- [X] T019 [US2] Wire auto-correlation into upload flow in backend/src/inventoryview/api/v1/automations.py — after successful import in POST /upload, call aap_correlation.correlate_hosts(), include correlation_summary (auto_matched, pending_review, unmatched counts) in UploadResponse
- [X] T020 [US2] Implement GET /api/v1/automations/hosts endpoint in backend/src/inventoryview/api/v1/automations.py — list aap_host records with cursor pagination, filter by correlation_status, search by hostname, join correlated resource details per contracts/automation-api.md

**Checkpoint**: User Story 2 fully functional — upload triggers auto-correlation, high-confidence matches create graph edges, low-confidence matches queued for review

---

## Phase 5: User Story 3 — Manual Match Review and Learned Mappings (Priority: P2)

**Goal**: Admin reviews pending matches in a dedicated queue with bulk actions, approves/rejects/ignores, approved matches create learned mappings for future imports.

**Independent Test**: Navigate to review queue, see pending matches with scores, approve one, re-import same data, verify previously-pending host now auto-matches.

**Depends on**: US2 (pending matches must exist)

### Implementation for User Story 3

- [X] T021 [US3] Implement GET /api/v1/automations/pending endpoint in backend/src/inventoryview/api/v1/automations.py — list aap_pending_match records with cursor pagination, filter by min_score/max_score, sort by score_desc/score_asc/hostname_asc, join AAP host data and suggested resource details per contracts/automation-api.md
- [X] T022 [US3] Implement POST /api/v1/automations/pending/review endpoint in backend/src/inventoryview/api/v1/automations.py — accept bulk ReviewRequest with array of actions (approve/reject/ignore), for approve: create AUTOMATED_BY graph edge + AAPHost node, update aap_host.correlation_status to 'manual_matched', create aap_learned_mapping row, support override_resource_uid for admin corrections. For reject: update status to 'rejected'. For ignore: update status to 'ignored'. Per contracts/automation-api.md
- [X] T023 [US3] Add review queue hooks to frontend/src/hooks/useAutomation.ts — usePendingMatches query (GET /pending with filters), useReviewMatches mutation (POST /pending/review with bulk actions), invalidate pending query on review success
- [X] T024 [US3] Create AutomationReviewPage in frontend/src/pages/AutomationReviewPage.tsx — paginated table of pending matches showing hostname, suggested resource name, confidence score bar, match reason badge. Bulk action toolbar: select-all checkbox, filter-by-score range slider, "Approve Selected" and "Reject Selected" buttons. Individual row: click to expand with resource search/picker for override. Per FR-008 and clarification Q3

**Checkpoint**: User Story 3 fully functional — review queue with bulk actions, learned mappings persist across imports

---

## Phase 6: User Story 4 — Automation History Timeline (Priority: P2)

**Goal**: Resource detail page shows complete automation history: first/last dates, total jobs, chronological execution list with status breakdowns.

**Independent Test**: Navigate to a resource with correlated AAP data, verify Automation History section shows first/last dates, total job count, paginated execution timeline.

**Depends on**: US2 (correlations must exist)

### Implementation for User Story 4

- [X] T025 [US4] Implement GET /api/v1/automations/resources/{resource_uid}/history endpoint in backend/src/inventoryview/api/v1/automations.py — query aap_host by correlated_resource_uid, join aap_job_execution, compute first/last automation dates, return paginated execution list with job_name, status breakdown (ok/changed/failures/dark/skipped), project, org, correlation_type per contracts/automation-api.md
- [X] T026 [US4] Add useAutomationHistory hook to frontend/src/hooks/useAutomation.ts — query GET /automations/resources/{uid}/history with pagination
- [X] T027 [US4] Create AutomationHistory component in frontend/src/components/automation/AutomationHistory.tsx — summary header (first automated, last automated, total jobs), paginated timeline list showing each execution with job name, date, status bars (ok/changed/failures/dark/skipped as coloured segments), project, org, direct/indirect badge. Show empty state when no automations exist
- [X] T028 [US4] Integrate AutomationHistory into existing resource detail page — import and render AutomationHistory component in the resource detail page, passing resource_uid as prop, positioned after existing resource metadata sections per FR-013

**Checkpoint**: User Story 4 fully functional — automation history visible on resource detail pages

---

## Phase 7: User Story 5 — Automation Coverage Dashboard (Priority: P2)

**Goal**: Landing page and analytics page show automation coverage metrics: total automated (deduplicated), coverage percentage, per-provider breakdown, top automated resources.

**Independent Test**: After importing and correlating AAP data, navigate to landing page and see coverage summary. Navigate to automation dashboard and see provider-level breakdowns.

**Depends on**: US2 (correlations must exist)

### Implementation for User Story 5

- [X] T029 [US5] Implement GET /api/v1/automations/coverage endpoint in backend/src/inventoryview/services/aap_reports.py — count distinct Resource UIDs with at least one AUTOMATED_BY incoming edge (deduplicated), compute total resources, coverage percentage, group by vendor for per-provider breakdown, fetch top 10 automated resources by job count, recent imports summary. Per contracts/automation-api.md
- [X] T030 [US5] Wire coverage endpoint in backend/src/inventoryview/api/v1/automations.py — GET /coverage calls aap_reports.get_coverage_stats(), returns CoverageResponse
- [X] T031 [US5] Add useCoverageStats hook to frontend/src/hooks/useAutomation.ts — query GET /automations/coverage
- [X] T032 [US5] Create AutomationCoverage widget in frontend/src/components/automation/AutomationCoverage.tsx — summary card showing "X / Y (Z%) automated", provider breakdown donut charts reusing existing DonutChart component, top automated resources list, empty state with "Upload metrics data" CTA when no data exists per FR-012
- [X] T033 [US5] Create AutomationDashboardPage in frontend/src/pages/AutomationDashboardPage.tsx — full coverage dashboard with AutomationCoverage widget, unautomated resources list, automation frequency distribution, provider drill-down links
- [X] T034 [US5] Add automation coverage summary to landing page in frontend/src/pages/LandingPage.tsx — small AutomationCoverage card between existing sections, showing total automated / total resources / percentage, link to full dashboard. Show nothing if no AAP data imported
- [X] T035 [P] [US5] Create AutomationBadge component in frontend/src/components/automation/AutomationBadge.tsx — inline badge showing "Automated" with job count, for use on provider drill-down page resource lists per FR-018

**Checkpoint**: User Story 5 fully functional — coverage dashboard, landing page summary, provider badges

---

## Phase 8: User Story 6 — Automation Relationships in Graph (Priority: P3)

**Goal**: Graph visualisation renders AAPHost nodes and AUTOMATED_BY edges with distinct styling. Deduplicated hostnames form visible hostname resolution trees.

**Independent Test**: Navigate to resource with AAP correlations, open graph overlay, verify AAPHost nodes and AUTOMATED_BY edges appear with distinct styling.

**Depends on**: US2 (graph nodes/edges must exist)

### Implementation for User Story 6

- [X] T036 [US6] Implement GET /api/v1/automations/graph/{resource_uid} endpoint in backend/src/inventoryview/api/v1/automations.py — query Apache AGE for AAPHost nodes connected to resource via AUTOMATED_BY edges, return nodes and edges in Cytoscape.js-compatible format per contracts/automation-api.md
- [X] T037 [US6] Extend graph canvas to render AAPHost nodes in frontend — update the existing Cytoscape.js graph component to handle "AAPHost" node type with distinct visual style (different colour, icon, shape from Resource nodes), and "AUTOMATED_BY" edge type with distinct line style (dashed for indirect, solid for direct). Add these to the graph's stylesheet configuration
- [X] T038 [US6] Integrate automation graph data into resource subgraph query — when fetching a resource's subgraph for the graph overlay, also fetch /automations/graph/{resource_uid} and merge the AAPHost nodes and AUTOMATED_BY edges into the Cytoscape.js elements array, so automation relationships appear alongside infrastructure topology per FR-014 and FR-015

**Checkpoint**: User Story 6 fully functional — automation relationships visible in graph with distinct styling

---

## Phase 9: User Story 7 — Automation Reports (Priority: P3)

**Goal**: Generate exportable automation coverage reports with deduplicated counts, per-provider breakdowns, automated and unautomated resource lists.

**Independent Test**: Generate coverage report, verify 3 hostnames resolving to 1 machine = 1 automated resource. Export as CSV and verify all fields present.

**Depends on**: US2 (correlations must exist), US5 (coverage stats service)

### Implementation for User Story 7

- [X] T039 [US7] Implement report generation in backend/src/inventoryview/services/aap_reports.py — generate_coverage_report() returns full report with deduplicated automated list (resource_uid, name, vendor, type, first_automated, last_automated, total_jobs, aap_hostnames array), unautomated list, summary stats. Support CSV export with io.StringIO + csv.writer per FR-016
- [X] T040 [US7] Implement GET /api/v1/automations/reports/coverage endpoint in backend/src/inventoryview/api/v1/automations.py — accept format=json|csv query param, optional vendor filter. For JSON: return ReportResponse. For CSV: return StreamingResponse with text/csv content type and Content-Disposition header per contracts/automation-api.md
- [X] T041 [US7] Add useReport hooks to frontend/src/hooks/useAutomation.ts — useAutomationReport query (GET /reports/coverage), useExportReport function that triggers CSV download via window.open or fetch+blob
- [X] T042 [US7] Add reports UI to AutomationDashboardPage or create dedicated reports section in frontend/src/pages/AutomationDashboardPage.tsx — "Generate Report" button, in-page report view showing automated/unautomated tables with deduplicated counts, "Export CSV" button, optional vendor filter dropdown

**Checkpoint**: User Story 7 fully functional — reports generated with accurate deduplicated counts, CSV export working

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 Add error handling for edge cases in backend/src/inventoryview/services/aap_import.py — empty archive, no valid CSVs, corrupt CSV rows (skip with warning), archive with no data/ directory. Return descriptive error messages per spec edge cases
- [X] T044 Add error handling for orphaned resources in backend/src/inventoryview/services/aap_correlation.py — when a correlated Resource is deleted, flag AAPHost as "resource_removed" in aap_host table. When a learned_mapping references a deleted resource, skip it and fall back to cascade per spec edge cases
- [X] T045 [P] Add multi-candidate handling in backend/src/inventoryview/services/aap_correlation.py — when an AAP host matches multiple resources with equal confidence, create one aap_pending_match per candidate so admin can choose per spec edge cases
- [X] T046 [P] Add loading/empty states to all automation frontend pages — skeleton loaders during data fetch, empty state illustrations with CTA to upload metrics data when no AAP data exists
- [X] T047 Run quickstart.md scenarios 1-7 as manual validation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — upload and parsing
- **US2 (Phase 4)**: Depends on US1 — correlation needs imported data
- **US3 (Phase 5)**: Depends on US2 — review queue needs pending matches
- **US4 (Phase 6)**: Depends on US2 — history needs correlations (can run parallel with US3)
- **US5 (Phase 7)**: Depends on US2 — coverage needs correlations (can run parallel with US3, US4)
- **US6 (Phase 8)**: Depends on US2 — graph needs AAPHost nodes (can run parallel with US3-US5)
- **US7 (Phase 9)**: Depends on US2, US5 — reports reuse coverage stats service
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

```
US1 (Upload) ──→ US2 (Correlation) ──┬──→ US3 (Review Queue)
                                      ├──→ US4 (History Timeline)
                                      ├──→ US5 (Coverage Dashboard) ──→ US7 (Reports)
                                      └──→ US6 (Graph Visualisation)
```

### Parallel Opportunities

After US2 completes, US3, US4, US5, and US6 can all run in parallel:
- **US3** (Review): backend API + frontend page — independent files
- **US4** (History): backend endpoint + frontend component — independent files
- **US5** (Coverage): backend service + frontend dashboard — independent files
- **US6** (Graph): backend endpoint + frontend graph extension — independent files

Within each story, [P] marked tasks can run in parallel.

---

## Parallel Example: After US2 Completes

```bash
# These 4 stories can start simultaneously:
US3: T021-T024 (Review Queue — API + frontend page)
US4: T025-T028 (History Timeline — API + frontend component)
US5: T029-T035 (Coverage Dashboard — API + frontend pages)
US6: T036-T038 (Graph — API + frontend graph extension)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T007)
3. Complete Phase 3: US1 — Upload (T008-T014)
4. Complete Phase 4: US2 — Correlation (T015-T020)
5. **STOP and VALIDATE**: Upload a metrics file, verify auto-correlation works, check graph for AUTOMATED_BY edges

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 + US2 → Core pipeline working (MVP!)
3. US3 → Review queue adds manual accuracy improvement
4. US4 + US5 (parallel) → Dashboard and history add visibility
5. US6 → Graph integration adds visual context
6. US7 → Reports add export capability
7. Polish → Edge cases and hardening

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable after US2
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The existing asset_correlation.py _extract_hw_ids() function is reused by US2 Tier 2 matching — do not duplicate
