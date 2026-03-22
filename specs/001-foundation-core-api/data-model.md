# Data Model: Foundation Core API

**Feature**: 001-foundation-core-api
**Date**: 2026-03-21

## Overview

The data model spans two storage layers within the same PostgreSQL 16 instance:

1. **Relational tables** (standard SQL): Administrator, Credential, RevokedToken, VaultConfig, SystemSetting
2. **Graph storage** (Apache AGE): Resource nodes, Relationship edges

This separation follows Constitution Principle I (Graph-First): resources and
relationships live in the graph; metadata and administrative data use standard
PostgreSQL tables.

---

## Relational Entities

### Administrator

Single built-in admin account (MVP).

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | PK, default gen_random_uuid() | |
| username | text | UNIQUE, NOT NULL, default 'admin' | |
| password_hash | text | NOT NULL | Argon2id hash |
| created_at | timestamptz | NOT NULL, default now() | |
| updated_at | timestamptz | NOT NULL, default now() | |
| setup_complete | boolean | NOT NULL, default false | Flipped after initial password set |

**State Transitions**:
- `setup_complete: false` -> `true` (irreversible, on first password creation)

---

### Credential

Encrypted infrastructure credentials stored in the vault.

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | PK, default gen_random_uuid() | |
| name | text | NOT NULL | Human-readable label |
| credential_type | text | NOT NULL, CHECK in supported types | See supported types below |
| encrypted_secret | bytea | NOT NULL | AES-256-GCM ciphertext |
| nonce | bytea | NOT NULL | 96-bit GCM nonce (unique per encryption) |
| auth_tag | bytea | NOT NULL | GCM authentication tag |
| metadata | jsonb | NOT NULL, default '{}' | Non-secret fields (region, account ID, etc.) |
| associated_collector | text | NULL | Collector name (future use) |
| created_at | timestamptz | NOT NULL, default now() | |
| updated_at | timestamptz | NOT NULL, default now() | |
| last_used_at | timestamptz | NULL | Updated when credential is used for connection test |

**Supported Credential Types**:
- `aws_key_pair`
- `azure_service_principal`
- `gcp_service_account`
- `vsphere`
- `openshift_kubernetes`
- `bearer_token`
- `username_password`
- `ssh_key`

**Validation Rules**:
- `credential_type` must be one of the supported types (CHECK constraint)
- `name` must be non-empty
- `encrypted_secret` is never returned in API responses (FR-008)
- `encrypted_secret` is never logged (FR-009)

---

### RevokedToken

Blocklist for revoked JWT tokens.

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| jti | UUID | PK | JWT token ID |
| revoked_at | timestamptz | NOT NULL, default now() | |
| expires_at | timestamptz | NOT NULL | Original token expiry (for cleanup) |

**Lifecycle**: Entries can be purged after `expires_at` passes (the token would be
invalid anyway). A periodic cleanup is optional for M1.

---

### VaultConfig

Vault key derivation parameters (one row).

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | integer | PK, default 1, CHECK (id = 1) | Singleton row |
| salt | bytea | NOT NULL | Argon2id salt (32 bytes, generated once) |
| created_at | timestamptz | NOT NULL, default now() | |

**Notes**: The salt is not secret -- it adds uniqueness to the key derivation.
The derived master key exists only in application memory.

---

### SystemSetting

Key-value store for system-level configuration.

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| key | text | PK | Setting name |
| value | jsonb | NOT NULL | Setting value |
| updated_at | timestamptz | NOT NULL, default now() | |

**Known Keys** (M1):
- `max_traversal_depth`: integer, default 5 (FR-015)

---

### CredentialAuditLog

Audit trail for credential access operations (FR-011).

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | PK, default gen_random_uuid() | |
| credential_id | UUID | NOT NULL, FK -> credentials(id) ON DELETE SET NULL | |
| operation | text | NOT NULL, CHECK in (create, read, update, delete, use) | |
| actor | text | NOT NULL | Username of actor |
| timestamp | timestamptz | NOT NULL, default now() | |
| details | jsonb | NULL | Additional context (never contains secrets) |

