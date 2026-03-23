# Feature Specification: Drift Calendar Heatmap

**Feature Branch**: `004-drift-calendar-heatmap`
**Created**: 2026-03-22
**Status**: Clarified
**Input**: User description: "Add a GitHub-style calendar heatmap for infrastructure drift. Each resource gets a year-long calendar grid where each day cell is coloured based on drift activity. Initial discovery appears as a cool colour. Subsequent metadata changes (drifts) shift the cell colour toward red. The intensity is relative — resources with more drift events compared to the fleet average appear hotter."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Resource Drift Calendar (Priority: P1)

A user navigates to a resource's detail page and sees a GitHub-style calendar heatmap showing the resource's change history over time. Each day cell in the calendar grid is coloured to reflect drift activity on that day. The day the resource was first discovered appears in a cool colour (green/blue). Days with metadata changes appear in progressively warmer colours (yellow → orange → red), with the intensity determined by how many drift events occurred on that day relative to the fleet-wide daily average. Days with no activity are left neutral/empty. The user can glance at the calendar and immediately identify periods of high change activity for that specific resource.

**Why this priority**: This is the core value — giving users an instant, visual timeline of how volatile a resource has been. Without this, the remaining stories have no foundation.

**Independent Test**: Navigate to a resource detail page for a resource with known drift history. Verify the calendar grid renders with colour-coded cells matching the drift event dates. Hover over a cell to see the date and event count.

**Acceptance Scenarios**:

1. **Given** a resource with drift history spanning multiple months, **When** the user views the resource detail page, **Then** a calendar heatmap is displayed showing coloured cells for days with drift events and neutral cells for quiet days
2. **Given** a resource that was first discovered 90 days ago, **When** the user views its calendar, **Then** the discovery day cell appears in a cool colour (green/blue) distinct from drift-change colours
3. **Given** a resource with a high total lifetime drift count (above fleet average) and 10 drift events on a single day, **When** the user views the calendar, **Then** that day's cell appears in a hot colour (deep red) reflecting both the resource's overall noisiness and the daily spike
4. **Given** a resource with a low total lifetime drift count (below fleet average) and 1 drift event on a day, **When** the user views the calendar, **Then** that day's cell appears in a mild warm colour (light yellow/green) reflecting the resource's overall quietness despite the single event
5. **Given** a day cell in the calendar, **When** the user hovers over it, **Then** a tooltip displays the date, the number of drift events, and the fields that changed

---

### User Story 2 — Fleet-Wide Drift Overview (Priority: P2)

A user views a fleet-level calendar heatmap on both the landing page and the analytics page that aggregates drift activity across all resources. Each day cell shows the total drift event count for the entire fleet that day, coloured by intensity. This gives operators a macro view of when infrastructure was most turbulent — useful for correlating change storms with incidents or maintenance windows. The calendar appears on both pages to provide maximum visibility regardless of the user's navigation path.

**Why this priority**: The fleet overview extends the per-resource calendar to an operational intelligence tool. It depends on the same calendar component from US1 but adds aggregation.

**Independent Test**: Navigate to both the landing page and analytics page. Verify a fleet-wide calendar heatmap renders on each, showing aggregate drift counts per day across all resources. Hover to see totals.

**Acceptance Scenarios**:

1. **Given** drift events exist across multiple resources on the same day, **When** the user views the fleet calendar on either the landing page or analytics page, **Then** the day cell colour reflects the total event count for that day
2. **Given** a day with no drift events across the entire fleet, **When** the user views the fleet calendar, **Then** that day's cell is neutral/empty
3. **Given** a day with significantly more total drift events than the yearly average, **When** the user views the fleet calendar, **Then** that cell appears in a hot colour indicating a change storm

---

### User Story 3 — Click-Through from Calendar to Drift Detail (Priority: P3)

A user clicks on a coloured day cell in a resource's drift calendar and the existing drift modal opens, filtered to show only the changes that occurred on that specific day. This connects the visual overview to the detailed change log without requiring the user to scroll through the full history.

**Why this priority**: This is a quality-of-life enhancement connecting the heatmap to the existing drift modal. It builds on US1 and the existing drift detail functionality.

**Independent Test**: Click a coloured day cell on a resource's drift calendar. Verify the drift modal opens showing only the changes for that specific day.

**Acceptance Scenarios**:

1. **Given** a resource calendar showing a coloured cell for a specific day, **When** the user clicks that cell, **Then** the drift modal opens filtered to entries from that day only
2. **Given** a neutral/empty day cell, **When** the user clicks it, **Then** nothing happens (no modal opens)

---

### Edge Cases

