# Feature Specification: InventoryView Frontend Dashboard

**Feature Branch**: `002-inventory-frontend-dashboard`
**Created**: 2026-03-22
**Status**: Implemented
**Input**: User description: "Build a frontend web application for InventoryView with Netflix-style landing page, carousels by normalised taxonomy, heatmaps, provider drill-down, graph visualization, and dark theme."

## Clarifications

### Session 2026-03-22

- Q: Where should heatmaps live in the application layout? → A: Both — compact summary on landing page above carousels, plus a detailed analytics page accessible from navigation.
- Q: How should resource details be presented? → A: Full page — clicking a resource navigates to a dedicated resource detail page.
- Q: How should the graph view be presented and accessed? → A: Overlay/modal on top of the current page, triggered by clicking a graph icon in the resource table row's graph column. Also accessible from the resource detail page.
- Q: What persistent navigation pattern should the application use? → A: Left sidebar navigation (collapsible) with icon + label for each section (Home, Providers, Analytics).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Landing Page with Taxonomy Carousels (Priority: P1)

An infrastructure operator opens InventoryView and immediately sees a Netflix-style landing page presenting their entire infrastructure inventory at a glance. The page displays horizontal, scrollable carousels — one per normalised resource type (virtual machines, hypervisors, datastores, clusters, networks, datacenters, etc.). Each carousel contains resource cards showing the resource name, provider/vendor badge, current state, and key metadata. The operator can scroll through each carousel to browse resources without leaving the page. Carousels only appear for types that have resources in the system.

**Why this priority**: This is the primary entry point to the application. Without a landing page, there is no application. The carousel layout provides immediate situational awareness across the entire inventory and is the foundation all other features build upon.

**Independent Test**: Can be fully tested by authenticating, loading the landing page, and verifying that carousels render with resource cards grouped by normalised type. Delivers standalone value as a visual inventory browser.

**Acceptance Scenarios**:

1. **Given** the operator is authenticated and resources exist in the backend, **When** they navigate to the landing page, **Then** they see one carousel per normalised resource type that contains at least one resource.
2. **Given** a carousel contains more resources than fit on screen, **When** the operator clicks a scroll arrow or swipes, **Then** the carousel scrolls to reveal additional resource cards.
3. **Given** a resource card is displayed, **When** the operator views it, **Then** it shows the resource name, vendor/provider badge (e.g. VMware, AWS), current state with a colour indicator, and a summary of key properties.
4. **Given** the operator clicks a resource card, **When** the application navigates to the resource detail page, **Then** they see full resource properties, metadata, timestamps (first seen, last seen), and a link to view its relationships.
5. **Given** the system has no resources for a particular normalised type, **When** the landing page loads, **Then** no carousel is shown for that empty type.

---

### User Story 2 - Provider Drill-Down with Filtering (Priority: P2)

An operator wants to focus on a specific provider (e.g. VMware, AWS, Azure, OpenShift). They select a provider from the landing page or navigation, and see a dedicated provider view listing all resources from that provider. The list supports filtering by category, state, region, and normalised type. Pagination allows navigating large inventories. The operator can sort and search within the provider view.

**Why this priority**: After seeing the high-level overview, the most common next action is drilling into a specific provider to inspect its resources. This is the primary navigation path for day-to-day use.

**Independent Test**: Can be tested by navigating to a provider view and verifying resource listing, filtering, and pagination work correctly against the backend API.

**Acceptance Scenarios**:

1. **Given** the operator is on the landing page, **When** they click a provider name or badge, **Then** they are taken to a provider-specific view showing all resources for that vendor.
2. **Given** the operator is in a provider view, **When** they apply a filter (e.g. category=compute, state=poweredOn), **Then** the resource list updates to show only matching resources.
3. **Given** the provider has more resources than one page, **When** the operator scrolls to the bottom or clicks "load more", **Then** additional resources are loaded via cursor-based pagination.
4. **Given** the operator is in a provider view, **When** they click a resource row, **Then** the application navigates to the resource detail page showing full properties and a button to view the resource graph.
5. **Given** no resources match the applied filters, **When** the list is empty, **Then** a clear "no results" message is displayed with a suggestion to adjust filters.

---

### User Story 3 - Interactive Graph Visualization (Priority: P3)