---

## Graph Entities (Apache AGE)

Graph name: `inventory_graph`

### Resource Node

Label: `Resource` (base) + category label (e.g., `Compute`, `Storage`, `Network`)

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| uid | string | YES | System-generated UUID |
| name | string | YES | Human-readable name |
| vendor_id | string | YES | Vendor's native identifier |
| vendor | string | YES | Vendor name (aws, azure, gcp, vmware, etc.) |
| vendor_type | string | YES | Original vendor resource type |
| normalised_type | string | YES | Universal taxonomy type |
| category | string | YES | Category from taxonomy (Compute, Storage, Network, etc.) |
| region | string | NO | Geographic region/location |
| state | string | NO | Current state (running, stopped, etc.) |
| classification_confidence | float | NO | 0.0-1.0 confidence in classification |
| classification_method | string | NO | How classified (rule, model, human) |
| first_seen | string | YES | ISO 8601 timestamp |
| last_seen | string | YES | ISO 8601 timestamp |
| raw_properties | map | NO | Vendor-specific properties (preserved as-is) |

**Uniqueness**: Composite key `(vendor_id, vendor)` enforced at the application
layer via upsert logic. AGE does not support unique property constraints natively,
so the service layer uses a Cypher MERGE pattern:

```cypher
MERGE (r:Resource {vendor_id: $vendor_id, vendor: $vendor})
ON CREATE SET r.uid = $uid, r.name = $name, ...
ON MATCH SET r.last_seen = $now, r.name = $name, ...
```

**Multi-Label**: Each resource node carries two labels: `Resource` (base) and its
category (e.g., `Compute`). In AGE, this is achieved by creating with both labels:
```cypher
CREATE (:Resource:Compute {uid: $uid, ...})
```

---

### Relationship Edge

Directed edges between Resource nodes.

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| type | string | YES | Edge label (DEPENDS_ON, HOSTED_ON, etc.) |
| source_collector | string | NO | Which collector reported this |
| confidence | float | YES | 0.0-1.0 |
| established_at | string | YES | ISO 8601 timestamp |
| last_confirmed | string | YES | ISO 8601 timestamp |
| inference_method | string | NO | How discovered (collector, rule, llm) |
| metadata | map | NO | Additional properties |

**Supported Edge Types** (M1):
- `DEPENDS_ON` / `DEPENDED_ON_BY`
- `HOSTED_ON` / `HOSTS`
- `MEMBER_OF` / `CONTAINS`
- `CONNECTED_TO`
- `ATTACHED_TO` / `ATTACHED_FROM`
- `MANAGES` / `MANAGED_BY`
- `ROUTES_TO` / `ROUTED_FROM`
- `PEERS_WITH`

**Creation Pattern**:
```cypher
MATCH (a:Resource {uid: $source_uid}), (b:Resource {uid: $target_uid})
CREATE (a)-[:DEPENDS_ON {
  confidence: $confidence,
  established_at: $now,
  last_confirmed: $now,
  source_collector: $collector
}]->(b)
```

---

## Entity Relationship Diagram

```text
┌─────────────────┐
│  Administrator   │
│  (SQL table)     │
└────────┬────────┘
         │ authenticates via
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Bearer Token   │     │  RevokedToken   │
│  (JWT, in-mem)  │────▶│  (SQL table)    │
└─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│   Credential    │────▶│ CredentialAudit │
│  (SQL table)    │     │   Log (SQL)     │
└─────────────────┘     └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│   Resource      │◀───────▶│  Relationship   │
│  (AGE node)     │  edges  │  (AGE edge)     │
└─────────────────┘         └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│  VaultConfig    │     │  SystemSetting  │
│  (SQL, singleton)│    │  (SQL, KV store)│
└─────────────────┘     └─────────────────┘
```
