# Feature Specification: AAP Metrics Correlation Engine

**Feature Branch**: `008-aap-metrics-correlation`
**Created**: 2026-03-23
**Status**: Draft
**Input**: Enhancement Proposal E-01 from InventoryView Enhancement Proposals v1.3

## Clarifications

### Session 2026-03-23

- Q: Should correlation run synchronously during upload or as a background job? → A: Asynchronous — upload returns immediately, correlation runs as background job with progress indicator.
- Q: Who can resolve reconciliation queue items? → A: Any authenticated user (RBAC deferred to E-12).
- Q: On collection completion, does correlation re-run against all resources or only changed ones? → A: Delta only — re-correlate only against resources created or updated in the latest collection.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Hardware-Level Fact Correlation (Priority: P1)

As an operator, I upload AAP metrics containing Ansible host facts and the system automatically correlates each AAP host to a discovered resource using hardware identifiers (SMBIOS serial, BIOS UUID) from ansible_facts, creating AUTOMATED_BY edges in the graph with 100% or 95% confidence.

**Why this priority**: Hardware-level matching is the most reliable correlation strategy and eliminates the primary source of miscounted nodes. Without this, all other tiers are weaker approximations.

**Independent Test**: Can be fully tested by uploading AAP metrics for a host with ansible_product_serial set, where a discovered vSphere VM has the matching serial in raw_properties. Delivers deterministic 1:1 correlation.

**Acceptance Scenarios**:

1. **Given** a discovered vSphere VM with SMBIOS serial `VMware-42-16-a8` in raw_properties and AAP metrics containing a host with `ansible_product_serial: VMware-42-16-a8`, **When** the correlation engine runs, **Then** an AUTOMATED_BY edge is created between the AAP host and the discovered VM with confidence 1.0, tier: smbios_serial
2. **Given** a discovered VM with BIOS UUID `abc-123-def` and AAP metrics containing a host with `ansible_product_uuid: abc-123-def` but no matching serial, **When** the correlation engine runs, **Then** an AUTOMATED_BY edge is created with confidence 0.95, tier: bios_uuid
3. **Given** a discovered VM with BIOS UUID `abc-123-def` and two AAP hosts both reporting `ansible_product_uuid: abc-123-def` (cloned VMs), **When** the correlation engine runs, **Then** the system flags a one-to-many ambiguity and places both matches in the reconciliation queue rather than silently picking one

---

### User Story 2 — Infrastructure-Level Fact Correlation (Priority: P2)

As an operator, when hardware identifiers are not available in ansible_facts, the system falls back to infrastructure-level matching using MAC addresses and IP addresses from ansible_facts, correlating against provider-discovered NIC and IP metadata with reduced but substantial confidence.

**Why this priority**: Many hosts do not expose SMBIOS serial via facts (e.g. cloud instances, containers). MAC and IP matching covers the next tier of reliable correlation.

**Independent Test**: Can be tested by uploading AAP metrics for a host with ansible_default_ipv4 containing a MAC and IP that match a discovered AWS instance. Delivers high-confidence correlation without hardware serial.

**Acceptance Scenarios**:

1. **Given** a discovered AWS instance with MAC `0a:1b:2c:3d:4e:5f` and AAP metrics with `ansible_default_ipv4.macaddress: 0a:1b:2c:3d:4e:5f`, **When** the correlation engine runs and no Tier 1 or 2 match exists, **Then** an AUTOMATED_BY edge is created with confidence 0.85, tier: mac_address
2. **Given** a discovered VM with IP `10.0.1.42` and AAP metrics with `ansible_all_ipv4_addresses` containing `10.0.1.42`, **When** the correlation engine runs and no Tier 1, 2, or 3 match exists, **Then** an AUTOMATED_BY edge is created with confidence 0.75, tier: ip_address
3. **Given** a discovered VM with IP `10.0.1.42` and AAP metrics with both matching IP and matching normalised hostname, **When** the correlation engine runs, **Then** confidence is boosted above either individual tier (e.g. 0.90) due to multi-tier reinforcement

---

### User Story 3 — Weak Correlation and Reconciliation Queue (Priority: P3)

As an operator, when only hostname or FQDN information is available in ansible_facts, the system attempts name-based correlation at reduced confidence and surfaces weak or unresolved matches in a reconciliation queue where I can manually confirm or reject proposed links.

**Why this priority**: Name-based matching catches resources that lack rich facts but is inherently unreliable. The reconciliation queue ensures weak matches are never silently accepted.

**Independent Test**: Can be tested by uploading AAP metrics for host `john.redhat.com` where a discovered VM named `john` exists but shares no hardware or network identifiers. The match appears in the reconciliation queue.

**Acceptance Scenarios**:

1. **Given** a discovered VM named `john` and AAP metrics for host `john.redhat.com` with no matching hardware, MAC, or IP identifiers, **When** the correlation engine runs, **Then** a proposed AUTOMATED_BY edge is created with confidence 0.30, tier: hostname_heuristic, and the match is placed in the reconciliation queue
2. **Given** a proposed match in the reconciliation queue, **When** the operator clicks Confirm, **Then** the AUTOMATED_BY edge is promoted to status: confirmed and removed from the queue
3. **Given** a proposed match in the reconciliation queue, **When** the operator clicks Reject, **Then** the proposed edge is deleted, the pair is recorded as a NOT_CORRELATED exclusion, and the AAP host remains unmatched
4. **Given** AAP metrics are uploaded and 3 hosts have no match at any tier, **When** the correlation engine completes, **Then** all 3 unmatched hosts appear in the reconciliation queue with status: unmatched and no proposed edge

---

### User Story 4 — Confidence Temperature Gauge (Priority: P2)

As an operator, I can see a temperature gauge on each correlated resource showing how confident the match is, ranging from cold/blue (hostname heuristic) through warm/amber (IP/MAC) to hot/red (hardware serial), plus an aggregate fleet gauge on the dashboard.

**Why this priority**: Confidence visibility is essential for operators to know whether they can trust a correlation or need to investigate. Without it, all matches look equal regardless of quality.

**Independent Test**: Can be tested by correlating resources at different tiers and verifying each displays the correct temperature colour and confidence percentage in the resource detail view.

**Acceptance Scenarios**:

1. **Given** a resource with an AUTOMATED_BY edge at confidence 1.0 (tier: smbios_serial), **When** the operator views the resource detail, **Then** a temperature gauge displays in the hot/red band with "100%" label
2. **Given** a resource with an AUTOMATED_BY edge at confidence 0.75 (tier: ip_address), **When** the operator views the resource detail, **Then** a temperature gauge displays in the warm/amber band with "75%" label
3. **Given** a fleet of 100 correlated resources with mixed confidence tiers, **When** the operator views the dashboard, **Then** an aggregate fleet temperature gauge shows the weighted average confidence across all correlated resources

---

### Edge Cases

- What happens when an AAP host's ansible_product_serial matches two discovered resources with the same serial (cloned VMs that were not re-sysprep'd)? System MUST flag as ambiguous and queue for manual resolution rather than picking one.
- What happens when AAP metrics are re-uploaded with updated facts for a host that already has a confirmed correlation? System MUST re-evaluate the correlation and update confidence/tier if a stronger match is now available, but MUST NOT downgrade a manually confirmed match.
- What happens when a discovered resource is deleted or decommissioned after an AUTOMATED_BY edge was created? The edge MUST be marked as stale and excluded from active counts, but preserved for audit.
- What happens when ansible_facts are empty or minimal (e.g. a network device with only ansible_hostname)? System MUST still attempt correlation at available tiers and clearly indicate in the UI that fact richness is low.
- How does the system handle AAP metrics for hosts using ansible_connection: local (localhost entries)? System MUST exclude localhost/127.0.0.1 entries from correlation to avoid false matches.
- What happens when the same AAP host matches multiple discovered resources at the same tier with equal confidence? System MUST place all candidates in the reconciliation queue as an ambiguous match group.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compare uploaded AAP host facts against discovered resource raw_properties using a six-tier correlation hierarchy: SMBIOS serial, BIOS UUID, MAC address, IP address, FQDN, normalised hostname.
- **FR-002**: System MUST walk the tier hierarchy from strongest (Tier 1) to weakest (Tier 6), stopping at the first match found.
- **FR-003**: System MUST assign a confidence score (0.0-1.0) to each correlation based on the matching tier.
- **FR-004**: System MUST boost confidence when multiple tiers match the same resource (e.g. IP + hostname > IP alone).
- **FR-005**: System MUST persist each correlation as an AUTOMATED_BY graph edge with properties: confidence, tier, matched_fields, timestamp, status (proposed|confirmed|rejected).
- **FR-006**: System MUST surface unmatched AAP hosts and low-confidence matches (below configurable threshold, default 0.50) in a reconciliation queue.
- **FR-007**: System MUST allow any authenticated user to Confirm, Reject, or Dismiss proposed matches from the reconciliation queue. Role-based access restrictions are deferred to E-12 (RBAC and Multi-Tenancy).
- **FR-008**: System MUST persist NOT_CORRELATED exclusion rules when an operator rejects a proposed match, preventing re-flagging on subsequent uploads.
- **FR-009**: System MUST display a per-resource temperature gauge in resource detail and list views showing correlation confidence as a colour-coded indicator (hot/red >= 90%, warm/amber 70-89%, tepid/yellow 40-69%, cold/blue < 40%).
- **FR-010**: System MUST display an aggregate fleet temperature gauge on the dashboard showing weighted average confidence across all correlated resources.
- **FR-011**: System MUST re-run correlation when new AAP metrics are uploaded or new collections complete, updating edges where stronger matches become available. Correlation MUST run asynchronously as a background job; the upload response MUST return immediately with a job reference. The UI MUST display a progress indicator while correlation is in progress. On collection completion, correlation MUST target only resources created or updated in that collection run (delta), not the full resource set.
- **FR-012**: System MUST NOT create AUTOMATED_BY edges for localhost, 127.0.0.1, or ::1 entries in AAP metrics.
- **FR-013**: System MUST NOT overwrite a manually confirmed correlation with an automated re-evaluation unless the operator explicitly triggers a re-correlation for that resource.
- **FR-014**: System MUST log all correlation actions (auto-match, confirm, reject, dismiss) with timestamp, operator (if manual), matched fields, and previous state for audit.