At any point while browsing resources, the operator can open a graph view overlay that visualises the relationships around a selected resource. The graph is triggered by clicking a graph icon in the resource table's graph column (in the provider drill-down view) or via a "View Graph" button on the resource detail page. The graph opens as a full-screen overlay/modal on top of the current page. It shows nodes (resources) connected by edges (relationships) with labels indicating the relationship type (DEPENDS_ON, HOSTED_ON, MEMBER_OF, CONTAINS, CONNECTED_TO, ATTACHED_TO, MANAGES, etc.). The operator can adjust traversal depth, pan and zoom the graph, click nodes to inspect them, and expand the graph by clicking on peripheral nodes. Relationship types are colour-coded for quick visual parsing. Closing the overlay returns the operator to the page they were on.

**Why this priority**: Graph visualization is the key differentiator of InventoryView — it surfaces hidden dependencies and topology. It requires the landing page and resource views to exist first so the operator has a resource to start from.

**Independent Test**: Can be tested by selecting any resource, opening the graph view, and verifying that nodes, edges, and relationship labels render correctly. Interaction (zoom, pan, click-to-expand) can be tested independently.

**Acceptance Scenarios**:

1. **Given** the operator is in the provider resource table, **When** they click the graph icon on a resource row, **Then** a full-screen graph overlay opens centred on that resource showing its immediate relationships.
1a. **Given** the operator is on a resource detail page, **When** they click "View Graph", **Then** the same graph overlay opens centred on that resource.
2. **Given** the graph is displayed with default depth, **When** the operator increases the depth slider, **Then** additional levels of connected resources appear in the graph.
3. **Given** the graph is displayed, **When** the operator clicks a node, **Then** a tooltip or panel shows that resource's name, type, vendor, state, and key properties.
4. **Given** the graph has many nodes, **When** the operator uses mouse wheel or pinch gesture, **Then** the graph zooms in/out smoothly.
5. **Given** the graph is displayed, **When** the operator clicks on a peripheral node, **Then** the graph expands to show that node's relationships (lazy expansion).
6. **Given** different relationship types exist, **When** the graph renders, **Then** each relationship type has a distinct colour and the edges are labelled with the relationship type.

---

### User Story 4 - Infrastructure Heatmaps (Priority: P4)

The operator wants to understand the density, distribution, and activity across their infrastructure at a glance. A compact heatmap summary strip appears at the top of the landing page (above the carousels) showing key metrics: resource counts by category, state distribution, and a mini activity indicator. For deeper analysis, a dedicated Analytics page (accessible from navigation) provides full-size heatmaps with resource counts by category (compute, storage, network, management), state distribution across the inventory (running, stopped, maintenance, etc.), and recently changed resources highlighted by recency. Both views update when the page loads.

**Why this priority**: Heatmaps provide operational intelligence beyond simple listing. They help operators spot anomalies (e.g. too many stopped VMs, storage filling up). This is additive to the core browsing experience.

**Independent Test**: Can be tested by loading the heatmap view and verifying that category counts, state distributions, and activity indicators render correctly based on the data in the backend.

**Acceptance Scenarios**:

1. **Given** resources exist across multiple categories, **When** the operator views the heatmap section, **Then** a category heatmap shows the count of resources per category with colour intensity proportional to count.
2. **Given** resources exist in various states, **When** the operator views the state distribution, **Then** a visual breakdown shows how many resources are in each state (e.g. poweredOn, poweredOff, maintenance, connected).
3. **Given** resources have been recently modified, **When** the operator views the activity heatmap, **Then** recently changed resources are highlighted with warmer colours indicating more recent changes.
4. **Given** the operator hovers over a heatmap cell, **When** the tooltip appears, **Then** it shows the exact count and a label for that cell (e.g. "compute: 15 resources").

---

### User Story 5 - Authentication and Session Management (Priority: P5)

The operator must log in before accessing any dashboard functionality. The login screen accepts username and password, authenticates against the backend, and stores the session token. If the token expires or is revoked, the operator is redirected to the login screen with a clear message. The application handles first-time setup detection gracefully.

**Why this priority**: Authentication is a prerequisite for all features, but it is a cross-cutting concern rather than a user-facing feature. It is lower priority because it is a known, well-understood pattern with no design risk.

**Independent Test**: Can be tested by attempting to access a protected page without a token (redirected to login), logging in (token stored), and verifying that token expiry redirects back to login.

**Acceptance Scenarios**:

