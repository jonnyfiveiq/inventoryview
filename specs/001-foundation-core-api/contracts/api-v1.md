# API Contract: InventoryView REST API v1

**Base URL**: `/api/v1`
**Auth**: Bearer token (JWT) on all endpoints except health and setup (when applicable)
**Content-Type**: `application/json`
**Date**: 2026-03-21

---

## Common Response Patterns

### Paginated List Response
```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "string | null",
    "has_more": true,
    "page_size": 50
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [ ... ]
  }
}
```

### Standard Error Codes
| HTTP | Code | When |
|------|------|------|
| 400 | VALIDATION_ERROR | Invalid input, bad filter, missing required field |
| 401 | UNAUTHORIZED | Missing or invalid/expired/revoked token |
| 404 | NOT_FOUND | Resource/credential not found |
| 409 | CONFLICT | Duplicate or conflicting state |
| 500 | INTERNAL_ERROR | Unexpected server error |

---

## Health

### GET /api/v1/health

No authentication required.

**Response 200**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "timestamp": "2026-03-21T10:00:00Z"
}
```

---

## Setup

### GET /api/v1/setup/status

No authentication required. Returns whether initial setup is complete.

**Response 200**:
```json
{
  "setup_complete": false
}
```

### POST /api/v1/setup/init

No authentication required. Only callable when `setup_complete` is false.

**Request**:
```json
{
  "password": "string (min 12 chars)"
}
```

**Response 201**:
```json
{
  "message": "Administrator account created successfully",
  "username": "admin"
}
```

**Response 409** (already set up):
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Initial setup has already been completed"
  }
}
```

---

## Authentication

### POST /api/v1/auth/login

**Request**:
```json
{
  "username": "admin",
  "password": "string"
}
```

