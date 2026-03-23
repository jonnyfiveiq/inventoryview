# Feature Specification: Resource Playlists

**Feature Branch**: `005-resource-playlists`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Spotify/Apple Music style playlists for curating bounded resource collections, with REST API consumption, activity tracking, and infrastructure analytics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Manage Playlists (Priority: P1)

As a platform administrator, I want to create named playlists of resources so that I can define bounded inventories that represent logical groupings (e.g., "Production OpenShift Cluster", "DMZ Network Devices", "Database Tier") for governance and external consumption.

Playlists appear in the left navigation sidebar, similar to how playlists appear in Spotify or Apple Music. I can create, rename, and delete playlists from the sidebar. Each playlist has a name and an optional description.

**Why this priority**: Without the ability to create and manage playlists, no other feature can function. This is the foundational capability.

**Independent Test**: Can be fully tested by creating a playlist via the sidebar, verifying it appears in the navigation, renaming it, and deleting it. Delivers the core organisational structure.

**Acceptance Scenarios**:

1. **Given** I am logged in, **When** I click a "New Playlist" button in the sidebar, **Then** a new playlist is created with a default name and I can immediately rename it inline.
2. **Given** a playlist exists in the sidebar, **When** I right-click or use an actions menu on it, **Then** I can rename or delete it.
3. **Given** I delete a playlist, **When** the deletion is confirmed, **Then** the playlist and its membership records are removed, and it disappears from the sidebar.
4. **Given** multiple playlists exist, **When** I view the sidebar, **Then** all playlists are listed in alphabetical order under a "Playlists" section.

---

### User Story 2 - Add Resources to Playlists (Priority: P1)

As a platform administrator, I want to add any resource to one or more playlists so that I can build up curated collections over time. From any resource detail page, I can add that resource to a playlist. A resource can belong to multiple playlists.

**Why this priority**: Equally critical as playlist creation — without adding resources, playlists have no content. Co-priority with US1.

**Independent Test**: Can be tested by navigating to a resource detail page, adding it to an existing playlist, then verifying it appears in the playlist members view.

**Acceptance Scenarios**:

1. **Given** I am viewing a resource detail page and playlists exist, **When** I click an "Add to Playlist" button, **Then** I see a dropdown or modal listing available playlists with checkboxes showing which playlists already contain this resource.
2. **Given** a resource is not in a playlist, **When** I select that playlist from the add menu, **Then** the resource is added and a confirmation is shown.
3. **Given** a resource is already in a playlist, **When** I uncheck that playlist, **Then** the resource is removed from that playlist.
4. **Given** I am viewing a playlist, **When** I want to remove a member, **Then** I can remove it directly from the playlist detail view.

---

### User Story 3 - View Playlist Members (Priority: P1)

As a platform administrator, I want to click on a playlist in the sidebar and see all its member resources so that I can review and manage the contents of my curated collection.

The playlist detail page shows a table of member resources with key attributes (name, vendor, type, category, state) and the ability to click through to individual resource detail pages. Members can be removed from this view.

**Why this priority**: Core viewing capability that makes playlists useful. Without seeing members, playlists have no visibility.

**Independent Test**: Can be tested by clicking a populated playlist in the sidebar and verifying all member resources are listed with correct attributes and navigation links.

**Acceptance Scenarios**:

1. **Given** I click a playlist in the sidebar, **When** the playlist detail page loads, **Then** I see a table listing all member resources with name, vendor, type, category, and state columns.
2. **Given** a playlist has members, **When** I click a resource row, **Then** I navigate to that resource's detail page.
3. **Given** an empty playlist, **When** I view it, **Then** I see a helpful empty state message suggesting how to add resources.
4. **Given** a playlist with many members, **When** I view it, **Then** results are paginated or scrollable without performance degradation.

---

### User Story 4 - REST API for External Clients (Priority: P2)

As an external system (e.g., Ansible Automation Platform, Nexus), I want to retrieve a playlist's resources via a REST endpoint so that I can consume a guardrailed, bounded inventory of resources for automation, provisioning, or compliance purposes.

The endpoint returns a JSON representation of the playlist and its member resources. This is the primary integration point for external consumers.

**Why this priority**: The core business value — serving bounded inventories to clients. Depends on playlists and membership existing (US1-3).

**Independent Test**: Can be tested by making a GET request to the playlist endpoint and verifying the JSON response contains the expected playlist metadata and member resources.

**Acceptance Scenarios**:

1. **Given** a playlist with members exists, **When** an authenticated client makes a GET request for that playlist, **Then** the response contains the playlist metadata and a list of member resources with their full details.
2. **Given** a playlist exists, **When** a client requests it by its unique identifier, **Then** the response is well-structured JSON suitable for machine consumption.
3. **Given** an invalid or non-existent playlist identifier, **When** a client requests it, **Then** a 404 response is returned with a clear error message.
4. **Given** an unauthenticated request, **When** the endpoint is called, **Then** a 401 response is returned.

