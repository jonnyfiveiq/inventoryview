# API Client Contract: InventoryView Frontend → Backend

**Feature**: 002-inventory-frontend-dashboard
**Date**: 2026-03-22
**Base URL**: `/api/v1`

## Authentication

All endpoints except Health and Setup Status require a bearer token in the `Authorization` header.

```
Authorization: Bearer <jwt_token>
```

On 401 response, the frontend MUST redirect to the login page.

---

## Endpoints Consumed by Frontend

### Health

#### `GET /api/v1/health`

**Auth**: None required

**Response 200**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "timestamp": "2026-03-22T10:00:00+00:00"
}
```

**Frontend usage**: Connection status indicator in sidebar footer.

---

### Setup

#### `GET /api/v1/setup/status`

**Auth**: None required

**Response 200**:
```json
{
  "setup_complete": true
}
```

**Frontend usage**: Route guard — if `setup_complete` is false, redirect to setup page.

#### `POST /api/v1/setup/init`

**Auth**: None required

**Request body**:
```json
{
  "password": "string"
}
```

**Response 201**:
```json
{
  "message": "Administrator account created successfully",
  "username": "admin"
}
```

**Response 409**: Setup already completed.

**Frontend usage**: Initial setup page for first-time administrator creation.

---

### Auth

#### `POST /api/v1/auth/login`

**Auth**: None required

**Request body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200**:
```json
{
  "token": "eyJ...",
  "token_type": "bearer",
  "expires_at": "2026-03-23T10:00:00+00:00"
}
```

**Response 401**: Invalid credentials.

**Frontend usage**: Login page → store token in auth store.

#### `POST /api/v1/auth/revoke`

**Auth**: Required

**Request body**:
```json
{
  "token": "eyJ..."
}
```

**Response 200**:
```json
{
  "message": "Token revoked successfully"
}
```

**Frontend usage**: Logout action.

---

### Resources

#### `GET /api/v1/resources`

**Auth**: Required

**Query parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| vendor | string? | null | Filter by vendor name |
| category | string? | null | Filter by category |
| region | string? | null | Filter by region |
| state | string? | null | Filter by state |
| cursor | string? | null | Cursor UID for pagination |
| page_size | int | 50 | Results per page (1-200) |

**Response 200**:
```json
{
  "data": [
    {
      "uid": "uuid-string",
      "name": "web-prod-01",
      "vendor_id": "vm-123",
      "vendor": "vmware",
      "vendor_type": "VirtualMachine",
      "normalised_type": "virtual_machine",
      "category": "compute",
      "region": null,
      "state": "poweredOn",
      "classification_confidence": null,
      "classification_method": null,
      "first_seen": "2026-03-22T10:00:00+00:00",
      "last_seen": "2026-03-22T10:00:00+00:00"
    }
  ],
  "next_cursor": "uuid-or-null",
  "page_size": 50
}
```

**Frontend usage**: Landing page carousels (grouped by `normalised_type`), provider drill-down table, heatmap aggregation.

#### `GET /api/v1/resources/{uid}`

**Auth**: Required

**Response 200**: Full resource detail including `raw_properties`.
```json
{
  "uid": "uuid-string",
  "name": "web-prod-01",
  "vendor_id": "vm-123",
  "vendor": "vmware",
  "vendor_type": "VirtualMachine",
  "normalised_type": "virtual_machine",
  "category": "compute",
  "region": null,
  "state": "poweredOn",
  "classification_confidence": null,
  "classification_method": null,
  "first_seen": "2026-03-22T10:00:00+00:00",
  "last_seen": "2026-03-22T10:00:00+00:00",
  "raw_properties": { "cpu": 4, "memoryMB": 8192 }
}
```

**Response 404**: Resource not found.

**Frontend usage**: ResourceDetailPage.

#### `GET /api/v1/resources/{uid}/relationships`

**Auth**: Required

**Query parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| direction | "in" \| "out" \| "both" | "both" | Filter edge direction |
| type | string? | null | Filter by relationship type |
| cursor | string? | null | Pagination cursor |
| page_size | int | 50 | Results per page (1-200) |

**Response 200**: Paginated list of relationships.

**Frontend usage**: Resource detail page relationship list.

#### `GET /api/v1/resources/{uid}/graph`

**Auth**: Required

**Query parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| depth | int | 1 | Traversal depth (min 1, max from system settings) |

**Response 200**:
```json
{
  "nodes": [
    { "uid": "uuid", "name": "web-prod-01", "category": "compute", "vendor": "vmware", "normalised_type": "virtual_machine" }
  ],
  "edges": [
    { "source_uid": "uuid-1", "target_uid": "uuid-2", "type": "HOSTED_ON", "confidence": 1.0 }
  ]
}
```

**Response 400**: Depth exceeds maximum.

**Frontend usage**: GraphCanvas (Cytoscape.js). Initial load + lazy expansion (re-fetch centred on clicked node).

#### `GET /api/v1/resources/{uid}/drift`

**Auth**: Required

**Response 200**: Full drift history for a resource, newest first.
```json
{
  "data": [
    {
      "id": "uuid-string",
      "resource_uid": "resource-uuid",
      "field": "state",
      "old_value": "poweredOn",
      "new_value": "poweredOff",
      "changed_at": "2026-03-20T14:30:00+00:00",
      "source": "collector"
    }
  ]
}
```

**Frontend usage**: DriftModal on ResourceDetailPage.

#### `GET /api/v1/resources/{uid}/drift/exists`

**Auth**: Required

**Response 200**:
```json
{
  "has_drift": true
}
```

**Frontend usage**: Conditionally show "Drift History" button on ResourceDetailPage.

#### `POST /api/v1/resources/{uid}/drift`

**Auth**: Required

**Request body**:
```json
{
  "field": "state",
  "old_value": "poweredOn",
  "new_value": "poweredOff",
  "changed_at": "2026-03-20T14:30:00+00:00",
  "source": "collector"
}
```

**Response 201**:
```json
{
  "status": "recorded"
}
```

**Response 400**: Missing required `field` parameter.

**Frontend usage**: Not consumed by frontend directly — used by collectors and seed script.

---

## Error Response Format

All error responses follow:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Error codes: `NOT_FOUND`, `UNAUTHORIZED`, `VALIDATION_ERROR`, `CONFLICT`, `INTERNAL_ERROR`.

## Frontend API Client Requirements

1. **Axios instance** with base URL from environment variable (`VITE_API_BASE_URL`, default `/api/v1`).
2. **Request interceptor**: Attach `Authorization: Bearer <token>` header from auth store.
3. **Response interceptor**: On 401, clear auth store and redirect to `/login`.
4. **Error handling**: Parse error response format and surface `message` to user.
5. **TanStack Query integration**: Each endpoint maps to a query key for automatic caching/invalidation.
