# Quickstart: UI Usage Analytics & Audit Tracking

## Scenario 1: Track a UI interaction

1. User logs in and navigates to a resource detail page.
2. Frontend `useTracking()` hook fires `track("Resource Browsing", "page_view")`.
3. Hook checks debounce — if the same (feature_area, action) was sent within 2 seconds, skip.
4. Hook sends `POST /api/v1/usage/events` with `{"feature_area": "Resource Browsing", "action": "page_view"}`.
5. Backend extracts user_id from token, inserts row into `usage_event` table.
6. Returns `201 Created`. Frontend ignores failures silently.

## Scenario 2: View the Usage dashboard

1. Admin navigates to Administration > Usage in the sidebar.
2. Frontend loads `GET /api/v1/usage/summary?start_date=2026-03-15&end_date=2026-03-22`.
3. Dashboard renders feature area cards showing: total events, unique users, trend arrow (up/down/flat).
4. Admin clicks "Last 30 days" — frontend re-fetches with updated date range.
5. All cards update to reflect the new period.

## Scenario 3: Drill down into a feature area

1. Admin clicks the "Graph Visualisation" card on the Usage dashboard.
2. Frontend loads `GET /api/v1/usage/feature/Graph%20Visualisation?start_date=...&end_date=...`.
3. Detail view shows action breakdown: "graph_overlay_opened: 85", "node_expanded: 33", "depth_changed: 10".
4. Admin clicks back — returns to overview with time-range preserved.

## Scenario 4: Review login activity

1. Admin scrolls to the "Login Activity" section on the Usage dashboard.
2. Frontend loads `GET /api/v1/usage/logins?start_date=...&end_date=...&page=1&page_size=50`.
3. Table shows recent login attempts: timestamp, username, IP, outcome.
4. Summary bar above shows: "42 successful, 5 failed, 3 unique users".
5. Admin pages through older entries using pagination controls.

## Scenario 5: Failed login is audited

1. Someone enters wrong credentials on the login page.
2. Backend auth handler records a `login_audit` entry: username="attacker", outcome="failure", failure_reason="Invalid credentials", ip_address="192.168.1.50".
3. Backend returns 401 as normal — the audit recording is transparent.
4. Later, admin sees this failed attempt in the Login Activity table.

## Scenario 6: Data retention purge

1. Admin opens the Usage dashboard (or 24 hours have passed since last purge).
2. Backend summary endpoint triggers lazy purge check.
3. If last purge was >24 hours ago: `DELETE FROM usage_event WHERE created_at < now() - interval '90 days'` and same for `login_audit`.
4. Dashboard loads normally with only the retained data.
