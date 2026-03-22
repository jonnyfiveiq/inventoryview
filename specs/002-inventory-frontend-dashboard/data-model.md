# Data Model: InventoryView Frontend Dashboard

**Feature**: 002-inventory-frontend-dashboard
**Date**: 2026-03-22

## Frontend TypeScript Types

The frontend does not own data storage — all entities are received from and sent to the backend API. These types represent the client-side shape of API responses.

### Resource

The core entity. Represents an infrastructure asset discovered by a collector.

```typescript
interface Resource {
  uid: string;                       // UUID, primary identifier
  name: string;                      // Human-readable name
  vendor_id: string;                 // Vendor-specific identifier (e.g. vm-123)
  vendor: string;                    // Source platform: "vmware", "aws", "azure", "openshift"
  vendor_type: string;               // Original vendor type (e.g. "VirtualMachine")
  normalised_type: string;           // Universal type: "virtual_machine", "hypervisor", etc.
  category: string;                  // Top-level: "compute", "storage", "network", "management"
  region: string | null;             // Geographic/logical region
  state: string | null;              // Current state: "poweredOn", "poweredOff", "maintenance", etc.
  classification_confidence: number | null;  // 0.0-1.0
  classification_method: string | null;      // "rules", "llm", "manual"
  first_seen: string;               // ISO 8601 datetime
  last_seen: string;                 // ISO 8601 datetime
  raw_properties: Record<string, unknown> | null;  // Full vendor properties (detail view only)
}
```

**Used in**: ResourceCard (carousel), ResourceTable (provider drill-down), ResourceDetailPage, graph node tooltips.

**Uniqueness**: `uid` is globally unique. `vendor_id` + `vendor` is the natural key used for upsert.

### Relationship (Edge)

A directed connection between two resources.

```typescript
interface Relationship {
  source_uid: string;                // Source resource UID
  target_uid: string;                // Target resource UID
  type: EdgeType;                    // Relationship type enum
  confidence: number;                // 0.0-1.0
  source_collector: string | null;   // Which collector reported this
  established_at: string;            // ISO 8601
  last_confirmed: string;            // ISO 8601
  inference_method: string | null;   // "collector", "rules", "llm"
  metadata: Record<string, unknown> | null;
}

type EdgeType =
  | "DEPENDS_ON"
  | "HOSTED_ON"
  | "MEMBER_OF"
  | "CONNECTED_TO"
  | "ATTACHED_TO"
  | "MANAGES"
  | "ROUTES_TO"
  | "CONTAINS"
  | "PEERS_WITH";
```

**Used in**: Graph edges (colour-coded by type), relationship lists on resource detail.

### SubgraphResponse

Response from the graph traversal endpoint.

```typescript
interface SubgraphNode {
  uid: string;
  name: string;
  category: string;
  vendor: string;
  normalised_type: string;           // Used for node shape mapping in graph
}

interface SubgraphEdge {
  source_uid: string;
  target_uid: string;
  type: string;
  confidence: number;
}

interface SubgraphResponse {
  nodes: SubgraphNode[];
  edges: SubgraphEdge[];
}
```

**Used in**: GraphCanvas (Cytoscape.js nodes/edges), GraphOverlay.

### PaginatedResponse

Wrapper for all list endpoints using cursor-based pagination.

```typescript
interface PaginatedResponse<T> {
  data: T[];
  next_cursor: string | null;        // null when no more pages
  page_size: number;
}
```

**Used in**: ResourceTable pagination, carousel data loading.

### AuthSession

Client-side session state.

```typescript
interface AuthSession {
  token: string;                      // JWT bearer token
  token_type: "bearer";
  expires_at: string;                 // ISO 8601
}

interface LoginRequest {
  username: string;
  password: string;
}

interface SetupStatus {
  setup_complete: boolean;
}
```

**Used in**: Auth store (Zustand), login page, route guards.

### Heatmap Aggregations

Derived client-side from resource list data. Not a backend entity.

```typescript
interface CategoryCount {
  category: string;                   // "compute", "storage", "network", "management"
  count: number;
}

interface StateDistribution {
  state: string;                      // "poweredOn", "poweredOff", "maintenance", etc.
  count: number;
}

interface ActivityEntry {
  uid: string;
  name: string;
  normalised_type: string;
  last_seen: string;                  // Used for recency colour
}
```

**Used in**: HeatmapStrip (landing page), HeatmapDetail (analytics page).

### Drift Types

Types for tracking resource configuration changes over time.

```typescript
interface DriftEntry {
  id: string;                          // UUID
  resource_uid: string;                // Resource this drift belongs to
  field: string;                       // Field that changed (e.g. "state", "num_cpu", "memory_mb")
  old_value: string | null;            // Previous value (null for first observation)
  new_value: string | null;            // New value (null if removed)
  changed_at: string;                  // ISO 8601 datetime
  source: string;                      // What detected the change (e.g. "collector")
}

interface DriftResponse {
  data: DriftEntry[];
}

interface DriftExistsResponse {
  has_drift: boolean;
}
```

**Used in**: DriftModal (resource detail page), drift history button visibility check.

### Vendor Aggregation

Derived client-side for the vendor carousel. Not a backend entity.

```typescript
interface VendorInfo {
  name: string;                        // Vendor name (e.g. "vmware", "aws")
  count: number;                       // Total resources
  types: number;                       // Number of distinct normalised_types
  color: string;                       // Vendor-specific colour
  borderColor: string;                 // Vendor-specific border colour
}
```

**Used in**: VendorCarousel (landing page).

## State Transitions

### Auth Flow

```
UNAUTHENTICATED → (login success) → AUTHENTICATED → (token expiry / revoke) → UNAUTHENTICATED
                → (setup incomplete) → SETUP_REQUIRED → (setup complete) → UNAUTHENTICATED
```

### Graph Overlay

```
CLOSED → (click graph icon / "View Graph") → LOADING → (data received) → INTERACTIVE
INTERACTIVE → (change depth) → LOADING → INTERACTIVE
INTERACTIVE → (click peripheral node) → EXPANDING → INTERACTIVE
INTERACTIVE → (close overlay) → CLOSED
```

## Relationships Between Frontend Entities

- **Resource → Relationship**: A resource has many relationships (edges where it is source or target).
- **Resource → SubgraphNode**: The graph view shows a resource as a node with simplified properties.
- **Resource → CategoryCount/StateDistribution**: Resources are aggregated for heatmap display.
- **AuthSession → all pages**: Auth token is required for every API call except health and setup status.
- **Resource → DriftEntry**: A resource has zero or more drift entries recording its configuration changes over time.
- **Resource → VendorInfo**: Resources are aggregated by vendor for the vendor carousel display.
- **SubgraphNode → normalised_type**: The graph uses normalised_type to determine node shapes (ellipse, hexagon, barrel, diamond, etc.).