### Correlation Tier Reference

| Tier | Match Strategy | Confidence | Ansible Fact | Provider Source |
|------|---------------|------------|-------------|----------------|
| 1 | SMBIOS Serial Number | 100% | ansible_product_serial | vSphere systemInfo.serialNumber, AWS dmi serial, BMC serial |
| 2 | BIOS UUID | 95% | ansible_product_uuid | vSphere vm.config.uuid, Hyper-V BIOSGUID, AWS instance-id |
| 3 | MAC Address | 85% | ansible_default_ipv4.macaddress | vSphere NIC hw address, AWS MAC, Azure NIC MAC |
| 4 | IP Address | 75% | ansible_all_ipv4_addresses | Provider-reported IPs, elastic IPs, private IPs |
| 5 | FQDN | 50% | ansible_fqdn | Resource FQDN from DNS / provider metadata |
| 6 | Hostname Heuristic | 30% | ansible_hostname (normalised) | Resource name / display name (normalised) |

### Confidence Temperature Gauge Reference

| Temperature | Colour | Confidence Range | Meaning |
|-------------|--------|-----------------|---------|
| Hot | Red | 90-100% | Hardware-level match (serial, BIOS UUID). Deterministic. No human review needed. |
| Warm | Amber | 70-89% | Infrastructure-level match (MAC, IP address). High confidence but should be validated if IP is DHCP or NIC was replaced. |
| Tepid | Yellow | 40-69% | Name-based match (FQDN). Reasonable but not deterministic. Manual review recommended. |
| Cold | Blue | 0-39% | Heuristic match (hostname normalisation). Weak correlation. Flagged in reconciliation queue for manual confirmation. |

### Key Entities

- **CorrelationEdge (AUTOMATED_BY)**: Directed graph edge from discovered Resource to AAP Host. Properties: confidence (float 0-1), tier (enum: smbios_serial|bios_uuid|mac_address|ip_address|fqdn|hostname_heuristic), matched_fields (list of field pairs), status (proposed|confirmed|rejected), created_at, updated_at, confirmed_by (operator, nullable).
- **AAPHost**: Represents an Ansible-managed host from uploaded metrics. Properties: hostname, ansible_facts (structured data), inventory_source, last_job_id, last_job_timestamp. Linked to CorrelationEdge.
- **ReconciliationItem**: Queue entry for unresolved or low-confidence matches. Properties: aap_host_id, candidate_resource_ids (list), proposed_tier, proposed_confidence, status (pending|confirmed|rejected|dismissed), resolved_by, resolved_at.
- **ExclusionRule (NOT_CORRELATED)**: Persisted rule preventing a specific AAP host and resource pair from being re-proposed. Properties: aap_host_id, resource_id, created_by, created_at, reason (optional).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tier 1 (SMBIOS serial) and Tier 2 (BIOS UUID) matches produce zero false positives across a test set of 500 resources with known ground truth.
- **SC-002**: Correlation engine processes 1,000 AAP hosts against 5,000 discovered resources in under 30 seconds.
- **SC-003**: 90% of AAP hosts are automatically correlated at Tier 1-4 without requiring manual reconciliation in a typical enterprise VMware + AWS environment.
- **SC-004**: Operators can resolve a reconciliation queue item (confirm/reject) in under 3 clicks and 10 seconds.
- **SC-005**: Temperature gauge is visible and accurate within 1 second of page load for any resource with an AUTOMATED_BY edge.
- **SC-006**: Re-upload of AAP metrics with updated facts correctly upgrades correlation tier and confidence without creating duplicate edges.

## Assumptions

- AAP metrics uploads include ansible_facts for each host. Hosts without facts can only be correlated at Tier 5 or 6.
- Provider plugins (vSphere, AWS, Azure) already expose hardware identifiers (serial, UUID, MAC, IP) in raw_properties. Any provider that does not will require plugin enhancement.
- The existing graph database (PostgreSQL + Apache AGE) supports the required Cypher queries for multi-property matching across node types.
- The reconciliation queue is a UI feature within the existing frontend. No separate microservice is required.
- Localhost entries (127.0.0.1, ::1) in AAP metrics are never valid correlation targets.
