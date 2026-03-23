# Feature Specification: AAP Automation Correlation

**Feature Branch**: `006-aap-automation-correlation`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Upload AAP metrics utility data, correlate AAP hosts to inventory resources, deduplicate hostnames that resolve to the same machine, track automation history (first/last/all dates), surface automation coverage on dashboards, per resource, and per provider, and expose automation relationships in graph visualisations."

## User Scenarios & Testing

### User Story 1 — Upload AAP Metrics Data (Priority: P1)

An administrator navigates to a new "Automations" section in the sidebar and uploads a metrics utility archive file (ZIP or tar.gz) exported from Ansible Automation Platform. The system extracts the nested CSV files (host inventory, job summaries, job events, indirect managed nodes), parses them, and stores the raw AAP data in the database. The upload shows progress and a summary of what was imported (host count, job count, event count).

**Why this priority**: Without data ingestion, no other feature can function. This is the foundational data pipeline.

**Independent Test**: Upload a metrics utility ZIP file via the sidebar, verify the import summary shows correct counts, and confirm AAP host and job data is persisted.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the dashboard, **When** they click the "Automations" section in the sidebar and upload a valid metrics utility ZIP file, **Then** the system extracts all nested CSVs, parses the 2-line metadata headers, and displays an import summary showing hosts imported, jobs processed, and events counted.
2. **Given** a user uploads a tar.gz archive instead of ZIP, **Then** the system handles it identically, extracting and parsing the flat CSV contents.
3. **Given** a user uploads an invalid or corrupt file, **Then** the system displays a clear error message and does not create partial data.
4. **Given** a user uploads a file that overlaps with previously imported data, **Then** the system merges intelligently — updating existing hosts with new job/event data rather than creating duplicates.

---

### User Story 2 — Automatic Host-to-Resource Correlation (Priority: P1)

After metrics data is imported, the system automatically attempts to match each AAP host to an existing inventory resource using a cascading matching strategy: (1) learned/confirmed mappings from prior imports, (2) SMBIOS/machine_id UUID matching against resource canonical IDs and vendor identifiers, (3) exact hostname/FQDN matching, (4) IP address matching, (5) hostname prefix/FQDN short name matching. Matches above the confidence threshold (score >= 80) are auto-linked. Lower-confidence matches and unmatched hosts are queued for manual review.

**Why this priority**: Correlation is the core value proposition — connecting AAP automation data to real infrastructure resources. Without this, uploaded data has no context.

**Independent Test**: After importing AAP data, verify that high-confidence matches (e.g. SMBIOS UUID matches) create automation records automatically, and low-confidence matches appear in a review queue.

**Acceptance Scenarios**:

1. **Given** AAP host data has been imported and a host's SMBIOS UUID matches a resource's canonical ID, **When** correlation runs, **Then** an automation record is created automatically with confidence "exact" and correlation type "direct".
2. **Given** a host named "webserver01" exists in AAP and a resource with FQDN "webserver01.example.com" exists in inventory, **When** correlation runs, **Then** the system matches them via hostname prefix strategy and queues for review (score below auto-match threshold).
3. **Given** three AAP hostnames — "john", "john.redhat", "john.redhat.com" — all resolve to the same underlying machine (same SMBIOS UUID), **When** correlation runs, **Then** all three are linked to the single inventory resource, and the automation count for that resource reflects the deduplicated total.
4. **Given** an AAP host has no matching resource in inventory, **Then** it appears as an unmatched pending record for admin review.

---

### User Story 3 — Manual Match Review and Learned Mappings (Priority: P2)

Administrators can review pending (low-confidence or unmatched) correlations in a dedicated review interface. For each pending match, the system shows the AAP hostname, suggested candidate resource (if any), confidence score, and match reason. The admin can approve (linking the host to the suggested or a different resource), reject, or ignore. Approved matches create "learned mappings" so the same hostname auto-resolves in future imports without asking again.

**Why this priority**: Automated matching cannot achieve 100% accuracy. Manual review ensures all hosts are accounted for and builds the system's intelligence over time through learned mappings.

