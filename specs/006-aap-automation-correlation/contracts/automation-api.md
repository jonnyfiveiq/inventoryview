# API Contract: Automation Endpoints

**Feature**: 006-aap-automation-correlation
**Base path**: `/api/v1/automations`
**Date**: 2026-03-22

## Endpoints

### POST /api/v1/automations/upload

Upload an AAP metrics utility archive. Auto-correlates after successful parsing.

**Request**: `multipart/form-data`
- `file` (required): ZIP or tar.gz archive, max 200MB
- `source_label` (optional, string): Label for this import batch (default: filename)

**Response 200**:
```json
{
  "import_id": "uuid",
  "source_label": "metrics-2026-03.zip",
  "hosts_imported": 1500,
  "hosts_updated": 200,
  "jobs_imported": 8500,
  "events_counted": 45000,
  "indirect_nodes_imported": 120,
  "correlation_summary": {
    "auto_matched": 1200,
    "pending_review": 250,
    "unmatched": 50
  }
}
```

**Response 400**: Invalid file format or corrupt archive
**Response 413**: File exceeds 200MB limit

---

### GET /api/v1/automations/hosts

List AAP hosts with pagination and filtering.

**Query parameters**:
- `cursor` (optional, string): Pagination cursor
- `limit` (optional, int, default 50, max 200)
- `status` (optional): Filter by correlation_status: `auto_matched`, `manual_matched`, `pending`, `rejected`
- `search` (optional, string): Search by hostname

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "host_id": "42",
      "hostname": "webserver01.example.com",
      "smbios_uuid": "abc-123-def",
      "org_id": "1",
      "inventory_id": "5",
      "first_seen": "2025-06-15T10:30:00Z",
      "last_seen": "2026-03-20T14:00:00Z",
      "total_jobs": 85,
      "total_events": 1200,
      "correlation_type": "direct",
      "correlation_status": "auto_matched",
      "match_score": 98,
      "match_reason": "smbios_match",
      "correlated_resource": {
        "uid": "uuid",
        "name": "vm-web01",
        "vendor": "vmware",
        "normalised_type": "virtual_machine"
      }
    }
  ],
  "next_cursor": "eyJ...",
  "total_count": 1500
}
```

---

### GET /api/v1/automations/pending

List pending matches for admin review queue.

**Query parameters**:
- `cursor` (optional, string): Pagination cursor
- `limit` (optional, int, default 50, max 200)
- `min_score` (optional, int): Minimum match score filter
- `max_score` (optional, int): Maximum match score filter
- `sort` (optional): `score_desc` (default), `score_asc`, `hostname_asc`

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "aap_host": {
        "id": "uuid",
        "host_id": "42",
        "hostname": "john.redhat",
        "smbios_uuid": null,
        "total_jobs": 12
      },
      "suggested_resource": {
        "uid": "uuid",
        "name": "john-vm",
        "vendor": "vmware",
        "normalised_type": "virtual_machine"
      },
      "match_score": 65,
      "match_reason": "hostname_prefix",
      "status": "pending",
      "created_at": "2026-03-22T09:00:00Z"
    }
  ],
  "next_cursor": "eyJ...",
  "total_count": 250
}
```

---

### POST /api/v1/automations/pending/review

Approve, reject, or ignore pending matches. Supports bulk operations.

**Request**:
```json
{
  "actions": [
    {
      "pending_match_id": "uuid",
      "action": "approve",
      "override_resource_uid": null
    },
    {
      "pending_match_id": "uuid",
      "action": "approve",
      "override_resource_uid": "uuid-of-different-resource"
    },
    {
      "pending_match_id": "uuid",
      "action": "reject"
    },
    {
      "pending_match_id": "uuid",
      "action": "ignore"
    }
  ]
}
```

**Response 200**:
```json
{
  "processed": 4,
  "results": [
    { "pending_match_id": "uuid", "action": "approve", "success": true, "learned_mapping_created": true },
    { "pending_match_id": "uuid", "action": "approve", "success": true, "learned_mapping_created": true },
    { "pending_match_id": "uuid", "action": "reject", "success": true },
    { "pending_match_id": "uuid", "action": "ignore", "success": true }
  ]
}
```

---

### GET /api/v1/automations/coverage

