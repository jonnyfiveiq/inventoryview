# Data Model: Resource Playlists

**Feature**: 005-resource-playlists
**Date**: 2026-03-22

## Entities

### Playlist

Represents a named, curated collection of resources.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| name | text | NOT NULL, max 255 chars | Display name |
| slug | text | NOT NULL, UNIQUE | URL-friendly identifier derived from name |
| description | text | nullable | Optional description of the playlist's purpose |
| created_at | timestamp with timezone | NOT NULL, default now() | When the playlist was created |
| updated_at | timestamp with timezone | NOT NULL, default now() | Last modification time (name, description, or membership change) |

**Indexes**:
- `UNIQUE(slug)` — for REST endpoint resolution
- `(name)` — for alphabetical sidebar listing

**Slug generation rules**:
- Lowercase, alphanumeric and hyphens only
- Spaces and special characters replaced with hyphens
- Consecutive hyphens collapsed
- Leading/trailing hyphens stripped
- On collision, append `-2`, `-3`, etc.
- Regenerated on rename

### Playlist Membership

Associates a resource with a playlist. A resource can belong to multiple playlists.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| playlist_id | UUID | NOT NULL, FK → playlist.id ON DELETE CASCADE | The playlist |
| resource_uid | text | NOT NULL | The resource UID (from the graph) |
| added_at | timestamp with timezone | NOT NULL, default now() | When the resource was added |

**Indexes**:
- `UNIQUE(playlist_id, resource_uid)` — prevents duplicates (FR-007)
- `(resource_uid)` — for looking up which playlists contain a resource
- `(playlist_id)` — for listing members of a playlist

**Cascade behaviour**:
- Deleting a playlist cascades to all its membership records
- Deleting a resource from the graph should trigger application-level cleanup of membership records + activity logging (FR-015)

### Playlist Activity

Append-only audit log capturing every change to a playlist.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| playlist_id | UUID | NOT NULL, FK → playlist.id ON DELETE CASCADE | The playlist this activity belongs to |
| action | text | NOT NULL, CHECK constraint | One of: `playlist_created`, `playlist_renamed`, `playlist_deleted`, `resource_added`, `resource_removed`, `resource_deleted_from_system` |
| resource_uid | text | nullable | The affected resource UID (null for playlist-level actions) |
| resource_name | text | nullable | Denormalised resource name at time of action (for historical readability) |
| resource_vendor | text | nullable | Denormalised resource vendor at time of action |
| detail | text | nullable | Additional context (e.g., old name on rename, deletion reason) |
| occurred_at | timestamp with timezone | NOT NULL, default now() | When the action occurred |

**Indexes**:
- `(playlist_id, occurred_at)` — for timeline queries and calendar heatmap
- `(occurred_at)` — for date-range filtering

**Design notes**:
- Resource name and vendor are denormalised at write time so the activity log remains readable even after resource deletion
- The `detail` field captures contextual info: for renames it stores the old name, for system deletions it notes "resource deleted from system"
- No foreign key on `resource_uid` since the resource may be deleted

## Relationships

```
Playlist 1 ──── * Playlist Membership * ──── 1 Resource (graph node)
    │
    └── 1 ──── * Playlist Activity
```

- A **Playlist** has zero or more **Memberships** (one per resource)
- A **Resource** can appear in zero or more **Playlists** (many-to-many via Membership)
- A **Playlist** has zero or more **Activity** entries (append-only log)
- Deleting a **Playlist** cascades to both its Memberships and Activity records
- Deleting a **Resource** triggers application-level cleanup: removes Membership rows and creates `resource_deleted_from_system` Activity entries

## State Transitions

### Playlist Lifecycle

```
[Created] → playlist_created activity logged
    │
    ├── Rename → playlist_renamed activity logged, slug regenerated, updated_at refreshed
    ├── Add resource → resource_added activity logged, membership created, updated_at refreshed
    ├── Remove resource → resource_removed activity logged, membership deleted, updated_at refreshed
    │
    └── [Deleted] → playlist_deleted activity logged, then CASCADE removes memberships and activities
```

No soft-delete. Deletion is permanent with confirmation prompt in the UI.