1. **Given** the operator is not authenticated, **When** they navigate to any page, **Then** they are redirected to the login screen.
2. **Given** the operator is on the login screen, **When** they enter valid credentials and submit, **Then** they are authenticated and redirected to the landing page.
3. **Given** the operator enters invalid credentials, **When** they submit, **Then** an error message is displayed without revealing which field was wrong.
4. **Given** the operator is authenticated, **When** their token expires, **Then** the next request redirects them to login with a "session expired" message.
5. **Given** the backend has not completed initial setup, **When** the operator navigates to the app, **Then** they see a setup prompt to create the initial administrator account.

---

### Edge Cases

- What happens when the backend is unreachable? The application displays a connection error banner with a retry option, not a blank page.
- What happens when a resource has no relationships? The graph view shows a single node with a message "No relationships found" rather than an empty canvas.
- What happens when the operator's browser window is narrow (mobile/tablet)? Carousels stack vertically, resource cards resize, and the graph view remains functional with touch gestures.
- What happens when the operator navigates to a resource that has been deleted? A "Resource not found" message is shown with a link back to the landing page.
- What happens when the backend returns an error during pagination? The existing results remain visible and an inline error message offers to retry loading the next page.
- What happens when there are hundreds of nodes in the graph? The graph caps visible nodes at a configurable limit and shows a "showing N of M" indicator, allowing the operator to expand further on demand.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST display a landing page with horizontal, scrollable carousels grouped by normalised resource type.
- **FR-002**: Each resource card MUST show the resource name, vendor/provider badge, current state indicator, and key property summary.
- **FR-003**: The application MUST provide a provider drill-down view listing all resources for a selected vendor in a table with filtering by category, state, region, and normalised type. Each row MUST include a graph icon column that opens the graph overlay for that resource.
- **FR-004**: The provider view MUST support cursor-based pagination matching the backend API pattern.
- **FR-005**: The application MUST provide an interactive graph visualization as a full-screen overlay/modal, accessible via a graph icon in the resource table and a "View Graph" button on the resource detail page.
- **FR-006**: The graph view MUST support adjustable traversal depth, pan, zoom, click-to-inspect nodes, and lazy expansion of peripheral nodes.
- **FR-007**: Relationship edges in the graph MUST be colour-coded by type (DEPENDS_ON, HOSTED_ON, MEMBER_OF, CONTAINS, CONNECTED_TO, ATTACHED_TO, MANAGES, etc.).
- **FR-008**: The landing page MUST display a compact heatmap summary strip above the carousels showing category counts and state distribution.
- **FR-008a**: The application MUST provide a dedicated Analytics page with full-size heatmaps for category counts, state distribution, and activity recency.
- **FR-009**: The application MUST use a dark theme throughout with a modern, clean aesthetic.
- **FR-010**: The application MUST authenticate users via the backend login endpoint and store the session token securely.
- **FR-011**: The application MUST redirect unauthenticated users to the login screen and handle token expiry gracefully.
- **FR-012**: The application MUST detect first-time setup state from the backend and present a setup flow for initial administrator creation.
- **FR-013**: The application MUST display meaningful error states (connection errors, empty results, not found) rather than blank screens.
- **FR-014**: The application MUST be responsive, adapting layout for desktop, tablet, and large monitor screen sizes.
- **FR-015**: The resource detail view MUST show all resource properties, metadata, first_seen/last_seen timestamps, and a link to the graph view.
- **FR-016**: The application MUST provide a collapsible left sidebar navigation with icon and label for each section: Home (landing page), Providers (with sub-items per vendor), and Analytics. The sidebar collapses to icon-only mode to maximise content area.

### Key Entities