**Response 200**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_at": "2026-03-22T10:00:00Z"
}
```

**Response 401**: Invalid credentials.

### POST /api/v1/auth/revoke

**Auth**: Required

**Request**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200**:
```json
{
  "message": "Token revoked successfully"
}
```

---

## Resources

### GET /api/v1/resources

**Auth**: Required
**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| vendor | string | Filter by vendor (aws, azure, gcp, vmware, etc.) |
| category | string | Filter by category (Compute, Storage, Network, etc.) |
| region | string | Filter by region |
| state | string | Filter by state (running, stopped, etc.) |
| cursor | string | Pagination cursor |
| page_size | integer | Items per page (default 50, max 200) |

**Response 200**: Paginated list of resources.
```json
{
  "data": [
    {
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "name": "web-server-01",
      "vendor_id": "i-1234567890abcdef0",
      "vendor": "aws",
      "vendor_type": "ec2:instance",
      "normalised_type": "virtual_machine",
      "category": "Compute",
      "region": "us-east-1",
      "state": "running",
      "classification_confidence": 1.0,
      "classification_method": "rule",
      "first_seen": "2026-03-20T10:00:00Z",
      "last_seen": "2026-03-21T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6IC...",
    "has_more": true,
    "page_size": 50
  }
}
```

**Response 400**: Invalid filter parameter.

### POST /api/v1/resources

**Auth**: Required

**Request**:
```json
{
  "name": "web-server-01",
  "vendor_id": "i-1234567890abcdef0",
  "vendor": "aws",
  "vendor_type": "ec2:instance",
  "normalised_type": "virtual_machine",
  "category": "Compute",
  "region": "us-east-1",
  "state": "running",
  "classification_confidence": 1.0,
  "classification_method": "rule",
  "raw_properties": { "instance_type": "t3.medium" }
}
```

**Response 201**: Created resource (same shape as list item + `raw_properties`).

**Response 200**: If upsert matched existing `(vendor_id, vendor)`, returns updated resource.

### GET /api/v1/resources/{uid}

**Auth**: Required

**Response 200**: Full resource detail including `raw_properties`.
```json
{
  "uid": "550e8400-e29b-41d4-a716-446655440000",
  "name": "web-server-01",
  "vendor_id": "i-1234567890abcdef0",
  "vendor": "aws",
  "vendor_type": "ec2:instance",
  "normalised_type": "virtual_machine",
  "category": "Compute",
  "region": "us-east-1",
  "state": "running",
  "classification_confidence": 1.0,
  "classification_method": "rule",
  "first_seen": "2026-03-20T10:00:00Z",
  "last_seen": "2026-03-21T10:00:00Z",
  "raw_properties": { "instance_type": "t3.medium" }
}
```

**Response 404**: Resource not found.

### PATCH /api/v1/resources/{uid}

**Auth**: Required

**Request**: Partial update (any subset of resource fields).
```json
{
  "state": "stopped",
  "raw_properties": { "instance_type": "t3.large" }
}
```

**Response 200**: Updated resource.

### DELETE /api/v1/resources/{uid}

**Auth**: Required

**Response 204**: Resource deleted (node and all connected edges removed).

**Response 404**: Resource not found.

### GET /api/v1/resources/{uid}/relationships

**Auth**: Required
**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| direction | string | `in`, `out`, or `both` (default: `both`) |
| type | string | Filter by relationship type |
| cursor | string | Pagination cursor |
| page_size | integer | Items per page (default 50, max 200) |

**Response 200**: Paginated list of relationships with connected resource summaries.

### GET /api/v1/resources/{uid}/graph

**Auth**: Required
**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| depth | integer | Traversal depth (default 1, max per system setting, default max 5) |

**Response 200**: Subgraph around the resource.
```json
{
  "nodes": [
    {
      "uid": "...",
      "name": "...",
      "category": "Compute",
      "vendor": "aws"
    }
  ],
  "edges": [
    {
      "source_uid": "...",
      "target_uid": "...",
      "type": "HOSTED_ON",
      "confidence": 0.95
    }
  ]
}
```

---

## Relationships

### POST /api/v1/relationships

**Auth**: Required

**Request**:
```json
{
  "source_uid": "550e8400-...",
  "target_uid": "660e8400-...",
  "type": "HOSTED_ON",
  "confidence": 0.95,
  "source_collector": "manual",
  "inference_method": "manual"
}
```

**Response 201**: Created relationship.

**Response 404**: Source or target resource not found.

### DELETE /api/v1/relationships

**Auth**: Required

**Request**:
```json
{
  "source_uid": "550e8400-...",
  "target_uid": "660e8400-...",
  "type": "HOSTED_ON"
}
```

**Response 204**: Relationship deleted.

---

## Credentials

### POST /api/v1/credentials

**Auth**: Required

**Request**:
```json
{
  "name": "AWS Production",
  "credential_type": "aws_key_pair",
  "secret": {
    "access_key_id": "AKIA...",
    "secret_access_key": "wJalr..."
  },
  "metadata": {
    "account_id": "123456789012",
    "region": "us-east-1"
  }
}
```

**Response 201**: Credential metadata (never the secret).
```json
{
  "id": "770e8400-...",
  "name": "AWS Production",
  "credential_type": "aws_key_pair",
  "metadata": { "account_id": "123456789012", "region": "us-east-1" },
  "associated_collector": null,
  "created_at": "2026-03-21T10:00:00Z",
  "updated_at": "2026-03-21T10:00:00Z",
  "last_used_at": null
}
```

**Response 400**: Unsupported credential type.

### GET /api/v1/credentials

**Auth**: Required
**Query Parameters**: `cursor`, `page_size`, `credential_type`

**Response 200**: Paginated list of credential metadata (never secrets).

### GET /api/v1/credentials/{id}

**Auth**: Required

**Response 200**: Single credential metadata.

**Response 404**: Credential not found.

### PATCH /api/v1/credentials/{id}

**Auth**: Required

**Request**: Partial update. Can update `name`, `metadata`, `secret`, `associated_collector`.
```json
{
  "name": "AWS Production (rotated)",
  "secret": {
    "access_key_id": "AKIA_NEW...",
    "secret_access_key": "NEW_wJalr..."
  }
}
```

**Response 200**: Updated credential metadata (never the secret).

### DELETE /api/v1/credentials/{id}

**Auth**: Required

**Response 204**: Credential permanently deleted.

**Response 404**: Credential not found.

### POST /api/v1/credentials/{id}/test

**Auth**: Required

**Response 200**:
```json
{
  "credential_id": "770e8400-...",
  "status": "success",
  "message": "Connection successful",
  "tested_at": "2026-03-21T10:05:00Z"
}
```

**Response 200** (failure):
```json
{
  "credential_id": "770e8400-...",
  "status": "failure",
  "message": "Access denied: invalid credentials",
  "tested_at": "2026-03-21T10:05:00Z"
}
```

---

## OpenAPI Documentation

### GET /docs

Auto-generated Swagger UI (FastAPI default). No authentication required.

### GET /redoc

Auto-generated ReDoc documentation. No authentication required.
