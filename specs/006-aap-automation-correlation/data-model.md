# Data Model: AAP Automation Correlation

**Feature**: 006-aap-automation-correlation
**Date**: 2026-03-22

## Graph Entities

### AAPHost (Graph Node)

Represents an AAP host imported from metrics utility data. Lives in Apache AGE graph.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| host_id | string | Yes | AAP host identifier (unique within org) |
| hostname | string | Yes | Display hostname from AAP |
| canonical_facts | string | No | Raw JSON from CSV canonical_facts field |
| smbios_uuid | string | No | Extracted from canonical_facts.ansible_machine_id |
| org_id | string | Yes | AAP organisation ID |
| inventory_id | string | Yes | AAP inventory ID |
| first_seen | string (ISO) | Yes | Earliest job execution date |
| last_seen | string (ISO) | Yes | Latest job execution date |
| total_jobs | integer | Yes | Aggregated job execution count |
| total_events | integer | Yes | Aggregated event count |
| correlation_type | string | Yes | "direct" or "indirect" |
| import_source | string | Yes | Label identifying the upload batch |

**Uniqueness**: `host_id` + `org_id` (composite). Re-imports update existing nodes.

### AUTOMATED_BY (Graph Edge: AAPHost → Resource)

Represents a confirmed correlation between an AAP host and an inventory resource.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| confidence | float | Yes | 0.0-1.0 normalised confidence |
| correlation_key | string | Yes | e.g., "smbios:abc-123" or "hostname:web01" |
| correlation_type | string | Yes | "direct" or "indirect" |
| inference_method | string | Yes | Strategy that produced match: "learned_mapping", "smbios_match", "exact_hostname", "ip_match", "hostname_prefix", "partial_match" |
| source_collector | string | Yes | Always "aap_metrics_import" |
| established_at | string (ISO) | Yes | When edge was created |
| last_confirmed | string (ISO) | Yes | When edge was last re-validated |

**Direction**: `(aaphost:AAPHost)-[:AUTOMATED_BY]->(r:Resource)` — the AAP host automates the resource.

## Relational Entities

### aap_host (Table)

Relational mirror of AAPHost graph nodes for efficient SQL queries (pagination, filtering, joins to job executions).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | gen_random_uuid() | Primary key |
| host_id | VARCHAR(255) | No | | AAP host identifier |
| hostname | VARCHAR(512) | No | | Display hostname |
| canonical_facts | JSONB | Yes | | Raw canonical_facts from CSV |
| smbios_uuid | VARCHAR(255) | Yes | | Extracted SMBIOS UUID |
| org_id | VARCHAR(255) | No | | AAP organisation ID |
| inventory_id | VARCHAR(255) | No | | AAP inventory ID |
| first_seen | TIMESTAMPTZ | No | | Earliest job date |
| last_seen | TIMESTAMPTZ | No | | Latest job date |
| total_jobs | INTEGER | No | 0 | Aggregated job count |
| total_events | INTEGER | No | 0 | Aggregated event count |
| correlation_type | VARCHAR(20) | No | 'direct' | "direct" or "indirect" |
| correlated_resource_uid | UUID | Yes | | Linked resource UID (null if pending/unmatched) |
| correlation_status | VARCHAR(20) | No | 'pending' | "auto_matched", "manual_matched", "pending", "rejected" |
| match_score | INTEGER | Yes | | 0-100 confidence score |
| match_reason | VARCHAR(255) | Yes | | Strategy that produced the match |
| import_source | VARCHAR(255) | No | | Upload batch label |
| created_at | TIMESTAMPTZ | No | now() | Row creation time |
| updated_at | TIMESTAMPTZ | No | now() | Last modification |

**Indexes**:
- UNIQUE on (host_id, org_id)
- INDEX on smbios_uuid
- INDEX on correlated_resource_uid
- INDEX on correlation_status
- INDEX on hostname

**Constraints**:
- CHECK correlation_status IN ('auto_matched', 'manual_matched', 'pending', 'rejected')
- CHECK correlation_type IN ('direct', 'indirect')

### aap_job_execution (Table)