- What happens when a resource has no drift history at all? The calendar renders with only the discovery-day cell coloured (cool colour) and all other days neutral
- What happens when a resource was discovered today? The calendar shows a single coloured cell for today
- What happens when drift data spans more than one year? The calendar displays the most recent 365 days with the ability to navigate to earlier periods
- How are days handled where both discovery and drift events occur? Discovery colour takes precedence for the first appearance; if drift also happens on discovery day, the cell uses a blended or split indicator
- What happens when there are zero resources with drift (new/empty system)? The fleet calendar shows all neutral cells with a message indicating no drift activity has been recorded yet
- How does the relative colouring work when only one resource has any drift? That resource's cells are coloured based on absolute thresholds as a fallback when fleet statistics are insufficient for meaningful comparison

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a calendar heatmap grid on each resource's detail page showing the most recent 365 days of activity
- **FR-002**: Each day cell in the calendar MUST be coloured based on the number of drift events recorded for that resource on that day
- **FR-003**: The colour scale MUST progress from cool (green/blue) for low activity through warm (yellow/orange) to hot (red) for high activity
- **FR-004**: The day a resource was first discovered MUST be visually distinguished from drift-change days using a distinct cool colour
- **FR-005**: Colour intensity MUST use a two-layer calculation: (1) a resource's total lifetime drift count compared to the fleet average sets the base intensity, so persistently noisy resources appear hotter overall; (2) per-day event spikes overlay on top, so days with unusually high activity for that resource stand out even further
- **FR-006**: When fleet statistics are insufficient (fewer than 5 resources with drift), the system MUST fall back to absolute thresholds for colouring (e.g., 1 event = light, 3 = medium, 5+ = hot)
- **FR-007**: Each day cell MUST show a tooltip on hover containing: the date, the number of drift events, and a summary of which fields changed
- **FR-008**: The calendar MUST render with weeks as columns and days of the week as rows, matching the GitHub contribution graph layout
- **FR-009**: Month labels MUST appear along the top of the calendar for orientation
- **FR-010**: The fleet-wide calendar heatmap MUST aggregate drift events across all resources per day and display on both the landing page and the analytics page
- **FR-011**: Clicking a coloured day cell on a resource's calendar MUST open the existing drift detail modal filtered to that specific day
- **FR-012**: Clicking a neutral/empty day cell MUST have no effect
- **FR-013**: The calendar MUST support navigating to earlier 365-day periods when drift history exceeds one year
- **FR-014**: The calendar MUST render within the existing page layout without requiring horizontal scrolling on screens 1024px and wider
- **FR-015**: The calendar MUST be accessible on screens as narrow as 375px, using horizontal scrolling within the calendar container if needed

### Key Entities

- **Drift Event**: A recorded change to a resource's metadata on a specific date. Key attributes: resource identifier, date of change, field that changed, previous value, new value, source of change
- **Discovery Event**: The first recorded appearance of a resource in the system. Key attributes: resource identifier, discovery date
- **Fleet Statistics**: Aggregated drift metrics across all resources used to calculate relative intensity. Key attributes: average daily drift count per resource, total daily drift count across fleet
- **Calendar Cell**: A single day in the calendar grid. Key attributes: date, event count, colour intensity, event type (discovery, drift, or empty)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the most-changed resources in their fleet within 5 seconds of viewing a resource's detail page
- **SC-002**: The calendar heatmap renders completely within 2 seconds for resources with up to 1,000 drift events
- **SC-003**: Users can distinguish between discovery events and drift events by colour alone without reading labels
- **SC-004**: The fleet-wide calendar accurately reflects total drift activity, enabling users to identify change-storm days within 10 seconds
- **SC-005**: 100% of coloured day cells show accurate tooltips with date, event count, and changed fields on hover
- **SC-006**: The calendar displays correctly on screens from 375px to 2560px wide

## Clarifications

### Session 2026-03-22

- Q: Where should the fleet-wide drift calendar heatmap be placed? → A: Both the landing page and the analytics page
- Q: How should relative colour intensity be calculated? → A: Two-layer approach — lifetime total drift count vs fleet average sets the base intensity; per-day event spikes overlay on top for additional contrast

## Assumptions

- The existing drift tracking system (resource_drift table and drift API endpoints) provides sufficient data for the calendar — no new data collection is needed
- Resource discovery date can be derived from the resource's `created_at` or `first_seen` timestamp already stored in the system
- The existing colour conventions in the application (dark theme with surface/border tokens) will be extended with a new heatmap colour scale
- The fleet average calculation uses a simple mean for both layers: lifetime average = total drift events across fleet / number of resources with drift; daily average = total events on that day / resources active on that day
- Calendar navigation (viewing earlier periods) is a simple previous/next control, not a date picker
