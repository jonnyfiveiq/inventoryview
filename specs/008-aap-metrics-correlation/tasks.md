# Tasks: AAP Metrics Correlation Engine

**Input**: Design documents from `/specs/008-aap-metrics-correlation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-endpoints.md

**Tests**: Not explicitly requested — test tasks omitted. Manual integration testing per quickstart.md.

**Organization**: Tasks grouped by user story. This is an enhancement of existing code, not greenfield.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Paths are relative to repository root

---

## Phase 1: Setup (Schema & Migration)

**Purpose**: Database schema changes and score normalisation required before any correlation work.

- [X] T001 Create Alembic migration for correlation engine schema changes in backend/alembic/versions/ — add `ansible_facts` (JSONB, nullable) and `last_correlated_at` (timestamptz, nullable) columns to `aap_host` table; add `tier` (text, nullable), `matched_fields` (JSONB, nullable), and `ambiguity_group_id` (UUID, nullable) columns to `aap_pending_match` table; create `correlation_exclusion` table (id serial PK, aap_host_id integer FK, resource_uid text, created_by text, reason text nullable, created_at timestamptz, unique on aap_host_id+resource_uid); create `correlation_audit` table (id serial PK, action text, aap_host_id integer FK, resource_uid text, tier text nullable, confidence float nullable, matched_fields JSONB nullable, previous_state JSONB nullable, actor text, created_at timestamptz)
- [X] T002 Migrate existing match_score values from integer (0-100) to float (0.0-1.0) in the same Alembic migration — `UPDATE aap_host SET match_score = match_score / 100.0 WHERE match_score > 1.0`; update `aap_pending_match.match_score` similarly
- [X] T003 Update Pydantic models in backend/src/inventoryview/models/automation.py — add `ansible_facts: dict | None`, `last_correlated_at: datetime | None` to AAPHost; add `CorrelationExclusion` model; add `CorrelationAuditEntry` model; add `CorrelationTier` string enum (smbios_serial, bios_uuid, mac_address, ip_address, fqdn, hostname_heuristic, learned_mapping); update `match_score` type annotations from int to float

---

## Phase 2: Foundational (Async Job Infrastructure)

**Purpose**: Background job tracker and async upload flow. MUST complete before user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create background job tracker service in backend/src/inventoryview/services/correlation_jobs.py — module-level dict storing {job_id: {status, progress, total, matched, queued_for_review, errors, started_at, completed_at}}; functions: create_job() → uuid, update_progress(), complete_job(), fail_job(), get_job_status(); CorrelationJobStatus enum (queued, running, completed, failed)
- [X] T005 Update request/response schemas in backend/src/inventoryview/schemas/automation.py — add UploadResponse schema (hosts_imported, jobs_imported, correlation_job_id, message); add CorrelationJobResponse schema (job_id, status, progress, total, matched, queued_for_review, errors, started_at, completed_at); update PendingMatchResponse to include tier, matched_fields, ambiguity_group_id; add ReviewActionRequest to support "dismiss" action and optional reason field
- [X] T006 Enhance upload endpoint in backend/src/inventoryview/api/v1/automations.py — change POST /automations/upload to return 202 with UploadResponse including correlation_job_id; import FastAPI BackgroundTasks; after import/persist, launch correlation as background task via BackgroundTasks.add_task(); add GET /automations/correlation-jobs/{job_id} endpoint returning CorrelationJobResponse from job tracker
- [X] T007 [P] Update frontend TypeScript types in frontend/src/api/types.ts — add UploadResponse interface (hosts_imported, jobs_imported, correlation_job_id, message); add CorrelationJobStatus type; add CorrelationJobResponse interface; update PendingMatchItem to include tier, matched_fields, ambiguity_group_id
- [X] T008 [P] Add API client functions in frontend/src/api/automations.ts — add getCorrelationJob(jobId: string) function calling GET /automations/correlation-jobs/{jobId}; update uploadMetrics return type to UploadResponse
- [X] T009 Add useCorrelationJob hook in frontend/src/hooks/useAutomation.ts — useQuery with 2-second refetchInterval while status is queued or running; disable refetch when completed or failed; accept onComplete callback
- [X] T010 Create CorrelationJobProgress component in frontend/src/components/automation/CorrelationJobProgress.tsx — accepts jobId prop; polls via useCorrelationJob hook; shows progress bar (progress/total), matched count, queued_for_review count, error count; transitions from loading → progress → complete/failed states; calls onComplete callback when done
- [X] T011 Integrate CorrelationJobProgress into upload flow in frontend/src/pages/AutomationUploadPage.tsx — after successful upload, show CorrelationJobProgress with returned correlation_job_id; on completion, invalidate automation queries and show summary

**Checkpoint**: Upload now returns immediately with job reference. UI shows correlation progress. Ready for user story implementation.

---

## Phase 3: User Story 1 — Hardware-Level Fact Correlation (Priority: P1) MVP

**Goal**: Upload AAP metrics with ansible_facts and correlate at Tier 1 (SMBIOS serial, 100%) and Tier 2 (BIOS UUID, 95%). Creates AUTOMATED_BY graph edges with confidence, tier, and matched_fields properties.

**Independent Test**: Upload AAP metrics for a host with ansible_product_serial matching a discovered vSphere VM's serialNumber in raw_properties. Verify AUTOMATED_BY edge created with confidence 1.0.

### Implementation for User Story 1

- [X] T012 [US1] Enhance ansible_facts extraction in backend/src/inventoryview/services/aap_import.py — during persist_import(), extract ansible_facts from metrics data and store in aap_host.ansible_facts JSONB column; parse ansible_product_serial, ansible_product_uuid from facts for quick access; handle missing/null facts gracefully
- [X] T013 [US1] Create fact extraction helpers in backend/src/inventoryview/services/aap_correlation.py — add extract_ansible_facts(host_row) function that reads ansible_facts JSONB and returns structured dict with serial, uuid, mac, ips, fqdn, hostname; add extract_resource_identifiers(resource_node) function that searches raw_properties for serialNumber, config.uuid, BIOS UUID, MAC, IP fields across vendor formats (vSphere, AWS, Azure); normalise all identifiers (lowercase, strip whitespace)
- [X] T014 [US1] Implement Tier 1 (SMBIOS serial) matcher in backend/src/inventoryview/services/aap_correlation.py — add _match_smbios_serial(host_facts, resource_ids) function; compare ansible_product_serial against resource serial numbers; return confidence=1.0, tier='smbios_serial', matched_fields list on match; return None on no match
- [X] T015 [US1] Implement Tier 2 (BIOS UUID) matcher in backend/src/inventoryview/services/aap_correlation.py — add _match_bios_uuid(host_facts, resource_ids) function; compare ansible_product_uuid against resource BIOS UUIDs; return confidence=0.95, tier='bios_uuid', matched_fields list on match
- [X] T016 [US1] Implement ambiguity detection in backend/src/inventoryview/services/aap_correlation.py — when a tier matcher finds multiple resources matching the same identifier (e.g. cloned VMs with same UUID), create pending_match entries for all candidates with shared ambiguity_group_id (UUID) instead of auto-matching; flag as ambiguous in job progress
- [X] T017 [US1] Implement localhost exclusion filter in backend/src/inventoryview/services/aap_correlation.py — add _is_localhost(host_row) function checking hostname against 'localhost', '127.0.0.1', '::1', and ansible_connection=='local' patterns; skip localhost hosts before any tier matching (FR-012)
- [X] T018 [US1] Refactor correlate_hosts() orchestrator in backend/src/inventoryview/services/aap_correlation.py — replace existing matching logic with tiered cascade: check exclusions first, then learned_mapping, then Tier 1 (serial), then Tier 2 (UUID); stop at first match; create AUTOMATED_BY edge via graph service with properties: confidence, tier, matched_fields (JSON), status='proposed' (or 'confirmed' for Tier 1), created_at, updated_at; report progress to job tracker after each host
- [X] T019 [US1] Implement correlation audit logging in backend/src/inventoryview/services/aap_correlation.py — add _log_audit(pool, action, aap_host_id, resource_uid, tier, confidence, matched_fields, previous_state, actor) function; insert into correlation_audit table; call on every auto_match, confirm, reject, dismiss action (FR-014)
- [X] T020 [US1] Update AUTOMATED_BY edge creation in backend/src/inventoryview/services/graph.py — enhance create_automated_by_edge() (or equivalent Cypher) to include properties: confidence (float), tier (string), matched_fields (string/JSON), status (string), created_at (ISO string), updated_at (ISO string), confirmed_by (string nullable); handle edge upsert (update if exists, create if not) to prevent duplicates on re-upload

**Checkpoint**: Hardware-level correlation works end-to-end. Upload AAP metrics → Tier 1/2 matching → AUTOMATED_BY edges with confidence scores. MVP complete.

---

## Phase 4: User Story 2 — Infrastructure-Level Fact Correlation (Priority: P2)

**Goal**: Extend correlation to Tier 3 (MAC address, 85%) and Tier 4 (IP address, 75%). Implement multi-tier reinforcement boost when multiple tiers match the same resource. Implement delta correlation on collection completion.

**Independent Test**: Upload AAP metrics for a host with ansible_default_ipv4.macaddress matching a discovered AWS instance MAC. Verify AUTOMATED_BY edge at confidence 0.85.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement Tier 3 (MAC address) matcher in backend/src/inventoryview/services/aap_correlation.py — add _match_mac_address(host_facts, resource_ids) function; compare ansible_default_ipv4.macaddress and ansible_interfaces MAC list against resource NIC MAC addresses; normalise MAC format (lowercase, colon-separated); return confidence=0.85, tier='mac_address', matched_fields on match
- [X] T022 [P] [US2] Implement Tier 4 (IP address) matcher in backend/src/inventoryview/services/aap_correlation.py — add _match_ip_address(host_facts, resource_ids) function; compare ansible_all_ipv4_addresses list against resource provider-reported IPs; return confidence=0.75, tier='ip_address', matched_fields on match
- [X] T023 [US2] Implement multi-tier reinforcement boost in backend/src/inventoryview/services/aap_correlation.py — add _calculate_boosted_confidence(matches: list[tuple[float, str]]) function; formula: max(confidences) + 0.15 * count(additional_matches), capped at next-higher tier base; integrate into correlate_hosts() after all tier checks complete — if multiple tiers matched the same resource, apply boost before deciding auto-match vs reconciliation
- [X] T024 [US2] Extend correlate_hosts() cascade with Tiers 3-4 in backend/src/inventoryview/services/aap_correlation.py — after Tier 2, try Tier 3 (MAC), then Tier 4 (IP); collect all matching tiers for boost calculation; apply boost formula; create edge with highest-confidence result
- [X] T025 [US2] Implement delta correlation trigger in backend/src/inventoryview/services/aap_correlation.py — add correlate_delta(pool, graph_name, collection_id_or_timestamp) function; query resources where last_seen > last_correlated_at (or last_correlated_at IS NULL); run correlation only against those resources and all existing AAP hosts; update last_correlated_at on processed resources
- [X] T026 [US2] Add delta correlation hook in backend/src/inventoryview/api/v1/automations.py — after collection completion events (if collection endpoint exists) or as a callable endpoint POST /automations/correlate-delta, trigger correlate_delta as background task; reuse job tracker for progress reporting

**Checkpoint**: Tiers 1-4 working. Multi-tier boost applied. Delta correlation on new collections.

---

## Phase 5: User Story 4 — Confidence Temperature Gauge (Priority: P2)

**Goal**: Visual temperature gauge showing correlation confidence per resource and aggregated across the fleet. Colour bands: hot/red (90-100%), warm/amber (70-89%), tepid/yellow (40-69%), cold/blue (0-39%).

**Independent Test**: View resource detail for a resource with an AUTOMATED_BY edge — temperature gauge shows correct colour and percentage.

### Implementation for User Story 4

- [X] T027 [P] [US4] Create GET /resources/{uid}/correlation endpoint in backend/src/inventoryview/api/v1/automations.py — query AUTOMATED_BY edge from graph for given resource_uid; return correlation detail (aap_host_id, hostname, confidence, tier, matched_fields, status, temperature band, confirmed_by, timestamps); return {is_correlated: false, correlation: null} if no edge exists
- [X] T028 [P] [US4] Create GET /automations/fleet-temperature endpoint in backend/src/inventoryview/api/v1/automations.py — query all AUTOMATED_BY edges; calculate weighted_average_confidence; compute tier_distribution and band_distribution counts; determine overall temperature band; return FleetTemperatureResponse
- [X] T029 [P] [US4] Add frontend API functions in frontend/src/api/automations.ts — add getResourceCorrelation(uid: string) and getFleetTemperature() functions
- [X] T030 [P] [US4] Add frontend hooks in frontend/src/hooks/useAutomation.ts — add useResourceCorrelation(uid: string) query hook; add useFleetTemperature() query hook
- [X] T031 [US4] Create TemperatureGauge component in frontend/src/components/automation/TemperatureGauge.tsx — accepts confidence (0-1), tier (optional), variant ('dot'|'bar'|'thermometer'), size ('sm'|'md'|'lg'); dot variant: 12px colour circle + percentage text for list views; bar variant: horizontal bar with colour fill for dashboard; thermometer variant: vertical gauge with gradient for resource detail; colour mapping: >=0.90 red (#ef4444), >=0.70 amber (#f59e0b), >=0.40 yellow (#eab308), <0.40 blue (#3b82f6); smooth CSS transitions between states
- [X] T032 [US4] Create FleetTemperature component in frontend/src/components/automation/FleetTemperature.tsx — uses useFleetTemperature hook; renders TemperatureGauge variant='bar' with weighted average; shows tier distribution breakdown; shows band distribution (hot/warm/tepid/cold counts); displays total correlated vs uncorrelated count
- [X] T033 [US4] Integrate temperature gauge into ResourceDetailPage in frontend/src/pages/ResourceDetailPage.tsx — add useResourceCorrelation(uid) hook call; if correlated, render TemperatureGauge variant='thermometer' in resource header area alongside existing automation badge; show tier name and matched fields detail below gauge
- [X] T034 [US4] Integrate fleet temperature into AutomationDashboardPage in frontend/src/pages/AutomationDashboardPage.tsx — add FleetTemperature component to dashboard summary section alongside existing coverage stats
- [X] T035 [US4] Add temperature dot to AutomationHistory component in frontend/src/components/automation/AutomationHistory.tsx — in Linked AAP Hosts section, show TemperatureGauge variant='dot' next to each host's correlation type badge displaying the confidence score

**Checkpoint**: Temperature gauge visible in resource detail, automation dashboard, and automation history. Fleet aggregate shows overall correlation health.

---

## Phase 6: User Story 3 — Weak Correlation and Reconciliation Queue (Priority: P3)

**Goal**: Tier 5 (FQDN, 50%) and Tier 6 (hostname heuristic, 30%) matching. Enhanced reconciliation queue with dismiss action, NOT_CORRELATED exclusion rules, and ambiguity group filtering.

**Independent Test**: Upload AAP metrics for host john.redhat.com where VM "john" exists with no hardware/network overlap. Match appears in reconciliation queue at 30% confidence.

### Implementation for User Story 3

- [X] T036 [P] [US3] Implement Tier 5 (FQDN) matcher in backend/src/inventoryview/services/aap_correlation.py — add _match_fqdn(host_facts, resource_ids) function; compare ansible_fqdn against resource FQDN from DNS/provider metadata; case-insensitive comparison; return confidence=0.50, tier='fqdn', matched_fields on match
- [X] T037 [P] [US3] Implement Tier 6 (hostname heuristic) matcher in backend/src/inventoryview/services/aap_correlation.py — add _match_hostname_heuristic(host_facts, resource_ids) function; normalise ansible_hostname by stripping domain suffixes; compare against resource name/display_name with same normalisation; return confidence=0.30, tier='hostname_heuristic', matched_fields on match
- [X] T038 [US3] Extend correlate_hosts() cascade with Tiers 5-6 in backend/src/inventoryview/services/aap_correlation.py — after Tier 4, try Tier 5 (FQDN) then Tier 6 (hostname); matches below configurable threshold (default 0.50) go to reconciliation queue as pending; unmatched hosts also go to reconciliation with status 'unmatched' and no proposed edge
- [X] T039 [US3] Implement exclusion rule checking in backend/src/inventoryview/services/aap_correlation.py — before attempting tier matching for a host, query correlation_exclusion table for any (aap_host_id, resource_uid) pairs; skip excluded resources during matching; add _check_exclusions(pool, aap_host_id, candidate_resource_uids) helper
- [X] T040 [US3] Implement confirmed match protection in backend/src/inventoryview/services/aap_correlation.py — before re-correlating a host, check if existing AUTOMATED_BY edge has status='confirmed' and confirmed_by is not null; if so, skip re-correlation unless explicitly triggered via re-correlate endpoint (FR-013)
- [X] T041 [US3] Create POST /automations/re-correlate endpoint in backend/src/inventoryview/api/v1/automations.py — accepts resource_uid; clears confirmed status on existing AUTOMATED_BY edge for that resource; triggers correlation as background task for that single resource against all AAP hosts; returns 202 with job reference
- [X] T042 [US3] Enhance POST /automations/review endpoint in backend/src/inventoryview/api/v1/automations.py — add 'dismiss' action type; on 'reject': create correlation_exclusion row with actor and optional reason, delete proposed edge, log audit; on 'dismiss': mark pending_match as dismissed without creating exclusion, log audit; on 'confirm': promote edge status to confirmed, set confirmed_by, persist learned mapping, log audit
- [X] T043 [US3] Enhance GET /automations/pending-matches endpoint in backend/src/inventoryview/api/v1/automations.py — add tier and ambiguity_group query parameters for filtering; include tier, matched_fields, ambiguity_group_id in response items
- [X] T044 [US3] Enhance AutomationReviewPage in frontend/src/pages/AutomationReviewPage.tsx — add tier badge column showing correlation tier name with colour coding; add "Dismiss" button alongside existing Approve/Reject; group ambiguous matches visually (matches sharing ambiguity_group_id shown in collapsible group with indicator); add tier filter dropdown; add matched_fields expandable detail row
- [X] T045 [US3] Add frontend types and API functions for exclusion and dismiss in frontend/src/api/types.ts and frontend/src/api/automations.ts — update ReviewAction to include 'dismiss' and optional reason; add reCorrelate(resourceUid: string) function

**Checkpoint**: Full 6-tier correlation working. Reconciliation queue handles weak matches. Exclusion rules prevent re-flagging. Manual re-correlation available.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, re-upload logic, seed data, performance validation.

- [X] T046 Implement re-upload upgrade logic in backend/src/inventoryview/services/aap_correlation.py — when AAP metrics are re-uploaded for an existing host with richer facts, re-run correlation; if new tier is stronger than existing, upgrade confidence and tier on AUTOMATED_BY edge; do not create duplicate edges; log audit with previous_state snapshot (SC-006)
- [X] T047 Implement stale edge handling in backend/src/inventoryview/services/aap_correlation.py — when a resource is deleted (detected via graph.py delete_resource_node), mark any AUTOMATED_BY edges pointing to it as stale by setting status='stale'; exclude stale edges from fleet-temperature calculations and active counts
- [X] T048 [P] Enhance seed_test_data.sh — add correlation test data: discovered VMs with SMBIOS serials and BIOS UUIDs in raw_properties; AAP metrics upload with ansible_facts containing matching serial, UUID, MAC, IP, and hostname-only hosts; include ambiguity case (two VMs with same UUID) and localhost entries
- [X] T049 [P] Add empty state handling in frontend/src/components/automation/TemperatureGauge.tsx — show "No correlation data" placeholder when no AAP metrics have been uploaded; show "Correlation in progress" when a job is running; handle null/undefined confidence gracefully
- [X] T050 Run quickstart.md validation — manually test all 7 integration scenarios from specs/008-aap-metrics-correlation/quickstart.md; verify SC-001 through SC-006 success criteria pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (migration must run first) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP target
- **US2 (Phase 4)**: Depends on Phase 3 (extends Tier 1-2 cascade with Tiers 3-4)
- **US4 (Phase 5)**: Depends on Phase 2 only (temperature gauge reads existing edges; can run in parallel with US2)
- **US3 (Phase 6)**: Depends on Phase 4 (extends Tier 1-4 cascade with Tiers 5-6, reconciliation queue needs all tiers)
- **Polish (Phase 7)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: After Foundational → independent, delivers MVP
- **US2 (P2)**: After US1 → extends tier cascade, adds boost formula
- **US4 (P2)**: After Foundational → independent of US2/US3, reads any existing edges
- **US3 (P3)**: After US2 → extends full cascade, reconciliation needs all tiers

### Within Each User Story

- Models/schemas before services
- Services before endpoints
- Backend endpoints before frontend integration
- Core matching before edge cases

### Parallel Opportunities

- T007, T008 (frontend types/API) run in parallel with T004, T005, T006 (backend foundational)
- T021, T022 (Tier 3, Tier 4 matchers) run in parallel within US2
- T027, T028, T029, T030 (US4 backend + frontend API) run in parallel
- T036, T037 (Tier 5, Tier 6 matchers) run in parallel within US3
- US4 (Phase 5) can run in parallel with US2 (Phase 4) since they don't share files
- T048, T049 (seed data, empty states) run in parallel in Polish phase

---

## Parallel Example: User Story 4

```bash
# Launch all backend + frontend API tasks together (different files):
Task T027: "Create GET /resources/{uid}/correlation endpoint"
Task T028: "Create GET /automations/fleet-temperature endpoint"
Task T029: "Add frontend API functions"
Task T030: "Add frontend hooks"

