# API Contract: Playlists

**Feature**: 005-resource-playlists
**Date**: 2026-03-22
**Base path**: `/api/v1/playlists`

All endpoints require `Authorization: Bearer <token>` header. Returns 401 if missing or invalid.

---

## List Playlists

```
GET /api/v1/playlists
```

**Query parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| cursor | string | null | Pagination cursor |
| page_size | int | 50 | Results per page (1-200) |

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Production OpenShift Cluster",
      "slug": "production-openshift-cluster",
      "description": "All resources in the prod OCP environment",
      "member_count": 42,
      "created_at": "2026-03-22T10:00:00Z",
      "updated_at": "2026-03-22T14:30:00Z"
    }
  ],
  "next_cursor": "string | null",
  "page_size": 50
}
```

---

## Create Playlist

```
POST /api/v1/playlists
```

**Request body**:
```json
{
  "name": "Production OpenShift Cluster",
  "description": "Optional description"
}
```

- `name`: required, 1-255 characters
- `description`: optional

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "name": "Production OpenShift Cluster",
  "slug": "production-openshift-cluster",
  "description": "Optional description",
  "member_count": 0,
  "created_at": "2026-03-22T10:00:00Z",
  "updated_at": "2026-03-22T10:00:00Z"
}
```

**Errors**:
- `400` — name missing or exceeds max length
- `409` — slug collision that cannot be auto-resolved (unlikely)

---

## Get Playlist Detail (by slug or UUID)

```
GET /api/v1/playlists/{identifier}
```

`{identifier}` can be a slug (e.g., `production-openshift-cluster`) or a UUID.

**Query parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| detail | string | "summary" | `summary` or `full`. Controls resource field depth. |

**Response** `200 OK` (detail=summary):
```json
{
  "id": "uuid",
  "name": "Production OpenShift Cluster",
  "slug": "production-openshift-cluster",
  "description": "All resources in the prod OCP environment",
  "member_count": 2,
  "created_at": "2026-03-22T10:00:00Z",
  "updated_at": "2026-03-22T14:30:00Z",
  "resources": [
    {
      "uid": "resource-uuid-1",
      "name": "master-0.ocp-prod-rdu",
      "vendor": "openshift",
      "normalised_type": "kubernetes_node",
      "category": "compute",
      "state": "ready"
    },
    {
      "uid": "resource-uuid-2",
      "name": "ocp-master-0-vm",
      "vendor": "vmware",
      "normalised_type": "virtual_machine",
      "category": "compute",
      "state": "poweredOn"
    }
  ]
}
```

**Response** `200 OK` (detail=full):
Same structure but each resource object includes all fields (`vendor_id`, `vendor_type`, `region`, `first_seen`, `last_seen`, `classification_confidence`, `classification_method`, `raw_properties`).

**Errors**:
- `404` — playlist not found by slug or UUID

---

## Update Playlist

```
PATCH /api/v1/playlists/{identifier}
```

**Request body** (partial update):
```json
{
  "name": "New Name",
  "description": "Updated description"
}
```

Both fields optional. If `name` changes, slug is regenerated.

**Response** `200 OK`: Updated playlist object (same shape as Create response).

**Errors**:
- `404` — playlist not found
- `400` — invalid name

---

## Delete Playlist

```
DELETE /api/v1/playlists/{identifier}
```

**Response** `204 No Content`

**Errors**:
- `404` — playlist not found

---

## Add Resource to Playlist

```
POST /api/v1/playlists/{identifier}/members
```

**Request body**:
```json
{
  "resource_uid": "resource-uuid"
}
```

**Response** `201 Created`:
```json
{
  "playlist_id": "uuid",
  "resource_uid": "resource-uuid",
  "added_at": "2026-03-22T14:30:00Z"
}
```

**Errors**:
- `404` — playlist not found
- `404` — resource not found in graph
- `409` — resource already in playlist

---

## Remove Resource from Playlist

```
DELETE /api/v1/playlists/{identifier}/members/{resource_uid}
```

**Response** `204 No Content`

**Errors**:
- `404` — playlist or membership not found

---

## Get Playlists for a Resource

```
GET /api/v1/resources/{uid}/playlists
```

Returns all playlists that contain this resource.

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Production OpenShift Cluster",
      "slug": "production-openshift-cluster",
      "member_count": 42
    }
  ]
}
```

---

## Get Playlist Activity Timeline

```
GET /api/v1/playlists/{identifier}/activity/timeline
```

**Query parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| start | string (YYYY-MM-DD) | null | Start date filter |
| end | string (YYYY-MM-DD) | null | End date filter |

**Response** `200 OK`:
```json
{
  "data": [
    {
      "date": "2026-03-22",
      "count": 5,
      "actions": ["resource_added", "resource_removed"]
    }
  ],
  "total_activity_count": 47
}
```

---

## Get Playlist Activity Log

```
GET /api/v1/playlists/{identifier}/activity
```

**Query parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| date | string (YYYY-MM-DD) | null | Filter to specific date |
| cursor | string | null | Pagination cursor |
| page_size | int | 50 | Results per page (1-200) |

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": "uuid",
      "action": "resource_added",
      "resource_uid": "resource-uuid",
      "resource_name": "master-0.ocp-prod-rdu",
      "resource_vendor": "openshift",
      "detail": null,
      "occurred_at": "2026-03-22T14:30:00Z"
    }
  ],
  "next_cursor": "string | null",
  "page_size": 50
}
```
