# Contract: Usage Dashboard API

## GET /api/v1/usage/summary

Get aggregate usage statistics grouped by feature area.

**Auth**: Required (Bearer token)

### Query Parameters

| Parameter  | Type   | Required | Default   | Description                         |
|------------|--------|----------|-----------|-------------------------------------|
| start_date | string | no       | 7 days ago | ISO 8601 date (e.g. 2026-03-15)   |
| end_date   | string | no       | today      | ISO 8601 date (e.g. 2026-03-22)   |

### Response

**200 OK**
```json
{
  "period": {
    "start": "2026-03-15T00:00:00Z",
    "end": "2026-03-22T23:59:59Z"
  },
  "feature_areas": [
    {
      "feature_area": "Resource Browsing",
      "total_events": 342,
      "unique_users": 3,
      "trend": "up",
      "trend_percentage": 15.2
    },
    {
      "feature_area": "Graph Visualisation",
      "total_events": 128,
      "unique_users": 2,
      "trend": "down",
      "trend_percentage": -8.4
    }
  ],
  "total_events": 1024,
  "total_unique_users": 4
}
```

**`trend`**: Compared to the immediately preceding period of equal length. Values: `"up"`, `"down"`, `"flat"` (change < 1%).

**`trend_percentage`**: Percentage change from previous period. Positive = up, negative = down.

---

## GET /api/v1/usage/feature/{feature_area}

Get detailed action breakdown for a specific feature area.

**Auth**: Required (Bearer token)

### Path Parameters

| Parameter    | Type   | Description                              |
|--------------|--------|------------------------------------------|
| feature_area | string | URL-encoded feature area name            |

### Query Parameters

Same as `/summary` (start_date, end_date).

### Response

**200 OK**
```json
{
  "feature_area": "Graph Visualisation",
  "period": {
    "start": "2026-03-15T00:00:00Z",
    "end": "2026-03-22T23:59:59Z"
  },
  "actions": [
    {
      "action": "graph_overlay_opened",
      "count": 85,
      "unique_users": 2
    },
    {
      "action": "node_expanded",
      "count": 33,
      "unique_users": 1
    },
    {
      "action": "depth_changed",
      "count": 10,
      "unique_users": 1
    }
  ],
  "total_events": 128
}
```

---

## GET /api/v1/usage/logins

Get login audit history with pagination.

**Auth**: Required (Bearer token)

### Query Parameters

| Parameter  | Type   | Required | Default    | Description                    |
|------------|--------|----------|------------|--------------------------------|
| start_date | string | no       | 7 days ago | ISO 8601 date                  |
| end_date   | string | no       | today      | ISO 8601 date                  |
| page       | int    | no       | 1          | Page number                    |
| page_size  | int    | no       | 50         | Items per page (max 100)       |

### Response

**200 OK**
```json
{
  "period": {
    "start": "2026-03-15T00:00:00Z",
    "end": "2026-03-22T23:59:59Z"
  },
  "summary": {
    "total_attempts": 47,
    "successful": 42,
    "failed": 5,
    "unique_users": 3
  },
  "entries": [
    {
      "id": "a1b2c3d4-...",
      "username": "admin",
      "outcome": "success",
      "failure_reason": null,
      "ip_address": "10.89.0.18",
      "created_at": "2026-03-22T14:30:00Z"
    },
    {
      "id": "e5f6g7h8-...",
      "username": "unknown_user",
      "outcome": "failure",
      "failure_reason": "Invalid credentials",
      "ip_address": "192.168.1.50",
      "created_at": "2026-03-22T14:28:00Z"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total_count": 47
}
```