# Then sequentially:
Task T031: "Create TemperatureGauge component" (needs hooks from T030)
Task T032: "Create FleetTemperature component" (needs T030 + T031)
Task T033: "Integrate into ResourceDetailPage" (needs T031)
Task T034: "Integrate into AutomationDashboardPage" (needs T032)
Task T035: "Add dot to AutomationHistory" (needs T031)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration)
2. Complete Phase 2: Foundational (async jobs, upload flow)
3. Complete Phase 3: US1 — Hardware-Level Correlation
4. **STOP and VALIDATE**: Upload AAP metrics → Tier 1/2 matches → AUTOMATED_BY edges with confidence
5. Deploy/demo if ready — delivers the highest-value correlation accuracy

### Incremental Delivery

1. Phase 1 + 2 → Async upload infrastructure ready
2. + US1 (Phase 3) → Hardware-level correlation MVP
3. + US2 (Phase 4) → MAC/IP matching + boost formula
4. + US4 (Phase 5) → Temperature gauge visualization (can overlap with US2)
5. + US3 (Phase 6) → Weak matching + reconciliation queue enhancements
6. + Polish (Phase 7) → Edge cases, seed data, validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is an **enhancement** — most tasks modify existing files, not create new ones
- New files: correlation_jobs.py, TemperatureGauge.tsx, CorrelationJobProgress.tsx, FleetTemperature.tsx, Alembic migration
- match_score normalisation (100→1.0) affects existing data — migration must handle both old and new formats
- Existing learned_mapping logic preserved as Tier 0 (checked before Tier 1)
