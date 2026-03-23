# Feature Specification: UI Usage Analytics & Audit Tracking

**Feature Branch**: `007-ui-usage-audit`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "I want an administration area in the left-hand navigation with a sub-menu item called Usage. The Usage page should show UI component usage analytics - tracking what features and pages users are interacting with most. This is not about resource-level analytics but about UI component usage: are people using drift detection, are people viewing the graph visualizations, are people looking at asset linkages, are people uploading automation metrics, are people using playlists, etc. I want to be able to see which UI features get the most engagement so I can understand user behavior patterns. The tracking should capture page views and feature interactions. The usage page should show aggregate statistics with time-based filtering and breakdowns by feature area. This should also audit login activity."

## User Scenarios & Testing

### User Story 1 - View UI Feature Usage Dashboard (Priority: P1)

As an administrator, I want to see a dashboard showing which UI features and pages are being used most so that I can understand user behaviour patterns and prioritise development efforts.

The Usage page is accessible from a new "Administration" section in the left-hand sidebar navigation, with "Usage" as a sub-menu item. The page displays aggregate statistics broken down by feature area (e.g. Drift Detection, Graph Visualisation, Asset Linkages, Automation Upload, Playlists, Resource Browsing). Each feature area shows total interactions, unique users, and trend direction. A time-range filter allows narrowing the view to the last 24 hours, 7 days, 30 days, or a custom date range.

**Why this priority**: This is the core value of the feature — without the dashboard, no usage data is actionable.

**Independent Test**: Can be tested by navigating to the Administration > Usage page and verifying that aggregate usage statistics are displayed with working time-range filters, even with minimal or zero tracked data.

**Acceptance Scenarios**:

1. **Given** I am a logged-in administrator, **When** I click "Administration" in the sidebar and then "Usage", **Then** I see the Usage dashboard with feature area breakdowns and aggregate counts.
2. **Given** the Usage dashboard is displayed, **When** I select "Last 7 days" from the time-range filter, **Then** all statistics update to reflect only activity within that period.
3. **Given** the Usage dashboard is displayed, **When** no usage data exists for the selected period, **Then** the dashboard displays zero counts with an informational message rather than an error.
4. **Given** the Usage dashboard is displayed, **When** I view feature area breakdowns, **Then** I see interaction counts for each tracked feature: Drift Detection, Graph Visualisation, Asset Linkages, Automation Metrics, Playlists, Resource Browsing, and Login Activity.

---

### User Story 2 - Track UI Feature Interactions (Priority: P1)

As a system, I must silently record user interactions with UI features so that the Usage dashboard has data to display. Tracking must be non-intrusive — it must not degrade the user experience or add noticeable latency to any interaction.

Tracked interactions include:
- **Page views**: Landing page, Resource Detail, Provider pages, Automation Dashboard, Automation Upload, Automation Review, Playlist pages
- **Feature interactions**: Opening the graph overlay, expanding drift timelines, clicking asset chain links, uploading automation metrics files, running correlations, creating/editing playlists, viewing resource relationships
- **Navigation patterns**: Which sidebar sections users expand and visit

Each tracked event records the feature area, the specific action name, a timestamp, and which user performed it.

**Why this priority**: Without tracking, the dashboard has no data. This is a foundational prerequisite.

**Independent Test**: Can be tested by performing various UI actions and verifying that corresponding usage events are persisted and retrievable.

**Acceptance Scenarios**:

1. **Given** I am a logged-in user, **When** I navigate to the Resource Detail page, **Then** a page view event is recorded with the feature area "Resource Browsing" and a timestamp.
2. **Given** I am viewing a resource, **When** I open the graph overlay, **Then** an interaction event is recorded for "Graph Visualisation".
3. **Given** I am viewing a resource, **When** I click on an asset chain link, **Then** an interaction event is recorded for "Asset Linkages".
4. **Given** tracking is active, **When** any page loads or feature interaction occurs, **Then** the page renders with no perceptible additional delay (tracking happens asynchronously).
5. **Given** the user's session has expired or they are unauthenticated, **When** they browse the login page, **Then** no usage events are recorded (only authenticated sessions are tracked).

---

### User Story 3 - Audit Login Activity (Priority: P2)

As an administrator, I want to see a log of login activity — both successful and failed attempts — so that I can monitor access patterns and detect potential security issues.

The login audit section appears on the Usage dashboard as a dedicated "Login Activity" area. It shows recent login attempts in reverse chronological order, including: timestamp, username, client IP address, outcome (success/failure), and the reason for failure if applicable (e.g. invalid credentials, account not found). A summary shows total successful logins, total failed attempts, and unique users for the selected time period.

**Why this priority**: Login auditing is a security best-practice and provides immediate value, but is secondary to the broader usage analytics.

**Independent Test**: Can be tested by performing successful and failed login attempts, then verifying they appear in the Login Activity section of the Usage dashboard.

**Acceptance Scenarios**:

1. **Given** a user successfully logs in, **When** an administrator views the Usage dashboard Login Activity section, **Then** the successful login is listed with timestamp, username, client IP address, and "Success" outcome.
2. **Given** someone attempts to log in with invalid credentials, **When** an administrator views Login Activity, **Then** the failed attempt is listed with timestamp, attempted username, and "Failed - Invalid credentials" outcome.
3. **Given** multiple login events have occurred, **When** the time-range filter is changed, **Then** the Login Activity list filters to show only events within the selected period.
4. **Given** the Login Activity section is displayed, **When** there are more than 50 entries, **Then** the list is paginated to avoid overwhelming the display.

---

### User Story 4 - Feature Usage Detail Drill-Down (Priority: P3)