**Independent Test**: Navigate to the review queue, see pending matches with scores, approve one match, re-import the same data, and verify the previously-pending host now auto-matches.

**Acceptance Scenarios**:

1. **Given** a pending match with score 65 and suggested resource, **When** the admin approves it, **Then** an automation record is created and a learned mapping is stored for future imports.
2. **Given** a pending match with the wrong suggested resource, **When** the admin overrides with a different resource from a search/picker, **Then** the automation record links to the corrected resource and the learned mapping reflects the override.
3. **Given** a host the admin knows is irrelevant, **When** they reject it, **Then** it is marked as rejected and excluded from future review queues for this source.

---

### User Story 4 — Automation History Timeline (Priority: P2)

For each correlated resource, the system tracks a complete automation history: first automation date, last automation date, total job runs, and a chronological record of all job executions with job name, status (ok/changed/failures/dark/skipped), project, inventory, and organisation. Users can view this timeline on the resource detail page.

**Why this priority**: Tracking when and how often a resource has been automated is essential for reporting on automation coverage and audit trails.

**Independent Test**: Navigate to a resource that has correlated AAP data, verify the automation history section shows first/last dates, total job count, and a chronological list of job executions with status breakdowns.

**Acceptance Scenarios**:

1. **Given** a resource with 15 correlated job executions, **When** a user views the resource detail page, **Then** an "Automation History" section shows first automation date, last automation date, total jobs (15), and a paginated list of executions with job name, status, date, project, and organisation.
2. **Given** a resource with both direct and indirect automations, **Then** the history clearly labels each entry with its correlation type.

---

### User Story 5 — Automation Coverage Dashboard (Priority: P2)

The landing page and analytics page display automation coverage metrics: total resources, total automated resources, automation coverage percentage, breakdown by provider showing how many resources per vendor are automated vs. not. A dedicated "Automation" dashboard section or page shows top automated resources, unautomated resources, automation frequency distribution, and provider-level coverage donut charts.

**Why this priority**: The primary business driver — customers are billed on what is automated, not what exists. Stakeholders need at-a-glance visibility into automation coverage vs. total inventory to identify gaps and validate billing accuracy.

**Independent Test**: After importing AAP data and running correlation, navigate to the landing page and verify automation coverage percentages appear. Navigate to the analytics/automation dashboard and verify provider-level breakdowns and top automated resources are displayed.

**Acceptance Scenarios**:

1. **Given** 1000 inventory resources and 300 have automation records, **When** a user views the automation dashboard, **Then** it shows "300 / 1000 (30%) automated" with a provider breakdown showing each vendor's automated vs. total count.
2. **Given** automation data exists, **When** viewing the provider drill-down page, **Then** an "Automation Coverage" column or badge shows which resources have been automated and a summary count.
3. **Given** no AAP data has been imported, **Then** the automation sections show an empty state with guidance to upload metrics data.

---

### User Story 6 — Automation Relationships in Graph (Priority: P3)

When viewing a resource's graph visualisation, AAP automation relationships are rendered as additional nodes and edges. AAP hosts that are correlated to a resource appear as connected nodes (with a distinct visual style), and job templates that have run against the resource appear as automation relationship edges. Where multiple AAP hostnames resolve to the same resource (deduplication scenario), all hostnames are shown connected to the single resource node, making the FQDN resolution tree visible.

**Why this priority**: Graph visualisation is the project's core differentiator. Showing automation relationships alongside infrastructure topology creates the complete picture of "what is this resource, what does it connect to, and what automates it."

**Independent Test**: Navigate to a resource with AAP correlations, open the graph overlay, and verify AAP host nodes and automation edges appear with distinct styling. For deduplicated hosts, verify all hostname variants connect to the same resource node.

**Acceptance Scenarios**:

1. **Given** a VM resource with 3 correlated AAP hostnames (john, john.redhat, john.redhat.com) via the same SMBIOS UUID, **When** viewing the graph, **Then** all 3 AAP host nodes appear connected to the VM node with "AUTOMATED_BY" relationship edges, forming a visible hostname resolution tree.
2. **Given** a resource with indirect automation (cloud/API), **Then** the graph edge is styled distinctly from direct automation edges to indicate the different correlation type.

