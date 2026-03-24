# API Contracts: AAP Metrics Correlation Engine

**Feature Branch**: `008-aap-metrics-correlation`
**Base Path**: `/api/v1`

## Enhanced Endpoints (existing)

### POST /automations/upload

Upload AAP metrics archive. **Enhanced**: Returns immediately with job reference instead of blocking until correlation completes.

**Request**: `multipart/form-data` with `file` field (ZIP or tar.gz) — unchanged.

**Response** (changed from current):
```json
{
  "hosts_imported": 142,
  "jobs_imported": 1893,
  "correlation_job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Import complete. Correlation running in background."
}
```

**Status codes**: 202 Accepted (was 200), 400 Bad Request, 401 Unauthorized

### GET /automations/pending-matches

List reconciliation queue items. **Enhanced**: Adds `tier`, `matched_fields`, `ambiguity_group_id` to response items.

**Query parameters** (existing + new):
- `status` — filter by status (pending|confirmed|rejected|dismissed)
- `min_score` — minimum confidence (float 0.0-1.0)
- `max_score` — maximum confidence (float 0.0-1.0)
- **`tier`** — NEW: filter by correlation tier
- **`ambiguity_group`** — NEW: filter by ambiguity group UUID
- `cursor` — pagination cursor
- `page_size` — default 50

**Response item** (enhanced):
```json
{
  "id": 42,
  "aap_host": {
    "id": 7,
    "hostname": "john.redhat.com",
    "smbios_uuid": null,
    "total_jobs": 15
  },
  "suggested_resource": {
    "uid": "res-abc-123",
    "name": "john",
    "vendor": "vmware",
    "normalised_type": "virtual_machine"
  },
  "match_score": 0.30,
  "match_reason": "Hostname heuristic: john.redhat.com → john",
  "tier": "hostname_heuristic",
  "matched_fields": [
    {"ansible_field": "ansible_hostname", "resource_field": "name", "values": ["john", "john"]}
  ],
  "ambiguity_group_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "created_at": "2026-03-23T10:00:00Z"
}
```

### POST /automations/review

Process review actions. **Enhanced**: Adds `dismiss` action and exclusion rule creation on reject.

**Request body** (enhanced):
```json
{
  "actions": [
    {
      "pending_match_id": 42,
      "action": "confirm",
      "override_resource_uid": null
    },
    {
      "pending_match_id": 43,
      "action": "reject",
      "reason": "Different machine with same hostname"
    },
    {
      "pending_match_id": 44,
      "action": "dismiss"
    }
  ]
}
```

**Actions**:
- `confirm` — Creates/promotes AUTOMATED_BY edge, persists learned mapping, logs audit
- `reject` — Deletes proposed edge, creates correlation_exclusion rule, logs audit
- `dismiss` — Marks as dismissed without creating exclusion rule, logs audit
- `ignore` — Existing action, kept for backward compatibility (alias for dismiss)

**Response**:
```json
{
  "processed": 3,
  "confirmed": 1,
  "rejected": 1,
  "dismissed": 1,
  "errors": []
}
```

## New Endpoints

### GET /automations/correlation-jobs/{job_id}

Poll background correlation job status.

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 87,
  "total": 142,
  "matched": 65,
  "queued_for_review": 12,
  "errors": [],
  "started_at": "2026-03-23T10:00:00Z",
  "completed_at": null
}
```

**Status values**: `queued`, `running`, `completed`, `failed`

**Status codes**: 200 OK, 404 Not Found (unknown job_id)

### GET /automations/fleet-temperature

Aggregate fleet correlation health.

**Response**:
```json
{
  "total_correlated": 450,
  "total_aap_hosts": 500,
  "uncorrelated": 50,
  "weighted_average_confidence": 0.82,
  "temperature": "warm",
  "tier_distribution": {
    "smbios_serial": 120,
    "bios_uuid": 80,
    "mac_address": 95,
    "ip_address": 85,
    "fqdn": 40,
    "hostname_heuristic": 30
  },
  "band_distribution": {
    "hot": 200,
    "warm": 180,
    "tepid": 40,
    "cold": 30
  }
}
```

### GET /resources/{uid}/correlation

Per-resource correlation detail (temperature gauge data).

**Response** (correlated resource):
```json
{
  "resource_uid": "res-abc-123",
  "is_correlated": true,
  "correlation": {
    "aap_host_id": 7,
    "aap_hostname": "john.redhat.com",
    "confidence": 1.0,
    "tier": "smbios_serial",
    "matched_fields": [
      {"ansible_field": "ansible_product_serial", "resource_field": "raw_properties.serialNumber", "values": ["VMware-42-16-a8", "VMware-42-16-a8"]}
    ],
    "status": "confirmed",
    "temperature": "hot",
    "confirmed_by": "admin",
    "created_at": "2026-03-23T10:00:00Z",
    "updated_at": "2026-03-23T10:05:00Z"
  }
}
```

**Response** (uncorrelated resource):
```json
{
  "resource_uid": "res-xyz-789",
  "is_correlated": false,
  "correlation": null
}
```

### POST /automations/re-correlate

Trigger manual re-correlation for a specific resource (FR-013 override).

**Request body**:
```json
{
  "resource_uid": "res-abc-123"
}
```

**Response**:
```json
{
  "correlation_job_id": "770e8400-e29b-41d4-a716-446655440002",
  "message": "Re-correlation triggered for res-abc-123"
}
```

**Status codes**: 202 Accepted, 404 Not Found

## Frontend Contracts

### TemperatureGauge Component

**Props**:
```typescript
interface TemperatureGaugeProps {
  confidence: number;        // 0.0-1.0
  tier?: string;             // Correlation tier name
  variant: "dot" | "bar" | "thermometer";
  // dot: 12px color circle + percentage text (list views)
  // bar: horizontal bar with fill (dashboard aggregate)
  // thermometer: vertical gauge with colour gradient (resource detail)
  size?: "sm" | "md" | "lg"; // default "md"
}
```

**Colour mapping**:
- `confidence >= 0.90` → red (#ef4444) — hot
- `confidence >= 0.70` → amber (#f59e0b) — warm
- `confidence >= 0.40` → yellow (#eab308) — tepid
- `confidence < 0.40` → blue (#3b82f6) — cold

### CorrelationJobProgress Component

**Props**:
```typescript
interface CorrelationJobProgressProps {
  jobId: string;
  onComplete?: () => void;
}
```

**Behaviour**: Polls `GET /automations/correlation-jobs/{jobId}` every 2 seconds until status is `completed` or `failed`. Shows progress bar with matched/queued/error counts.