---

### User Story 5 - JSON Preview in UI (Priority: P2)

As a platform administrator, I want to click a "JSON" button on a playlist detail page to see exactly what external clients would receive when calling the REST endpoint, so that I can verify the output before sharing the endpoint with integration teams.

**Why this priority**: Builds trust and transparency for the API integration. Depends on the REST endpoint (US4) being defined.

**Independent Test**: Can be tested by clicking the JSON preview button on a playlist and verifying the displayed JSON matches the REST endpoint response format.

**Acceptance Scenarios**:

1. **Given** I am viewing a playlist detail page, **When** I click a "JSON" button, **Then** a panel or modal displays the formatted JSON payload that the REST endpoint would return.
2. **Given** the JSON preview is displayed, **When** I review it, **Then** it matches exactly what a GET request to the playlist endpoint would return.
3. **Given** the JSON preview is open, **When** I want to copy it, **Then** I can copy the JSON content to clipboard.

---

### User Story 6 - Playlist Activity Log and Calendar Heatmap (Priority: P3)

As a platform administrator, I want to see an activity history for a playlist so that I can track changes over time — who added or removed resources and when. I also want a calendar heatmap visualisation (the same style used for drift tracking) to see the frequency and pattern of playlist changes at a glance.

**Why this priority**: Audit and governance value. Depends on playlists being functional (US1-3).

**Independent Test**: Can be tested by making several changes to a playlist (add/remove resources), then viewing the activity log and verifying entries appear, and the calendar heatmap reflects activity on the correct dates.

**Acceptance Scenarios**:

1. **Given** resources have been added to and removed from a playlist, **When** I view the playlist detail page, **Then** I see an activity log showing each change with timestamp, action (added/removed), and the affected resource.
2. **Given** a playlist has activity history, **When** I view the calendar heatmap on the playlist page, **Then** days with more changes show darker shading, and I can click a day to see that day's activity.
3. **Given** a new playlist with no activity, **When** I view the calendar heatmap, **Then** it displays an empty calendar with no highlighted days.
4. **Given** I click a day on the calendar heatmap, **When** activity exists for that day, **Then** the activity log filters to show only that day's entries.

---

### User Story 7 - Infrastructure Donut Charts on Playlist (Priority: P3)

As a platform administrator, I want to see infrastructure donut charts on the playlist detail page showing the breakdown of resources by infrastructure type (Private Cloud, Public Cloud, Networking, Storage) so that I can understand the composition of my curated collection at a glance.

**Why this priority**: Analytics and visual insight. Depends on playlist membership existing (US1-3). Reuses the existing donut chart component.

**Independent Test**: Can be tested by creating a playlist with resources from multiple infrastructure types and verifying the donut charts accurately reflect the proportions.

**Acceptance Scenarios**:

1. **Given** a playlist contains resources from multiple infrastructure types, **When** I view the playlist detail page, **Then** donut charts display the count and proportion of resources grouped by Private Cloud, Public Cloud, Networking, and Storage.
2. **Given** a playlist contains only one infrastructure type, **When** I view the donuts, **Then** only the relevant donut chart shows data; empty groups are either omitted or shown as empty.
3. **Given** a playlist is empty, **When** I view the playlist detail page, **Then** the donut charts section is hidden or shows an empty state.

---

### Edge Cases

