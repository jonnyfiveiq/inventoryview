# Data Model: Drift Calendar Heatmap

**Feature**: 004-drift-calendar-heatmap | **Date**: 2026-03-22

## Existing Entities (No Changes)

### Resource (graph node)

Already contains `first_seen` (ISO datetime string) which serves as the discovery date for the calendar.

| Property | Type | Notes |
|----------|------|-------|
| uid | string (UUID) | Primary identifier |
| first_seen | string (ISO 8601) | Discovery date — used for the cool-coloured calendar cell |
| last_seen | string (ISO 8601) | Last collection update |
| name | string | Display name |
| vendor | string | Provider name |
| normalised_type | string | Taxonomy type |

### Drift Entry (resource_drift table)

Already contains `changed_at` timestamp for grouping by date.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| resource_uid | string | FK to resource node |
| field | string | Field that changed |
| old_value | string (nullable) | Previous value |
| new_value | string (nullable) | New value |
| changed_at | timestamp with timezone | When the change occurred — used for calendar date grouping |
| source | string | Change source (default: "collector") |

**Existing index**: `(resource_uid, changed_at)` — sufficient for the date-range aggregation queries.

## New Transient Structures (Frontend Only)

### DriftTimelineDay

Represents a single day's aggregated drift activity for one resource.

| Field | Type | Notes |
|-------|------|-------|
| date | string (YYYY-MM-DD) | Calendar date |
| count | number | Total drift events on this day |
| fields | string[] | List of distinct field names that changed |

### DriftTimelineResponse

Response from the per-resource drift timeline endpoint.

| Field | Type | Notes |
|-------|------|-------|
| data | DriftTimelineDay[] | Daily aggregated drift events |
| total_drift_count | number | Resource's total lifetime drift event count |
| first_seen | string (ISO 8601) | Resource's discovery date |

### FleetDriftTimelineResponse

Response from the fleet-wide drift timeline endpoint.

| Field | Type | Notes |
|-------|------|-------|
| data | DriftTimelineDay[] | Daily aggregated drift events across all resources |
| fleet_avg_lifetime | number | Average total lifetime drift count per resource (across resources that have drift) |
| total_resources_with_drift | number | Count of resources that have at least one drift entry |

### CalendarCellData

Frontend-only structure for rendering a single calendar cell.

| Field | Type | Notes |
|-------|------|-------|
| date | string (YYYY-MM-DD) | Calendar date |
| count | number | Event count for this day |
| fields | string[] | Fields that changed |
| type | "discovery" \| "drift" \| "empty" | Cell type for colour selection |
| intensity | number (0.0–1.0) | Computed colour intensity from two-layer model |

## Relationships

- Each **DriftTimelineDay** maps to zero or more **DriftEntry** rows (aggregated by date)
- Each **CalendarCellData** maps to exactly one day in the 365-day calendar grid
- **DriftTimelineResponse.first_seen** maps to the resource's graph node `first_seen` property
- **FleetDriftTimelineResponse.fleet_avg_lifetime** is used by the frontend to compute the base intensity layer for per-resource calendars

## No Schema Migrations Required

All new data structures are transient (API response shapes and frontend state). The existing `resource_drift` table and its `(resource_uid, changed_at)` index support the required aggregation queries without modification.
