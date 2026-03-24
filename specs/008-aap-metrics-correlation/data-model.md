# Data Model: AAP Metrics Correlation Engine

**Feature Branch**: `008-aap-metrics-correlation`
**Date**: 2026-03-23

## Entity Relationship Overview

```
AAPHost (relational)
  │
  ├── ansible_facts (JSONB)
  │     ├── ansible_product_serial
  │     ├── ansible_product_uuid
  │     ├── ansible_default_ipv4.macaddress
  │     ├── ansible_all_ipv4_addresses[]
  │     ├── ansible_fqdn
  │     └── ansible_hostname
  │
  ├──> AUTOMATED_BY edge (graph) ──> Resource (graph)
  │     ├── confidence (float 0-1)
  │     ├── tier (enum)
  │     ├── matched_fields (list)
  │     └── status (proposed|confirmed|rejected)
  │
  ├──> aap_pending_match (relational) ──> Resource
  │     ├── tier, matched_fields
  │     ├── status (pending|confirmed|rejected|dismissed)
  │     └── ambiguity_group_id (nullable)
  │
  └──> correlation_exclusion (relational) ──> Resource
        └── NOT_CORRELATED rule
```

## Entities

### AAPHost (existing table: `aap_host` — enhanced)

Represents an Ansible-managed host from uploaded metrics.

| Field | Type | Notes |
|-------|------|-------|
| id | serial PK | Existing |
| host_id | text | AAP host identifier |
| hostname | text | Hostname from AAP inventory |
| canonical_facts | jsonb | Existing — AAP canonical facts |
| **ansible_facts** | **jsonb** | **NEW — Full ansible_facts from metrics upload** |
| smbios_uuid | text | Existing — extracted from canonical_facts |
| org_id | text | AAP organization |
| inventory_id | text | AAP inventory |
| correlation_type | text | Match tier name (updated to E-01 tiers) |
| correlation_status | text | auto_matched / pending / confirmed / rejected |
| correlated_resource_uid | text | Matched resource UID |
| match_score | float | Normalised 0.0-1.0 (was integer 0-100) |
| match_reason | text | Human-readable match explanation |
| **last_correlated_at** | **timestamptz** | **NEW — When correlation last ran for this host** |
| total_jobs | integer | Existing |
| total_events | integer | Existing |
| first_seen | timestamptz | Existing |
| last_seen | timestamptz | Existing |
| created_at | timestamptz | Existing |
| updated_at | timestamptz | Existing |

**Validation rules**:
- `ansible_facts` may be null (hosts without facts correlate at Tier 5/6 only)
- `match_score` MUST be 0.0-1.0 (migration: divide existing scores by 100)
- `correlation_type` values: `smbios_serial`, `bios_uuid`, `mac_address`, `ip_address`, `fqdn`, `hostname_heuristic`, `learned_mapping`

### AUTOMATED_BY Edge (existing graph edge — enhanced)

Directed graph edge from AAPHost node to Resource node.

| Property | Type | Notes |
|----------|------|-------|
| confidence | float | 0.0-1.0 |
| **tier** | **string** | **NEW — smbios_serial\|bios_uuid\|mac_address\|ip_address\|fqdn\|hostname_heuristic\|learned_mapping** |
| **matched_fields** | **string** | **NEW — JSON array of {ansible_field, resource_field, value} tuples** |
| **status** | **string** | **NEW — proposed\|confirmed\|rejected** |
| created_at | string | ISO 8601 timestamp |
| **updated_at** | **string** | **NEW — Last modified timestamp** |
| **confirmed_by** | **string** | **NEW — Username if manually confirmed, null if auto** |

### ReconciliationItem (existing table: `aap_pending_match` — enhanced)

Queue entry for unresolved or low-confidence matches.

| Field | Type | Notes |
|-------|------|-------|
| id | serial PK | Existing |
| aap_host_id | integer FK | Existing |
| suggested_resource_uid | text | Existing |
| match_score | float | Normalised 0.0-1.0 |
| match_reason | text | Existing |
| **tier** | **text** | **NEW — Correlation tier that produced this match** |
| **matched_fields** | **jsonb** | **NEW — Field pairs that matched** |
| **ambiguity_group_id** | **uuid** | **NEW — Groups multiple candidates for same host** |
| status | text | Existing — add 'dismissed' value |
| reviewed_by | text | Existing |
| reviewed_at | timestamptz | Existing |
| override_resource_uid | text | Existing |
| created_at | timestamptz | Existing |

**State transitions**:
- `pending` → `confirmed` (operator approves)
- `pending` → `rejected` (operator rejects → creates exclusion rule)
- `pending` → `dismissed` (operator dismisses without creating exclusion)

### CorrelationExclusion (new table: `correlation_exclusion`)

Persisted NOT_CORRELATED rule preventing re-flagging.

| Field | Type | Notes |
|-------|------|-------|
| id | serial PK | |
| aap_host_id | integer FK | References aap_host.id |
| resource_uid | text | Excluded resource UID |
| created_by | text | Username of operator |
| reason | text | Optional explanation |
| created_at | timestamptz | |

**Uniqueness**: Composite unique on (aap_host_id, resource_uid).

### CorrelationAudit (new table: `correlation_audit`)

Audit log for all correlation actions (FR-014).

| Field | Type | Notes |
|-------|------|-------|
| id | serial PK | |
| action | text | auto_match, confirm, reject, dismiss, re_correlate |
| aap_host_id | integer FK | |
| resource_uid | text | |
| tier | text | Nullable (not applicable for reject/dismiss) |
| confidence | float | Nullable |
| matched_fields | jsonb | Nullable |
| previous_state | jsonb | Snapshot of prior correlation state |
| actor | text | 'system' for auto, username for manual |
| created_at | timestamptz | |

### CorrelationJob (in-memory only — not persisted)

Tracks background correlation job progress.

| Field | Type | Notes |
|-------|------|-------|
| job_id | uuid | Unique job identifier |
| status | enum | queued, running, completed, failed |
| progress | integer | Hosts processed so far |
| total | integer | Total hosts to process |
| matched | integer | Successful correlations |
| queued_for_review | integer | Items sent to reconciliation |
| errors | list[string] | Error messages |
| started_at | datetime | |
| completed_at | datetime | Nullable |

## Resource Table Enhancement (existing)

| Field | Type | Notes |
|-------|------|-------|
| **last_correlated_at** | **timestamptz** | **NEW — Added to resource graph node properties. Tracks when correlation last evaluated this resource. Used for delta correlation.** |

## Migration Notes

1. Add `ansible_facts` JSONB column to `aap_host` (nullable, default null)
2. Add `last_correlated_at` timestamptz column to `aap_host` (nullable)
3. Add `tier` and `matched_fields` columns to `aap_pending_match`
4. Add `ambiguity_group_id` UUID column to `aap_pending_match` (nullable)
5. Add 'dismissed' to allowed values for `aap_pending_match.status`
6. Create `correlation_exclusion` table with composite unique index
7. Create `correlation_audit` table
8. Migrate existing `match_score` from integer (0-100) to float (0.0-1.0): `UPDATE aap_host SET match_score = match_score / 100.0`
9. Migrate existing `correlation_type` values to E-01 tier names
10. Add `last_correlated_at` property to Resource graph nodes