- **Resource**: An infrastructure asset identified by uid, with a name, vendor, vendor_id, vendor_type, normalised_type, category, region, state, and raw properties. Displayed in carousels, lists, detail views, and graph nodes.
- **Relationship**: A directed connection between two resources with a type label (e.g. DEPENDS_ON, HOSTED_ON), confidence score, and optional metadata. Displayed as graph edges.
- **Provider/Vendor**: A grouping of resources by their source platform (VMware, AWS, Azure, OpenShift). Used for navigation and drill-down.
- **Normalised Type**: A vendor-agnostic classification of resources (virtual_machine, hypervisor, datastore, cluster, virtual_switch, port_group, datacenter, management_plane, resource_pool, subnet). Used to organise carousels on the landing page.
- **Session**: The authenticated user's bearer token, expiry time, and username. Managed client-side for API authorisation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can identify all resources of a given type within 5 seconds of landing page load by scanning the relevant carousel.
- **SC-002**: Operators can navigate from the landing page to a filtered provider view in under 3 clicks.
- **SC-003**: The graph visualization for a resource with up to 50 connected nodes renders and becomes interactive within 2 seconds.
- **SC-004**: 90% of operators can find the dependency chain for a given resource on their first attempt without instructions.
- **SC-005**: The landing page loads and displays all carousels within 3 seconds on a standard broadband connection.
- **SC-006**: Heatmaps accurately reflect the current state of the inventory and update on each page load.
- **SC-007**: The application is fully usable on screens from 1280px to 3840px wide without horizontal scrolling or layout breakage.
- **SC-008**: Authentication flow (login to landing page) completes in under 5 seconds.

## Assumptions

- The existing InventoryView backend API at `/api/v1/` is the sole data source. No direct database access is needed.
- The backend API contract (endpoints, request/response shapes) is stable and will not change during frontend development.
- The application will be deployed as a static web application served separately from the backend, communicating via HTTP.
- Standard web browser capabilities (modern Chrome, Firefox, Safari, Edge) are sufficient; no desktop application wrapper is needed.
- The initial release targets desktop browsers; mobile optimization is a future enhancement (responsive layout is included but not a primary target).
- The dark theme is the only theme for the initial release; a light theme toggle is not in scope.
- Resource counts per environment are expected to be in the low thousands (not millions); extreme scale optimization is not required for the initial release.

### User Story 6 - Resource Drift Tracking (Priority: P6)

An operator wants to understand how a resource's configuration has changed over time. When viewing a resource that has recorded drift entries (e.g. state changes, CPU/memory modifications, IP address changes), a "Drift History" button appears on the resource detail page. Clicking it opens a modal showing a chronological timeline of all changes, grouped by date. Each entry shows which field changed, the old and new values, and the timestamp. This helps operators understand the evolution of a resource without needing to check external systems.

**Why this priority**: Drift tracking adds operational intelligence on top of the existing resource detail view. It requires the resource detail page and backend drift schema to exist first.

**Independent Test**: Navigate to a resource that has drift entries → "Drift History" button appears. Click → modal opens showing grouped changes. Resources without drift → no button shown.

**Acceptance Scenarios**:

1. **Given** a resource has recorded drift entries, **When** the operator views its detail page, **Then** a "Drift History" button is visible.
2. **Given** the operator clicks "Drift History", **When** the modal opens, **Then** changes are grouped by date with newest first.
3. **Given** a drift entry exists, **When** it is displayed, **Then** it shows the field name, old value, new value, timestamp, and source.
4. **Given** a resource has no drift entries, **When** the operator views its detail page, **Then** no "Drift History" button is shown.
5. **Given** the drift modal is open, **When** the operator clicks close or the backdrop, **Then** the modal closes and returns to the detail page.

---

### User Story 7 - Vendor Navigation Carousel & Vendor Page (Priority: P7)

An operator wants quick visual access to all vendors (providers) in the system. The landing page shows a vendor carousel strip below the heatmap and above the resource type carousels. Each vendor card displays the vendor name, total resource count, and number of resource types, colour-coded by vendor. Clicking a vendor card navigates to a dedicated vendor page that lists all resources for that vendor, grouped by normalised type in expandable table sections. Each table row shows resource name (linked to detail), state with colour indicator, region, category, and a graph icon to open the graph overlay.

**Why this priority**: Vendor navigation is an enhancement to the landing page experience. It requires the landing page and resource detail page to exist first.

**Independent Test**: Landing page shows vendor carousel with all vendors from seed data. Click a vendor → vendor page loads with resources grouped by type. Click resource name → navigates to detail. Click graph icon → graph overlay opens.

**Acceptance Scenarios**:

1. **Given** resources exist from multiple vendors, **When** the operator views the landing page, **Then** a vendor carousel appears showing one card per vendor, ordered by resource count descending.
2. **Given** a vendor card is displayed, **When** the operator views it, **Then** it shows the vendor name, resource count, type count, and is colour-coded by vendor.
3. **Given** the operator clicks a vendor card, **When** the vendor page loads, **Then** all resources for that vendor are displayed in table sections grouped by normalised type.
4. **Given** the operator is on a vendor page, **When** they view a resource table, **Then** each row shows name (linked), state (with colour dot), region, category, and a graph icon.
5. **Given** the operator clicks the graph icon on a vendor page row, **When** the graph overlay opens, **Then** it is centred on that resource.