As an administrator, I want to click on a feature area in the Usage dashboard to see detailed breakdowns of specific actions within that feature, so that I can understand exactly how a feature is being used.

For example, clicking on "Drift Detection" would show a breakdown of: how many drift timeline expansions, how many drift comparison views, how many drift snapshots viewed. Clicking "Automation Metrics" would show: uploads attempted, correlations run, review actions taken.

**Why this priority**: This adds depth to the analytics but is not required for the initial value of seeing top-level usage patterns.

**Independent Test**: Can be tested by clicking on a feature area card and verifying that a detailed breakdown of actions within that feature is displayed.

**Acceptance Scenarios**:

1. **Given** the Usage dashboard is displayed, **When** I click on the "Graph Visualisation" feature area, **Then** I see a detailed breakdown showing counts for: graph overlay opened, node expanded, depth changed.
2. **Given** I am viewing a feature detail breakdown, **When** I want to return to the overview, **Then** I can navigate back to the full dashboard without losing my time-range selection.

---

### Edge Cases

- What happens when the usage tracking storage becomes very large over time? Usage data older than 90 days is automatically purged to prevent unbounded growth.
- What happens if a user performs rapid repeated actions (e.g. clicking graph overlay open/close quickly)? Events are debounced on the client side — repeated identical actions within 2 seconds are counted as a single event.
- What happens if the tracking service is temporarily unavailable? Tracking failures are silently ignored and do not affect the user's workflow. Events are fire-and-forget.
- What happens when there are no administrators other than the current user? The Usage page still functions and shows all tracked data including the current user's own activity.
- What happens if a user clears their browser or uses multiple tabs? Each tab independently tracks events. Server-side deduplication is not required — the goal is measuring engagement volume, not unique interaction counting.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide an "Administration" section in the left-hand sidebar navigation, containing a "Usage" sub-menu item.
- **FR-002**: System MUST display a Usage dashboard page showing aggregate UI feature usage statistics.
- **FR-003**: System MUST track page view events when authenticated users navigate to any application page.
- **FR-004**: System MUST track feature interaction events when authenticated users perform key actions (opening graph overlay, expanding drift timeline, clicking asset chain links, uploading automation files, running correlations, managing playlists).
- **FR-005**: System MUST provide time-range filtering on the Usage dashboard with preset options (24 hours, 7 days, 30 days) and custom date range selection.
- **FR-006**: System MUST display usage breakdowns grouped by feature area. Feature areas are discovered dynamically from recorded events (initial areas include Drift Detection, Graph Visualisation, Asset Linkages, Automation Metrics, Playlists, Resource Browsing, and Login Activity, but new areas appear automatically when new event types are tracked).
- **FR-007**: System MUST record all login attempts (both successful and failed) with timestamp, username, client IP address, and outcome.
- **FR-008**: System MUST display login audit history in the Usage dashboard with pagination for large result sets.
- **FR-009**: System MUST perform tracking asynchronously so that it does not add perceptible latency to user interactions.
- **FR-010**: System MUST debounce rapid repeated identical events on the client side, collapsing events within a 2-second window into a single tracked event.
- **FR-011**: System MUST automatically purge usage tracking data older than 90 days.
- **FR-012**: System MUST silently handle tracking failures without impacting the user experience.
- **FR-013**: System MUST restrict access to the Usage dashboard to authenticated administrators only.
- **FR-014**: System MUST support drill-down from a feature area summary to a detailed action-level breakdown.
- **FR-015**: System MUST show for each feature area: total interactions, unique user count, and trend direction compared to the previous equivalent period.

### Key Entities

- **Usage Event**: Represents a single tracked user interaction. Attributes: feature area, specific action name, user identifier, timestamp.
- **Login Audit Entry**: Represents a login attempt. Attributes: timestamp, username attempted, client IP address, outcome (success/failure), failure reason (if applicable).
- **Feature Area**: A logical grouping of related UI actions (e.g. "Drift Detection", "Graph Visualisation"). Discovered dynamically from recorded usage events rather than maintained as a fixed list. Used to aggregate and display usage statistics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Administrators can view the Usage dashboard and identify the top 3 most-used feature areas within 10 seconds of page load.
- **SC-002**: All tracked UI interactions appear in the Usage dashboard within 30 seconds of occurring.
- **SC-003**: Login audit entries capture 100% of login attempts (both successful and failed) with no gaps.
- **SC-004**: Usage tracking adds no more than 50 milliseconds of perceived delay to any user interaction.
- **SC-005**: Time-range filtering updates the dashboard display within 2 seconds.
- **SC-006**: The system handles at least 10,000 tracked events per day without performance degradation on the Usage dashboard.
- **SC-007**: Usage data older than 90 days is automatically removed, keeping storage bounded.

## Clarifications

### Session 2026-03-22

- Q: Should login audit entries capture client IP address? → A: Yes, capture IP address on login attempts.
- Q: Should usage events include target context (e.g. which resource UID was viewed)? → A: No — track only feature area and action name, not specific entities.
- Q: Should the feature area list be fixed or dynamic? → A: Dynamic — dashboard discovers feature areas from recorded events automatically.

## Assumptions

- Only authenticated users' actions are tracked; unauthenticated page visits (e.g. the login page itself) are not recorded as usage events.
- The "Administration" navigation section is new and will initially contain only the "Usage" item, but is designed to accommodate future admin features.
- Login audit data follows the same 90-day retention policy as usage events.
- All existing users are considered administrators for the purpose of accessing the Usage dashboard (the application currently has a single admin role).
- Trend direction is calculated by comparing the selected time period against the immediately preceding period of equal length (e.g. "Last 7 days" compares against the 7 days before that).