Individual job execution records per host.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | gen_random_uuid() | Primary key |
| aap_host_id | UUID | No | | FK → aap_host.id |
| job_id | VARCHAR(255) | No | | AAP job identifier |
| job_name | VARCHAR(512) | No | | Job template name |
| ok | INTEGER | No | 0 | Success count |
| changed | INTEGER | No | 0 | Changed count |
| failures | INTEGER | No | 0 | Failure count |
| dark | INTEGER | No | 0 | Unreachable count |
| skipped | INTEGER | No | 0 | Skipped count |
| project | VARCHAR(512) | Yes | | AAP project name |
| org_name | VARCHAR(255) | Yes | | AAP organisation name |
| inventory_name | VARCHAR(255) | Yes | | AAP inventory name |
| executed_at | TIMESTAMPTZ | No | | Job execution timestamp |
| created_at | TIMESTAMPTZ | No | now() | Row creation time |

**Indexes**:
- UNIQUE on (aap_host_id, job_id)
- INDEX on executed_at
- INDEX on aap_host_id

**Constraints**:
- FK aap_host_id REFERENCES aap_host(id) ON DELETE CASCADE

### aap_pending_match (Table)

Pending correlations awaiting admin review.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | gen_random_uuid() | Primary key |
| aap_host_id | UUID | No | | FK → aap_host.id |
| suggested_resource_uid | UUID | Yes | | Best-guess resource UID |
| match_score | INTEGER | No | | 0-100 confidence |
| match_reason | VARCHAR(255) | No | | Strategy that produced the suggestion |
| status | VARCHAR(20) | No | 'pending' | "pending", "approved", "rejected", "ignored" |
| reviewed_by | UUID | Yes | | FK → administrators.id |
| reviewed_at | TIMESTAMPTZ | Yes | | When reviewed |
| override_resource_uid | UUID | Yes | | Admin-selected different resource |
| created_at | TIMESTAMPTZ | No | now() | Row creation time |

**Indexes**:
- INDEX on status
- INDEX on aap_host_id
- INDEX on match_score

**Constraints**:
- CHECK status IN ('pending', 'approved', 'rejected', 'ignored')
- FK aap_host_id REFERENCES aap_host(id) ON DELETE CASCADE

### aap_learned_mapping (Table)

Confirmed hostname-to-resource mappings that persist across imports.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | No | gen_random_uuid() | Primary key |
| hostname | VARCHAR(512) | No | | AAP hostname |
| resource_uid | UUID | No | | Mapped resource UID |
| org_id | VARCHAR(255) | No | | AAP organisation scope |
| source_label | VARCHAR(255) | No | | Import source scope |
| created_by | UUID | Yes | | FK → administrators.id |
| created_at | TIMESTAMPTZ | No | now() | When mapping was created |

**Indexes**:
- UNIQUE on (hostname, org_id, source_label)
- INDEX on resource_uid

## State Transitions

### aap_host.correlation_status

```
pending ──(auto-match score ≥80)──→ auto_matched
pending ──(admin approves)────────→ manual_matched
pending ──(admin rejects)─────────→ rejected
rejected ──(new import re-evaluates)──→ pending (only if new data changes match)
```

### aap_pending_match.status

```
pending ──(admin approves)──→ approved  (creates learned_mapping + AUTOMATED_BY edge)
pending ──(admin rejects)───→ rejected  (marks aap_host as rejected)
pending ──(admin ignores)───→ ignored   (skipped, re-evaluable on next import)
```

## Relationships Diagram

```
┌─────────────────────┐         ┌─────────────────────┐
│   AAPHost (graph)   │         │   Resource (graph)   │
│                     │─AUTOMATED_BY──→│                     │
│ host_id, hostname,  │         │ uid, name, vendor,   │
│ smbios_uuid, org_id │         │ normalised_type      │
└─────────────────────┘         └─────────────────────┘
         │                                │
    mirrors                          referenced by
         │                                │
         ▼                                ▼
┌─────────────────────┐         ┌─────────────────────┐
│  aap_host (table)   │←───FK───│ aap_pending_match   │
│                     │         │ (table)              │
│ correlated_resource │         └─────────────────────┘
│ _uid → Resource.uid │
└─────────────────────┘
         │
    FK (CASCADE)
         │
         ▼
┌─────────────────────┐         ┌─────────────────────┐
│ aap_job_execution   │         │ aap_learned_mapping  │
│ (table)             │         │ (table)              │
│                     │         │ hostname→resource_uid│
└─────────────────────┘         └─────────────────────┘
```
