# Research: Resource Playlists

**Feature**: 005-resource-playlists
**Date**: 2026-03-22

## R1: Storage — Graph vs Relational for Playlists

**Decision**: Use standard PostgreSQL tables (not Apache AGE graph).

**Rationale**: The constitution explicitly states "Metadata and administrative data (credentials, user accounts, configuration) MAY use standard PostgreSQL tables alongside the graph." Playlists are user-curated administrative groupings, not discovered infrastructure relationships. They don't benefit from Cypher traversal — they are simple CRUD with foreign-key membership. The existing credential and drift subsystems use the same pattern (relational tables alongside the graph).

**Alternatives considered**:
- Graph nodes/edges: Would require MEMBER_OF edges in AGE. Rejected because playlists are not infrastructure relationships — they are human-created boundaries. Mixing administrative grouping with discovered relationships pollutes the graph model.
- Hybrid (graph + relational): Unnecessary complexity for a simple membership model.

## R2: Slug Generation Strategy

**Decision**: Auto-generate URL slugs from playlist name using a deterministic slugify algorithm. Append numeric suffix on collision. UUID always works as fallback.

**Rationale**: External teams (Ansible, Nexus) need human-readable, bookmarkable URLs. A slug like `/playlists/prod-openshift-cluster` is far more usable in automation playbooks than a UUID. The UUID fallback ensures stability when playlists are renamed.

**Alternatives considered**:
- UUID only: Machine-friendly but poor DX for external integrators who configure endpoints manually.
- User-defined slugs: More control but adds UX complexity and validation burden. Auto-generated covers 95% of cases.

## R3: Activity Log Storage

**Decision**: Dedicated `playlist_activity` table with denormalised resource name/vendor for historical readability.

**Rationale**: Activity entries must persist even after a resource is deleted from the system (the log should still show "removed vm-7020 from playlist"). Denormalising the resource name at write time ensures the activity log remains readable regardless of resource lifecycle. This matches the pattern used by `credential_audit_log`.

**Alternatives considered**:
- Normalised (foreign key only): Loses context when resources are deleted. Would show orphaned UIDs.
- Event sourcing: Overkill for a simple audit trail. Standard append-only table suffices.

## R4: Calendar Heatmap Reuse

**Decision**: Reuse existing `DriftCalendar` component by abstracting it to accept a generic timeline data source, or create a parallel `PlaylistCalendar` that uses the same `CalendarGrid`/`CalendarCell`/`CalendarNav` sub-components.

**Rationale**: The existing drift calendar has mode support (`resource` | `fleet`). Adding a `playlist` mode or creating a thin wrapper that feeds playlist activity data into the same grid components avoids duplication. The sub-components (`CalendarGrid`, `CalendarCell`, `CalendarNav`, `CalendarLegend`) are already well-factored.

**Alternatives considered**:
- Fork the calendar: Creates maintenance burden with duplicate code.
- Generic calendar library: Adds external dependency for something already built.

## R5: REST Response Detail Levels

**Decision**: Default response returns summary fields (name, uid, vendor, normalised_type, category, state). `?detail=full` adds all resource fields including raw_properties.

**Rationale**: Most external consumers (Ansible inventory, Nexus) need the summary for resource identification and routing. Full detail with raw_properties can be large (hundreds of KB per resource) and is only needed for deep integration scenarios. Making it opt-in keeps default payloads fast and small.

**Alternatives considered**:
- Always full detail: Large payloads for simple inventory use cases.
- Always summary only: Forces consumers to make N+1 calls for full detail.

## R6: Playlist Listing Endpoint

**Decision**: Provide `GET /api/v1/playlists` endpoint listing all playlists with member count, in addition to the detail endpoint. This supports the sidebar population and external client discovery.

**Rationale**: The sidebar needs a lightweight list of playlists with just name, slug, and member count. External clients also need to discover available playlists. Cursor-based pagination follows the existing API pattern.

**Alternatives considered**:
- No list endpoint (sidebar fetches all): Works for small numbers but doesn't scale. API consistency demands a list endpoint.
