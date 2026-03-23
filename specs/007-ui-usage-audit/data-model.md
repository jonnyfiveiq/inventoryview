# Data Model: UI Usage Analytics & Audit Tracking

## Entity: usage_event

Stores individual UI interaction events from authenticated users.

| Field         | Type         | Constraints                  | Description                                    |
|---------------|--------------|------------------------------|------------------------------------------------|
| id            | UUID         | PK, auto-generated           | Unique event identifier                        |
| feature_area  | VARCHAR(100) | NOT NULL, indexed            | Logical grouping (e.g. "Drift Detection")      |
| action        | VARCHAR(100) | NOT NULL                     | Specific action (e.g. "graph_overlay_opened")  |
| user_id       | UUID         | NOT NULL, FK → administrators| User who performed the action                  |
| created_at    | TIMESTAMPTZ  | NOT NULL, DEFAULT now(), indexed | When the event occurred                     |

**Indexes**:
- `ix_usage_event_feature_area` on (feature_area)
- `ix_usage_event_created_at` on (created_at)
- Composite index on (feature_area, created_at) for dashboard aggregation queries

**Retention**: Rows older than 90 days are purged via lazy scheduled DELETE.

**Notes**:
- No target context (resource UID, etc.) is stored per clarification decision.
- Feature areas are free-form strings discovered dynamically — no FK to a feature area table.
- The `action` field uses snake_case convention (e.g. `page_view`, `graph_overlay_opened`, `drift_timeline_expanded`).

---

## Entity: login_audit

Stores all login attempts (successful and failed) for security auditing.

| Field          | Type         | Constraints                  | Description                                    |
|----------------|--------------|------------------------------|------------------------------------------------|
| id             | UUID         | PK, auto-generated           | Unique audit entry identifier                  |
| username       | VARCHAR(150) | NOT NULL                     | Username attempted (may not exist in system)    |
| outcome        | VARCHAR(20)  | NOT NULL                     | "success" or "failure"                         |
| failure_reason | VARCHAR(200) | NULL                         | Reason for failure (NULL on success)           |
| ip_address     | VARCHAR(45)  | NOT NULL                     | Client IP address (IPv4 or IPv6)               |
| created_at     | TIMESTAMPTZ  | NOT NULL, DEFAULT now(), indexed | When the attempt occurred                   |

**Indexes**:
- `ix_login_audit_created_at` on (created_at)
- `ix_login_audit_username` on (username)

**Retention**: Same 90-day purge policy as usage_event.

**Notes**:
- `username` is stored as a plain string, not as a FK to administrators, because failed attempts may use non-existent usernames.
- `ip_address` uses VARCHAR(45) to accommodate IPv6 addresses.
- `outcome` is constrained to "success" or "failure" values.

---

## Relationships

```text
administrators (1) ──→ (N) usage_event     [user_id FK]
login_audit has no FK relationships (username is free-text for failed attempts)
```

## Feature Area Convention

Feature areas are string constants defined in the tracking instrumentation. Initial values:

| Feature Area         | Example Actions                                              |
|----------------------|--------------------------------------------------------------|
| Resource Browsing    | page_view, search_executed                                   |
| Graph Visualisation  | graph_overlay_opened, node_expanded, depth_changed           |
| Drift Detection      | drift_timeline_expanded, drift_comparison_viewed             |
| Asset Linkages       | asset_chain_link_clicked, asset_chain_viewed                 |
| Automation Metrics   | metrics_uploaded, correlation_run, review_action_taken        |
| Playlists            | playlist_created, playlist_edited, playlist_member_added      |
| Navigation           | sidebar_section_expanded, page_navigated                     |

New feature areas appear automatically in the dashboard when new event types are tracked.