---

### User Story 7 — Automation Reports (Priority: P3)

Users can generate reports showing automation coverage: a list of all automated resources with their automation dates, job counts, and provider; a list of unautomated resources; and a deduplicated count ensuring that multiple AAP hostnames resolving to the same machine are counted only once. Reports are viewable in the UI and exportable.

**Why this priority**: Accurate reporting is critical for billing validation. The deduplication problem (multiple hostnames = one machine) is the core challenge this feature solves.

**Independent Test**: Generate an automation coverage report, verify the total automated count is deduplicated (3 hostnames resolving to 1 machine = 1 automated resource, not 3), and export the report.

**Acceptance Scenarios**:

1. **Given** 3 AAP hostnames all correlated to the same resource, **When** generating an automation report, **Then** that resource is counted exactly once in the "automated resources" total.
2. **Given** a user requests an automation coverage report, **Then** the report shows: total resources, total automated (deduplicated), coverage percentage, and per-provider breakdown.
3. **Given** a user exports the report, **Then** it downloads in a consumable format with all fields included.

---

### Edge Cases

- What happens when a metrics utility file contains no valid CSV data? System shows an error with specifics about what was expected vs. found.
- What happens when the same file is uploaded twice? System detects overlap by checking AAP host IDs and job IDs, merges new data without duplicating existing records.
- What happens when an AAP host matches multiple inventory resources with equal confidence? System creates a pending match for each candidate and lets the admin choose.
- What happens when a previously-correlated resource is deleted from inventory? The automation record is orphaned gracefully — it remains for historical reporting but is flagged as "resource removed."
- What happens when a learned mapping references a resource that no longer exists? The learned mapping is skipped during import and the host falls back to the standard matching cascade.
- How are indirect managed nodes (cloud/API targets) handled differently? They use a separate matching strategy: VMware moid matching, Azure resource ID matching, or generic hostname matching with correlation type "indirect."

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept metrics utility archive uploads (ZIP and tar.gz formats, max 200MB) containing AAP CSV data via a file upload interface in the sidebar navigation. Correlation MUST run automatically upon successful upload completion.
- **FR-002**: System MUST parse the 4 CSV types from metrics utility exports: main_host (host inventory with canonical_facts and SMBIOS UUIDs), job_host_summary (per-job execution results), main_jobevent (task-level events), and main_indirectmanagednodeaudit (cloud/API managed nodes).
- **FR-003**: System MUST strip the 2-line metadata header from each CSV before parsing the actual data rows.
- **FR-004**: System MUST automatically correlate AAP hosts to inventory resources using a cascading matching strategy with at least 5 tiers: learned mappings, SMBIOS/hardware ID, exact hostname/FQDN, IP address, and hostname prefix/partial matching.
- **FR-005**: System MUST assign confidence scores to each match and auto-link matches scoring 80 or above.
- **FR-006**: System MUST queue matches scoring below 80 as pending for admin review.
- **FR-007**: System MUST deduplicate AAP hostnames that resolve to the same underlying machine (via shared SMBIOS UUID or learned mapping) so that one physical/virtual machine is counted once regardless of how many hostname variants appear in AAP.
- **FR-008**: System MUST provide a review interface for pending matches showing AAP hostname, suggested resource, confidence score, and match reason, with approve/reject/ignore actions. The interface MUST support bulk approve/reject with select-all and filter-by-confidence-score capabilities.
- **FR-009**: System MUST store approved matches as learned mappings that persist across future imports, enabling automatic resolution of previously-ambiguous hosts.
- **FR-010**: System MUST track automation history per resource: first automation date, last automation date, total job count, and individual job execution records with name, status, project, inventory, and organisation.
- **FR-011**: System MUST differentiate between direct automations (SSH/WinRM host-level) and indirect automations (cloud/API-managed) with separate correlation types.
- **FR-012**: System MUST display automation coverage metrics on the landing page and analytics page: total automated resources (deduplicated), coverage percentage, and per-provider breakdown.
- **FR-013**: System MUST show automation history on individual resource detail pages.
- **FR-014**: System MUST model AAP hosts as graph nodes (label: `AAPHost`) with `AUTOMATED_BY` edges to `Resource` nodes, and render these in the graph visualisation with distinct node types and edge styles.
- **FR-015**: System MUST show the hostname resolution tree in graph view when multiple AAP hostnames are correlated to a single resource.
- **FR-016**: System MUST support generating automation coverage reports with deduplicated counts and per-provider breakdowns.
- **FR-017**: System MUST handle re-imports gracefully by merging new data with existing records (no duplicates for the same host/job combinations).
- **FR-018**: System MUST show automation coverage indicators on the provider drill-down page for each resource.