---

### Edge Cases

- What happens when the backend is unreachable? The application displays a connection error banner with a retry option, not a blank page.
- What happens when a resource has no relationships? The graph view shows a single node with a message "No relationships found" rather than an empty canvas.
- What happens when the operator's browser window is narrow (mobile/tablet)? Carousels stack vertically, resource cards resize, and the graph view remains functional with touch gestures.
- What happens when the operator navigates to a resource that has been deleted? A "Resource not found" message is shown with a link back to the landing page.
- What happens when the backend returns an error during pagination? The existing results remain visible and an inline error message offers to retry loading the next page.
- What happens when there are hundreds of nodes in the graph? The graph caps visible nodes at a configurable limit and shows a "showing N of M" indicator, allowing the operator to expand further on demand.
- What happens when a resource has no drift entries? The "Drift History" button is hidden entirely rather than showing an empty modal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST display a landing page with horizontal, scrollable carousels grouped by normalised resource type.
- **FR-002**: Each resource card MUST show the resource name, vendor/provider badge, current state indicator, and key property summary.
- **FR-003**: The application MUST provide a provider drill-down view listing all resources for a selected vendor in a table with filtering by category, state, region, and normalised type. Each row MUST include a graph icon column that opens the graph overlay for that resource.
- **FR-004**: The provider view MUST support cursor-based pagination matching the backend API pattern.
- **FR-005**: The application MUST provide an interactive graph visualization as a full-screen overlay/modal, accessible via a graph icon in the resource table and a "View Graph" button on the resource detail page.
- **FR-006**: The graph view MUST support adjustable traversal depth, pan, zoom, click-to-inspect nodes, and lazy expansion of peripheral nodes.
- **FR-007**: Relationship edges in the graph MUST be colour-coded by type (DEPENDS_ON, HOSTED_ON, MEMBER_OF, CONTAINS, CONNECTED_TO, ATTACHED_TO, MANAGES, etc.).
- **FR-007a**: Graph nodes MUST use distinct shapes per normalised_type (e.g. ellipse for virtual_machine, hexagon for hypervisor, barrel for datastore, diamond for virtual_switch) and display two-line labels showing the resource name and normalised type.
- **FR-007b**: Graph layout MUST dynamically scale spacing (repulsion, edge length) based on the number of nodes to prevent overlap.
- **FR-007c**: Graph controls MUST include a node type legend showing the shape-to-type mapping.
- **FR-008**: The landing page MUST display a "Resources Discovered" summary strip above the carousels showing total resource count, resources added in the last 24 hours, counts by type with category-coloured cells, counts by provider with horizontal bar charts, and state distribution with coloured indicators.
- **FR-008a**: The application MUST provide a dedicated Analytics page with full-size heatmaps for category counts, state distribution, and activity recency.
- **FR-009**: The application MUST use a dark theme throughout with a modern, clean aesthetic.
- **FR-010**: The application MUST authenticate users via the backend login endpoint and store the session token securely.
- **FR-011**: The application MUST redirect unauthenticated users to the login screen and handle token expiry gracefully.
- **FR-012**: The application MUST detect first-time setup state from the backend and present a setup flow for initial administrator creation.
- **FR-013**: The application MUST display meaningful error states (connection errors, empty results, not found) rather than blank screens.
- **FR-014**: The application MUST be responsive, adapting layout for desktop, tablet, and large monitor screen sizes.
- **FR-015**: The resource detail view MUST show all resource properties, metadata, first_seen/last_seen timestamps, a relationships table with friendly resource names (not UUIDs), and a link to the graph view.
- **FR-015a**: The relationships table MUST resolve related resource UIDs to human-readable names via parallel batch API calls, displaying the name as a hyperlink to the related resource's detail page.
- **FR-016**: The application MUST provide a collapsible left sidebar navigation with icon and label for each section: Home (landing page), Providers (with sub-items per vendor), and Analytics. The sidebar collapses to icon-only mode to maximise content area.
- **FR-017**: The application MUST display a vendor navigation carousel on the landing page between the heatmap and type carousels, showing one card per vendor with name, resource count, type count, and vendor-specific colour.
- **FR-018**: The application MUST provide a dedicated vendor page (accessible via vendor carousel) that lists all resources for a vendor grouped by normalised type in table sections, with columns for name (linked to detail), state (coloured indicator), region, category, and graph icon.
- **FR-019**: The application MUST support drift tracking by showing a "Drift History" button on resource detail pages where drift entries exist, opening a modal displaying chronological changes grouped by date with field name, old/new values, timestamp, and source.
- **FR-020**: The application MUST support multi-vendor environments including VMware, AWS, Azure, and OpenShift with vendor-specific colours throughout (VMware=blue, AWS=amber, Azure=cyan, OpenShift=red).