- What happens when a resource that belongs to a playlist is deleted from the system? The membership record is automatically cleaned up and an activity entry is logged noting the removal was due to resource deletion.
- What happens when a user tries to add a resource that is already in a playlist? The system indicates the resource is already a member and takes no duplicate action.
- What happens when a playlist with members is deleted? The user is prompted with a confirmation that includes the member count. Upon confirmation, all membership and activity records are removed.
- What happens when two users modify the same playlist simultaneously? Standard last-write-wins behaviour; activity log captures both changes independently.
- What is the maximum number of resources in a single playlist? No hard limit enforced by default; the system handles large playlists (1,000+ resources) gracefully with pagination.
- What happens when an external client requests a playlist while it is being modified? The response reflects the state at the time of the request (read consistency).
- What happens when two playlists would produce the same slug? The system appends a numeric suffix to ensure uniqueness (e.g., `prod-cluster`, `prod-cluster-2`).
- What happens to external client bookmarks when a playlist is renamed? The slug changes when renamed; the UUID endpoint continues to work as a stable fallback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authenticated users to create a new playlist with a name and optional description.
- **FR-002**: System MUST allow authenticated users to rename and update the description of an existing playlist.
- **FR-003**: System MUST allow authenticated users to delete a playlist, with confirmation when the playlist contains members.
- **FR-004**: System MUST display all playlists in the left navigation sidebar under a dedicated "Playlists" section, listed alphabetically.
- **FR-005**: System MUST allow users to add any resource to one or more playlists from the resource detail page.
- **FR-006**: System MUST allow users to remove resources from a playlist, both from the playlist detail view and from the resource detail page's "Add to Playlist" control.
- **FR-007**: System MUST prevent duplicate resource entries within a single playlist.
- **FR-008**: System MUST display a playlist detail page showing all member resources in a table with name, vendor, normalised type, category, and state.
- **FR-009**: System MUST expose a REST endpoint that returns a playlist and its member resources as JSON for external client consumption. Playlists are addressable by auto-generated slug (e.g., `/playlists/prod-openshift-cluster`) or by UUID. By default the response includes summary resource fields (name, uid, vendor, normalised_type, category, state); a `?detail=full` query parameter includes all resource fields including raw_properties.
- **FR-010**: System MUST require authentication for all playlist REST endpoints.
- **FR-011**: System MUST provide a JSON preview button on the playlist detail page that displays the exact response the REST endpoint would return.
- **FR-012**: System MUST record an activity entry whenever a resource is added to or removed from a playlist, capturing the timestamp, action type, and affected resource.
- **FR-013**: System MUST display a calendar heatmap on the playlist detail page showing the frequency of playlist changes over time, using the same visual style as the existing drift calendar.
- **FR-014**: System MUST display infrastructure donut charts on the playlist detail page showing the breakdown of member resources by infrastructure type (Private Cloud, Public Cloud, Networking, Storage).
- **FR-015**: System MUST automatically remove playlist membership records when a resource is deleted from the system, and log this as an activity event.
- **FR-016**: System MUST provide a copyable endpoint URL on the playlist detail page so administrators can easily share the REST endpoint with integration teams.

### Key Entities

- **Playlist**: A named, user-created collection with a unique identifier (UUID), an auto-generated URL slug derived from the name, a description, creation timestamp, and last-modified timestamp. The slug is regenerated when the playlist is renamed. Owned by the system (not per-user scoped).
- **Playlist Membership**: The association between a playlist and a resource, recording when the resource was added.
- **Playlist Activity**: An audit record capturing every change to a playlist — action type (resource_added, resource_removed, resource_deleted_from_system, playlist_created, playlist_renamed, playlist_deleted), timestamp, and affected resource identifier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new playlist and add their first resource to it within 30 seconds.
- **SC-002**: External clients can retrieve a playlist's full resource inventory in a single request, with response times under 2 seconds for playlists containing up to 500 resources.
- **SC-003**: The playlist activity log accurately reflects 100% of membership changes, with no lost events.
- **SC-004**: Users can identify the infrastructure composition of a playlist (via donut charts) within 3 seconds of viewing the playlist page.
- **SC-005**: The JSON preview exactly matches the REST endpoint response, with zero discrepancies.
- **SC-006**: A playlist with 1,000 member resources renders its detail page within 3 seconds.
- **SC-007**: All playlist changes are visible in the calendar heatmap within one page refresh.

## Clarifications

### Session 2026-03-22

- Q: How should external clients reference a playlist in the REST URL? → A: Auto-generated slug from playlist name, with UUID as fallback. External-facing URLs use the slug (e.g., `/playlists/prod-openshift-cluster`); internal operations and the UUID endpoint also work as a fallback.
- Q: What level of resource detail should the playlist REST endpoint return per member? → A: Configurable via query parameter. Default response returns summary fields (name, uid, vendor, normalised_type, category, state). Adding `?detail=full` includes all resource fields including raw_properties.

## Assumptions

- Playlists are system-scoped, not per-user. Any authenticated user can view and modify any playlist. Per-user or role-based playlist permissions are out of scope for this iteration.
- The existing authentication mechanism is used for all playlist operations — no new auth flows are needed.
- The infrastructure type grouping (Private Cloud, Public Cloud, Networking, Storage) follows the same vendor mapping already established in the dashboard donut charts.
- The calendar heatmap component already exists for drift tracking and will be reused for playlist activity visualisation.
- The donut chart component already exists and will be reused for playlist infrastructure breakdown.
- External clients authenticate using the same token-based auth as the UI.

## Out of Scope

- Per-user playlist ownership or role-based access control on individual playlists.
- Playlist sharing or collaboration features beyond system-wide visibility.
- Automatic/dynamic playlist membership based on rules or filters (all membership is manual).
- Playlist ordering or drag-and-drop reordering of members.
- Playlist import/export beyond the REST endpoint.
- Webhooks or push notifications for playlist changes.