### Key Entities

- **AAP Host**: A host record from the metrics utility export, identified by host_id with hostname, canonical_facts (SMBIOS UUID), organisation, inventory, and aggregated automation metrics (first_seen, last_seen, total_events, total_jobs).
- **AAP Job Execution**: A record of a specific job template execution against a host, with job name, status breakdown (ok/changed/failures/dark/skipped), project, organisation, and timestamps.
- **Automation Record**: The correlated link between an AAP host and an inventory resource, storing correlation type (direct/indirect), correlation key (smbios:uuid or hostname:name), confidence level (exact/probable), and full automation details.
- **Pending Match**: An uncertain correlation awaiting admin review, with AAP host data, suggested candidate resource, match score, match reason, and raw metrics data.
- **Learned Mapping**: A confirmed host-to-resource mapping that persists across imports, scoped by AAP hostname, source label, and organisation.
- **Indirect Managed Node**: A cloud/API-managed resource from AAP (e.g., VMware VM managed via vCenter API, Azure resource via Azure RM), with separate matching logic using vendor-specific identifiers (moid, Azure resource ID).

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can upload a metrics utility file and see import results within 30 seconds for files containing up to 10,000 hosts.
- **SC-002**: High-confidence correlations (SMBIOS UUID match, exact hostname match) achieve 95%+ accuracy requiring no manual intervention.
- **SC-003**: The deduplication count is provably accurate — 3 AAP hostnames resolving to 1 machine always equals 1 in coverage reports, not 3.
- **SC-004**: Automation coverage dashboard loads within 2 seconds and shows accurate percentages across all providers.
- **SC-005**: Learned mappings reduce the manual review queue by at least 50% on the second import from the same source.
- **SC-006**: Graph visualisation renders AAP automation relationships alongside infrastructure topology without performance degradation for resources with up to 50 correlated automation nodes.
- **SC-007**: Users can identify the full automation trail for any resource in the inventory within 3 clicks from the landing page.

## Clarifications

### Session 2026-03-22

- Q: How should AAP host data be modelled in the graph? → A: Hybrid — AAP hosts become graph nodes (label: `AAPHost`) with `AUTOMATED_BY` edges to `Resource` nodes. Job executions and learned mappings are stored in relational tables.
- Q: Should correlation run automatically after upload or on-demand? → A: Auto-correlate immediately after upload completes. 200MB file size limit.
- Q: Should the review queue support bulk actions? → A: Yes — bulk approve/reject with select-all and filter-by-confidence-score, plus individual actions.

## Assumptions

- The metrics utility file format follows the standard AAP metrics-utility export structure with ZIP or tar.gz archives containing CSV files in the `data/YYYY/MM/DD/` directory hierarchy.
- Each CSV has a 2-line metadata header (collection metadata) before the actual data header row.
- The `canonical_facts` field in host CSVs is a JSON string containing `ansible_machine_id` (SMBIOS UUID) when available.
- Resources in the inventory already have `canonical_id` and/or vendor-specific identifiers populated during collection.
- The auto-match confidence threshold of 80 (on a 0-100 scale) provides a reasonable balance between automation and accuracy.
- File uploads are limited to authenticated administrators.
- Report export format will be CSV by default (consistent with the input format).