### Key Entities

- **Resource**: An infrastructure asset identified by uid, with a name, vendor, vendor_id, vendor_type, normalised_type, category, region, state, and raw properties. Displayed in carousels, lists, detail views, and graph nodes.
- **Relationship**: A directed connection between two resources with a type label (e.g. DEPENDS_ON, HOSTED_ON), confidence score, and optional metadata. Displayed as graph edges.
- **Provider/Vendor**: A grouping of resources by their source platform (VMware, AWS, Azure, OpenShift). Used for navigation, vendor carousel, and vendor drill-down page.
- **Normalised Type**: A vendor-agnostic classification of resources (virtual_machine, hypervisor, datastore, cluster, virtual_switch, port_group, datacenter, management_plane, resource_pool, subnet, load_balancer, security_group, object_store, managed_database, kubernetes_cluster, kubernetes_node, namespace, deployment, statefulset, ingress, service, persistent_volume, route, virtual_network, network_gateway). Used to organise carousels on the landing page and table sections on vendor pages.
- **DriftEntry**: A record of a single field change on a resource, including resource_uid, field name, old_value, new_value, changed_at timestamp, and source. Stored in the backend and displayed in the drift modal.
- **Session**: The authenticated user's bearer token, expiry time, and username. Managed client-side for API authorisation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can identify all resources of a given type within 5 seconds of landing page load by scanning the relevant carousel.
- **SC-002**: Operators can navigate from the landing page to a filtered provider view in under 3 clicks.
- **SC-003**: The graph visualization for a resource with up to 50 connected nodes renders and becomes interactive within 2 seconds.
- **SC-004**: 90% of operators can find the dependency chain for a given resource on their first attempt without instructions.
- **SC-005**: The landing page loads and displays all carousels within 3 seconds on a standard broadband connection.
- **SC-006**: Heatmaps accurately reflect the current state of the inventory and update on each page load.
- **SC-007**: The application is fully usable on screens from 1280px to 3840px wide without horizontal scrolling or layout breakage.
- **SC-008**: Authentication flow (login to landing page) completes in under 5 seconds.
- **SC-009**: Operators can view the complete drift history of a resource within 2 clicks from the resource detail page.
- **SC-010**: Operators can navigate from the landing page to a vendor-specific resource list in 1 click via the vendor carousel.

## Assumptions

- The existing InventoryView backend API at `/api/v1/` is the sole data source. No direct database access is needed.
- The backend API contract (endpoints, request/response shapes) is stable and will not change during frontend development.
- The application will be deployed as a static web application served separately from the backend, communicating via HTTP.
- Standard web browser capabilities (modern Chrome, Firefox, Safari, Edge) are sufficient; no desktop application wrapper is needed.
- The initial release targets desktop browsers; mobile optimization is a future enhancement (responsive layout is included but not a primary target).
- The dark theme is the only theme for the initial release; a light theme toggle is not in scope.
- Resource counts per environment are expected to be in the low thousands (not millions); extreme scale optimization is not required for the initial release.
- The backend supports a `resource_drift` table and drift API endpoints (`GET /resources/{uid}/drift`, `GET /resources/{uid}/drift/exists`, `POST /resources/{uid}/drift`).
- Multi-vendor seed data (VMware, AWS, Azure, OpenShift) is available via the seed script for development and testing.

## Out of Scope

- Light theme or theme switching.
- Real-time push updates (WebSocket/SSE) — the dashboard refreshes on page load or manual refresh.
- Credential management UI (viewing, creating, or editing stored credentials).
- User management (creating additional users, role-based access beyond single admin).
- Collector configuration or triggering scans from the frontend.
- Export/reporting features (CSV, PDF).
- Mobile-first design (responsive is included but mobile is not a primary target).
