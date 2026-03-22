# Feature Specification: Spotlight-Style Universal Search

**Feature Branch**: `003-spotlight-search`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Add a Spotlight-style universal search to the main landing page that filters results in real-time grouped by normalised taxonomy across all providers."

## Clarifications

### Session 2026-03-22

- Q: Should search match only resource names, or also other visible fields (vendor_id, state, provider, normalised_type)? → A: All visible fields (name, vendor_id, state, provider, normalised_type).
- Q: When a taxonomy group has more than 5 results, what should "Show all" do? → A: Show up to 10 inline, then link to provider page for the full list.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Search with Taxonomy Grouping (Priority: P1)

An authenticated user on the landing page wants to quickly find resources across their entire infrastructure. They activate the search overlay (via a search icon in the header or the keyboard shortcut Cmd+K / Ctrl+K). A centered overlay appears with a dimmed/blurred background and a prominent search input field. As they type (e.g., "John"), results appear instantly below the input, grouped by normalised taxonomy. For example, if there are hypervisors named "John-hypervisor" and virtual machines named "John-VMs" across VMware, AWS, and Azure, two groups are displayed: one headed "Virtual Machine (3)" and one headed "Hypervisor (1)". Each result row shows the resource name, provider badge, and current state. The user can continue typing to narrow results further.

**Why this priority**: This is the core value of the feature — instant, cross-provider search with grouped results is the primary user need.

**Independent Test**: Can be tested by opening the search overlay, typing a query, and verifying grouped results appear matching resources across all providers.

**Acceptance Scenarios**:

1. **Given** the user is on any authenticated page, **When** they press Cmd+K (Mac) or Ctrl+K (Windows/Linux), **Then** a centered search overlay appears with a focused text input and a dimmed/blurred background.
2. **Given** the search overlay is open, **When** the user types "John", **Then** results appear grouped by normalised taxonomy (e.g., "Virtual Machine", "Hypervisor") with each group showing a count of matching resources.
3. **Given** the search overlay is showing results, **When** results span multiple providers, **Then** each result row displays the resource name, provider name, and current state.
4. **Given** the search overlay is open with results, **When** the user clears the search field, **Then** all results are cleared and the overlay shows an empty state prompt (e.g., "Start typing to search...").
5. **Given** the search overlay is open, **When** the user types a query with no matches, **Then** a "No results found" message is displayed.

---

### User Story 2 - Keyboard Navigation and Selection (Priority: P2)

A power user wants to navigate search results entirely via keyboard. After typing a query, they use the arrow keys (Up/Down) to move through results across taxonomy groups. The currently highlighted result is visually distinct. Pressing Enter on a highlighted result navigates to that resource's detail page and closes the overlay. Pressing Escape at any time closes the overlay and returns focus to the previous page.

**Why this priority**: Keyboard navigation is essential for the Spotlight-like experience and power-user productivity, but the feature delivers value even without it (mouse clicks still work).

**Independent Test**: Can be tested by opening the overlay, typing a query, using arrow keys to navigate, pressing Enter, and verifying navigation to the correct resource detail page.

**Acceptance Scenarios**:

1. **Given** search results are displayed, **When** the user presses the Down arrow key, **Then** the first result is highlighted, and subsequent presses move highlight through results across groups.
2. **Given** a result is highlighted, **When** the user presses Enter, **Then** the application navigates to that resource's detail page and the overlay closes.
3. **Given** the search overlay is open, **When** the user presses Escape, **Then** the overlay closes and focus returns to the underlying page.
4. **Given** the highlight is on the last result, **When** the user presses Down arrow, **Then** the highlight wraps to the first result.

---

### User Story 3 - Search Activation via Header Icon (Priority: P3)

A user who prefers mouse interaction sees a search icon in the application header/toolbar. Clicking the icon opens the same search overlay as the keyboard shortcut. The icon includes a subtle hint showing the keyboard shortcut (e.g., "Cmd+K") so users can learn the shortcut over time.

**Why this priority**: Provides discoverability for the search feature for users who may not know the keyboard shortcut.

**Independent Test**: Can be tested by clicking the search icon in the header and verifying the overlay opens with the input focused.

**Acceptance Scenarios**:

1. **Given** the user is on any authenticated page, **When** they click the search icon in the header, **Then** the search overlay opens with the input field focused.
2. **Given** the search icon is visible, **When** the user hovers over it, **Then** a tooltip shows the keyboard shortcut (Cmd+K / Ctrl+K).

---

### Edge Cases

