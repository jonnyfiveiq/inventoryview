# API Contract: Drift Calendar Heatmap

**Feature**: 004-drift-calendar-heatmap | **Date**: 2026-03-22

## Backend API

### Endpoint 1: Resource Drift Timeline

**Method**: GET
**Path**: `/api/v1/resources/{uid}/drift/timeline`
**Auth**: JWT Bearer token (existing)

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start | string (YYYY-MM-DD) | No | 365 days ago | Start date (inclusive) |
| end | string (YYYY-MM-DD) | No | Today | End date (inclusive) |

**Response** (200):

```json
{
  "data": [
    {
      "date": "2026-03-15",
      "count": 3,
      "fields": ["state", "ip_address", "memory_mb"]
    },
    {
      "date": "2026-03-10",
      "count": 1,
      "fields": ["state"]
    }
  ],
  "total_drift_count": 47,
  "first_seen": "2025-12-01T14:30:00Z"
}
```

**Notes**:
- `data` contains only days that have drift events (sparse array, not all 365 days)
- `total_drift_count` is the resource's all-time drift event count (not limited to the date range)
- `first_seen` is the resource's discovery timestamp from the graph node
- Days with no events are omitted from the response — the frontend fills gaps as empty cells

**SQL Logic** (conceptual):

```sql
SELECT DATE(changed_at) AS date,
       COUNT(*) AS count,
       ARRAY_AGG(DISTINCT field) AS fields
FROM resource_drift
WHERE resource_uid = :uid
  AND changed_at >= :start
  AND changed_at < :end + INTERVAL '1 day'
GROUP BY DATE(changed_at)
ORDER BY date
```

### Endpoint 2: Fleet Drift Timeline

**Method**: GET
**Path**: `/api/v1/drift/fleet-timeline`
**Auth**: JWT Bearer token (existing)

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start | string (YYYY-MM-DD) | No | 365 days ago | Start date (inclusive) |
| end | string (YYYY-MM-DD) | No | Today | End date (inclusive) |

**Response** (200):

```json
{
  "data": [
    {
      "date": "2026-03-15",
      "count": 12,
      "fields": ["state", "ip_address", "memory_mb", "num_cpu"]
    },
    {
      "date": "2026-03-10",
      "count": 5,
      "fields": ["state", "version"]
    }
  ],
  "fleet_avg_lifetime": 14.2,
  "total_resources_with_drift": 38
}
```

**Notes**:
- `data` aggregates drift events across ALL resources per day
- `fleet_avg_lifetime` = total drift events in system / count of resources with ≥1 drift entry
- `total_resources_with_drift` = count of distinct resource_uids in resource_drift table
- Used by both the fleet calendar AND per-resource calendars (for the relative intensity baseline)

**SQL Logic** (conceptual):

```sql
-- Daily aggregation
SELECT DATE(changed_at) AS date,
       COUNT(*) AS count,
       ARRAY_AGG(DISTINCT field) AS fields
FROM resource_drift
WHERE changed_at >= :start
  AND changed_at < :end + INTERVAL '1 day'
GROUP BY DATE(changed_at)
ORDER BY date;

-- Fleet stats
SELECT COUNT(*) AS total_events,
       COUNT(DISTINCT resource_uid) AS total_resources_with_drift
FROM resource_drift;
-- fleet_avg_lifetime = total_events / total_resources_with_drift
```

## Frontend Component Contract

### DriftCalendar Component

**Props**:

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| mode | "resource" \| "fleet" | Yes | Whether to show per-resource or fleet-wide data |
| resourceUid | string | Only in "resource" mode | Resource UID for per-resource timeline |
| onDayClick | (date: string) => void | No | Callback when a coloured cell is clicked |
| className | string | No | Additional CSS classes |

**Behaviour**:
- In `resource` mode: fetches `/resources/{uid}/drift/timeline` and `/drift/fleet-timeline` (for relative baseline), renders per-resource calendar with two-layer colouring
- In `fleet` mode: fetches `/drift/fleet-timeline` only, renders fleet aggregate calendar with absolute daily intensity
- Renders a 53-column × 7-row SVG grid with month labels, day-of-week labels, and colour legend
- Tooltip on hover shows date, event count, and changed fields
- Previous/Next navigation to shift the 365-day window

### Colour Intensity Calculation

**Two-Layer Model** (resource mode):

```
baseIntensity = clamp(resource.total_drift_count / fleet_avg_lifetime, 0, 1)
spikeIntensity = clamp(day.count / max(resourceMaxDailyCount, 1), 0, 1)
finalIntensity = clamp(baseIntensity * 0.4 + spikeIntensity * 0.6, 0, 1)
```

**Colour Scale** (5 levels):

| Level | Intensity Range | Colour | Meaning |
|-------|----------------|--------|---------|
| 0 | 0 (no events) | Transparent / neutral | No drift activity |
| 1 | 0.01–0.25 | Light yellow-green | Low activity |
| 2 | 0.26–0.50 | Yellow | Moderate activity |
| 3 | 0.51–0.75 | Orange | High activity |
| 4 | 0.76–1.00 | Red | Very high activity |

**Discovery cell**: Blue/teal (#38bdf8) regardless of drift activity — always visually distinct.

**Fleet mode**: Uses absolute daily count mapped to percentile buckets across the visible 365-day window.

**Fallback** (fewer than 5 resources with drift): Use absolute thresholds — 1 event = level 1, 3 = level 2, 5 = level 3, 8+ = level 4.

### DriftModal Extension

The existing DriftModal receives a new optional prop:

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| filterDate | string (YYYY-MM-DD) | No | If provided, show only drift entries from this date |

When `filterDate` is set, the modal title includes the date and the entry list is filtered client-side from the full drift history.
