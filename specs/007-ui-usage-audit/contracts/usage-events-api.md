# Contract: Usage Event Ingestion API

## POST /api/v1/usage/events

Record a UI usage event.

**Auth**: Required (Bearer token)

### Request Body

```json
{
  "feature_area": "Graph Visualisation",
  "action": "graph_overlay_opened"
}
```

| Field        | Type   | Required | Constraints        |
|--------------|--------|----------|--------------------|
| feature_area | string | yes      | max 100 chars      |
| action       | string | yes      | max 100 chars      |

### Response

**201 Created**
```json
{
  "status": "ok"
}
```

**401 Unauthorized** — Missing or invalid token.

### Behaviour

- User ID is extracted from the bearer token (not sent in the body).
- Timestamp is server-generated.
- Response is immediate; no downstream processing blocks the response.
- Invalid or missing fields return 422 Validation Error.

---

## POST /api/v1/usage/events/batch

Record multiple usage events in a single request (optional optimisation).

**Auth**: Required (Bearer token)

### Request Body

```json
{
  "events": [
    { "feature_area": "Resource Browsing", "action": "page_view" },
    { "feature_area": "Drift Detection", "action": "drift_timeline_expanded" }
  ]
}
```

| Field  | Type  | Required | Constraints      |
|--------|-------|----------|------------------|
| events | array | yes      | max 50 items     |

### Response

**201 Created**
```json
{
  "status": "ok",
  "count": 2
}
```