- What happens when the user types very quickly (rapid keystrokes)? Search debounces input to avoid excessive requests — results update after a brief pause in typing.
- What happens when the backend is slow or unavailable? A loading indicator appears while results are being fetched. If the backend is unreachable, a non-blocking error message appears in the overlay.
- What happens when a search query returns hundreds of results? Each taxonomy group initially shows 5 results with a "Show more" option to expand to 10 inline. Beyond 10, a "View all X on provider page" link navigates to the provider page with the search query pre-filled.
- What happens when the user opens search on a narrow/mobile screen? The overlay adapts responsively — full width on small screens, centered modal on larger screens.
- What happens when the user clicks outside the overlay? The overlay closes.
- What happens when the search field contains special characters? Special characters are treated as literal text and do not cause errors.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a search overlay that can be activated from any authenticated page via keyboard shortcut (Cmd+K on Mac, Ctrl+K on Windows/Linux).
- **FR-002**: System MUST provide a clickable search icon in the application header that opens the same search overlay.
- **FR-003**: The search overlay MUST appear as a centered modal with a dimmed/blurred background behind it.
- **FR-004**: The search input field MUST receive focus automatically when the overlay opens.
- **FR-005**: As the user types, the system MUST display matching results grouped by normalised taxonomy type (e.g., virtual_machine, hypervisor, datastore, subnet).
- **FR-006**: Search MUST match across all providers (VMware, AWS, Azure, OpenShift, and any future providers) simultaneously.
- **FR-007**: Search MUST perform case-insensitive substring matching against all visible resource fields: name, vendor_id, state, provider, and normalised_type.
- **FR-008**: Each taxonomy group header MUST display the human-readable taxonomy type name and the count of matching resources in that group.
- **FR-009**: Each result row within a group MUST display the resource name, provider name, and current state.
- **FR-010**: Clicking a result MUST navigate the user to that resource's detail page and close the overlay.
- **FR-011**: The search overlay MUST support keyboard navigation: Up/Down arrows to move between results, Enter to select, Escape to close.
- **FR-012**: The search overlay MUST close when the user presses Escape or clicks outside the overlay.
- **FR-013**: The system MUST debounce search input to avoid excessive requests while the user is actively typing.
- **FR-014**: Each taxonomy group MUST initially display up to 5 results. If more exist, a "Show more" action expands the group to show up to 10 results inline. If still more exist beyond 10, a "View all X on provider page" link MUST navigate to the provider page with the search query pre-filled as a filter.
- **FR-015**: The search overlay MUST display a loading indicator while results are being fetched.
- **FR-016**: The search overlay MUST display a "No results found" message when no resources match the query.
- **FR-017**: The search icon in the header MUST display a hint showing the keyboard shortcut.

### Key Entities

- **Search Query**: The text input from the user used to filter resources. Attributes: query string, timestamp.
- **Search Result**: A matching resource returned from the search. Attributes: resource name, resource UID, provider, normalised taxonomy type, current state.
- **Taxonomy Group**: A logical grouping of search results by normalised type. Attributes: taxonomy type name, result count, list of matching results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can find any resource by name, vendor_id, state, provider, or type in 3 keystrokes or fewer beyond the minimum needed to uniquely identify it (search results appear after the first keystroke pause).
- **SC-002**: Search results appear within 500 milliseconds of the user pausing typing, for inventories of up to 10,000 resources.
- **SC-003**: 100% of resources matching the search query are returned and correctly grouped by their normalised taxonomy type.
- **SC-004**: Users can navigate from search activation to viewing a resource's detail page in under 5 seconds using only the keyboard.
- **SC-005**: The search overlay is accessible and usable on screen widths from 375px (mobile) to 2560px (ultrawide).
- **SC-006**: Users discover the search feature within their first session, measured by the visibility of the header icon and keyboard shortcut hint.

## Assumptions

- The existing backend resource listing endpoint supports text-based filtering (query parameter) that can be used for search. If not, a dedicated search endpoint may need to be added.
- Search is performed against all visible resource fields: name, vendor_id, state, provider, and normalised_type.
- The normalised taxonomy types already defined in the system (virtual_machine, hypervisor, datastore, etc.) are the grouping categories.
- Authentication is already handled — the search feature is only available to authenticated users.
- The existing resource detail page already exists and can be navigated to via resource UID.
- Debounce interval of 250-300ms is a reasonable default for balancing responsiveness and request volume.
- Each taxonomy group shows up to 5 results by default, expandable to 10 inline, with a link to the provider page for larger result sets.

## Scope

### In Scope

- Search overlay UI (modal with blur background)
- Real-time search with debounced input
- Results grouped by normalised taxonomy type
- Cross-provider search (all vendors in one query)
- Keyboard shortcut activation (Cmd+K / Ctrl+K)
- Header search icon with shortcut hint
- Full keyboard navigation (arrows, Enter, Escape)
- Click-to-navigate to resource detail
- Loading and empty states
- Responsive design

### Out of Scope

- Search history or recent searches
- Saved/bookmarked searches
- Advanced search syntax (filters, boolean operators)
- Search across non-visible resource fields (e.g., tags, IP addresses, descriptions, internal metadata)
- Server-side search indexing or full-text search infrastructure
- Search analytics or tracking
- Voice search