Automation coverage statistics for dashboard.

**Query parameters**: None

**Response 200**:
```json
{
  "total_resources": 1000,
  "automated_resources": 300,
  "coverage_percentage": 30.0,
  "by_provider": [
    {
      "vendor": "vmware",
      "total": 500,
      "automated": 200,
      "coverage_percentage": 40.0
    },
    {
      "vendor": "aws",
      "total": 300,
      "automated": 80,
      "coverage_percentage": 26.7
    }
  ],
  "top_automated": [
    {
      "resource_uid": "uuid",
      "resource_name": "prod-db01",
      "vendor": "vmware",
      "total_jobs": 250,
      "last_automated": "2026-03-20T14:00:00Z"
    }
  ],
  "recent_imports": [
    {
      "source_label": "metrics-2026-03.zip",
      "imported_at": "2026-03-22T09:00:00Z",
      "hosts_count": 1500
    }
  ]
}
```

---

### GET /api/v1/automations/resources/{resource_uid}/history

Automation history for a specific resource.

**Path parameters**:
- `resource_uid` (UUID): The resource to query

**Query parameters**:
- `cursor` (optional, string): Pagination cursor
- `limit` (optional, int, default 20, max 100)

**Response 200**:
```json
{
  "resource_uid": "uuid",
  "first_automated": "2025-06-15T10:30:00Z",
  "last_automated": "2026-03-20T14:00:00Z",
  "total_jobs": 85,
  "aap_hosts": [
    {
      "hostname": "john.redhat.com",
      "correlation_type": "direct",
      "match_reason": "smbios_match"
    }
  ],
  "executions": {
    "items": [
      {
        "job_id": "1234",
        "job_name": "patch-webservers",
        "ok": 10,
        "changed": 3,
        "failures": 0,
        "dark": 0,
        "skipped": 2,
        "project": "infra-patching",
        "org_name": "Default",
        "correlation_type": "direct",
        "executed_at": "2026-03-20T14:00:00Z"
      }
    ],
    "next_cursor": "eyJ...",
    "total_count": 85
  }
}
```

---

### GET /api/v1/automations/reports/coverage

Generate exportable automation coverage report.

**Query parameters**:
- `format` (optional): `json` (default) or `csv`
- `vendor` (optional, string): Filter by vendor

**Response 200 (JSON)**:
```json
{
  "generated_at": "2026-03-22T10:00:00Z",
  "summary": {
    "total_resources": 1000,
    "automated_resources": 300,
    "coverage_percentage": 30.0,
    "deduplicated_note": "3 AAP hostnames resolved to 1 resource are counted once"
  },
  "automated": [
    {
      "resource_uid": "uuid",
      "resource_name": "vm-web01",
      "vendor": "vmware",
      "normalised_type": "virtual_machine",
      "first_automated": "2025-06-15T10:30:00Z",
      "last_automated": "2026-03-20T14:00:00Z",
      "total_jobs": 85,
      "aap_hostnames": ["john", "john.redhat", "john.redhat.com"]
    }
  ],
  "unautomated": [
    {
      "resource_uid": "uuid",
      "resource_name": "db-backup-03",
      "vendor": "aws",
      "normalised_type": "virtual_machine"
    }
  ]
}
```

**Response 200 (CSV)**: `Content-Type: text/csv`, `Content-Disposition: attachment; filename=automation-coverage-YYYY-MM-DD.csv`

---

### GET /api/v1/automations/graph/{resource_uid}

Get automation subgraph for a resource (for Cytoscape.js rendering).

**Path parameters**:
- `resource_uid` (UUID): The resource to query

**Response 200**:
```json
{
  "nodes": [
    {
      "id": "resource-uuid",
      "label": "vm-web01",
      "type": "Resource",
      "vendor": "vmware",
      "normalised_type": "virtual_machine"
    },
    {
      "id": "aaphost-uuid",
      "label": "john.redhat.com",
      "type": "AAPHost",
      "correlation_type": "direct",
      "total_jobs": 85
    }
  ],
  "edges": [
    {
      "source": "aaphost-uuid",
      "target": "resource-uuid",
      "type": "AUTOMATED_BY",
      "confidence": 0.98,
      "correlation_type": "direct",
      "inference_method": "smbios_match"
    }
  ]
}
```
