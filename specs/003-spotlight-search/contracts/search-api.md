# Contract: Search API

**Feature**: 003-spotlight-search
**Date**: 2026-03-22

## Overview

Extension to the existing `GET /api/v1/resources` endpoint to support text-based search.

## Endpoint

### GET /api/v1/resources

**Change type**: Extended (backward-compatible — new optional query parameter)

#### New Query Parameter

| Parameter | Type | Required | Default | Constraints |
|-----------|------|----------|---------|-------------|
| search | string | No | (none) | Minimum 2 characters. Case-insensitive substring match. |

#### Behavior When `search` Is Provided

1. The backend performs case-insensitive substring matching (`CONTAINS`) against these fields: `name`, `vendor_id`, `state`, `vendor`, `normalised_type`.
2. A resource matches if ANY of the five fields contain the search string.
3. The `search` parameter is combinable with existing filters (`vendor`, `category`, `region`, `state`). When combined, both the search AND the filter must match (AND logic).
4. Pagination (cursor, page_size) works identically to non-search queries.
5. Results are ordered by `name` ascending (default sort).

#### Request Example

```
GET /api/v1/resources?search=john&page_size=50
Authorization: Bearer <token>
```

#### Response Format (unchanged)

```json
{
  "items": [
    {
      "uid": "550e8400-...",
      "name": "john-hypervisor-01",
      "vendor_id": "host-101",
      "vendor": "VMware",
      "vendor_type": "HostSystem",
      "normalised_type": "hypervisor",
      "category": "compute",
      "region": null,
      "state": "connected",
      "classification_confidence": 0.95,
      "classification_method": "rule_based",
      "first_seen": "2026-03-15T10:00:00",
      "last_seen": "2026-03-22T14:00:00"
    }
  ],
  "next_cursor": "eyJ...",
  "has_more": false
}
```

#### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | `search` parameter is less than 2 characters | `{"error": {"code": "VALIDATION_ERROR", "message": "Search query must be at least 2 characters"}}` |
| 401 | Missing or invalid auth token | Standard auth error |

## Frontend Contract

### SpotlightSearch Component

**Trigger**: Keyboard shortcut (Cmd+K / Ctrl+K) or header search icon click.

**Props**: None (global overlay, manages its own state).

**Behavior**:
1. Opens centered modal overlay with backdrop blur/dim
2. Auto-focuses search input
3. Debounces input by 300ms
4. Calls `GET /api/v1/resources?search={query}&page_size=50` on debounced value
5. Groups results client-side by `normalised_type`
6. Displays grouped results with taxonomy headers showing type + count
7. Each group shows max 5 results initially, expandable to 10
8. Beyond 10, shows "View all X on provider page" link
9. Supports keyboard navigation (Up/Down/Enter/Escape)
10. Clicking result or pressing Enter on highlighted result navigates to `/resources/{uid}`
11. Escape or click-outside closes overlay

### useSearch Hook

**Input**: `query: string` (debounced, minimum 2 characters)

**Output**:
```typescript
{
  data: Resource[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}
```

**Query key**: `["resources", "search", query]`

**Enabled**: Only when `query.length >= 2`
