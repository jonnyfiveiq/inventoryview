# Research: UI Usage Analytics & Audit Tracking

## Decision 1: Storage Strategy for Usage Events

**Decision**: Use standard PostgreSQL relational tables (not the graph).

**Rationale**: Usage events and login audit entries are administrative metadata, not resource or relationship data. The Constitution (Principle I) explicitly permits standard PostgreSQL tables for metadata. Relational tables with time-based indexing are ideal for time-series aggregation queries (GROUP BY feature_area, date ranges, COUNT DISTINCT user_id). The graph database offers no advantage for this workload.

**Alternatives considered**:
- Graph nodes/edges: Rejected — violates the spirit of graph-first (these aren't resources or relationships), adds unnecessary complexity to Cypher queries for simple aggregation.
- External analytics service (e.g., Plausible, PostHog): Rejected — adds an external dependency violating Constitution Principle VIII (zero-friction deployment).
- Client-side only (localStorage): Rejected — data doesn't survive browser clears, can't aggregate across users, no login audit capability.

## Decision 2: Event Ingestion Pattern

**Decision**: Individual event POST with client-side debounce (2-second window for identical events). Fire-and-forget from the client — no retry on failure.

**Rationale**: The application is single-tenant with low concurrent user counts. Batching adds complexity (flush timers, page-unload handling via sendBeacon) with minimal benefit at this scale. Individual POSTs are simpler to implement and debug. The 2-second client-side debounce prevents noise from rapid repeated actions.

**Alternatives considered**:
- Batch events client-side and POST periodically: Rejected — adds complexity (batch buffer, flush timer, sendBeacon for page unload) with little benefit at expected scale.
- WebSocket streaming: Rejected — overkill for low-frequency events, adds connection management complexity.

## Decision 3: Dashboard Aggregation Strategy

**Decision**: Server-side aggregation via SQL queries with time-range parameters. No pre-computed materialized views.

**Rationale**: At 10,000 events/day with 90-day retention (~900K rows max), PostgreSQL can handle aggregate queries (COUNT, COUNT DISTINCT, GROUP BY) efficiently with proper indexing. Pre-computed views add write-time overhead and staleness concerns.

**Alternatives considered**:
- Materialized views refreshed on schedule: Rejected — adds operational complexity, staleness window, and is unnecessary at this data volume.
- Pre-aggregated daily rollup tables: Rejected — same reasons; premature optimization.

## Decision 4: Login Audit Integration

**Decision**: Record login audit entries directly in the auth endpoint handler (synchronous within the request). Separate table from usage events.

**Rationale**: Login audit must capture 100% of attempts (SC-003). Unlike usage tracking which is fire-and-forget, login audit is a security requirement and must not be lossy. Recording synchronously in the auth handler guarantees capture. A separate table keeps the schema clean — login entries have different attributes (IP address, outcome, failure reason) than usage events (feature area, action).

**Alternatives considered**:
- Same table as usage events with a special feature_area: Rejected — different attributes (IP, outcome) would require nullable columns or JSON blobs.
- Async/background recording: Rejected — risks losing audit entries if the background task fails.

## Decision 5: Data Retention / Purge Mechanism

**Decision**: Scheduled DELETE query removing rows older than 90 days, triggered on each dashboard page load (lazy purge) with a daily guard to avoid running multiple times.

**Rationale**: At ~900K max rows, a DELETE with a timestamp filter is fast. A lazy approach (triggered when someone actually views the dashboard) avoids needing an external scheduler or cron job. A simple "last purge" timestamp in the application prevents redundant runs within the same day.

**Alternatives considered**:
- PostgreSQL partitioning by month with partition drop: Rejected — overkill for <1M rows, adds migration complexity.
- External cron job: Rejected — violates zero-friction deployment principle.
- pg_cron extension: Rejected — not available in all PostgreSQL deployments, adds dependency.

## Decision 6: Tracking Hook Architecture

**Decision**: A single `useTracking()` React hook that exposes a `track(featureArea, action)` function. Instrumented at the component level where interactions occur. Uses a Zustand store internally for debounce state.

**Rationale**: A hook-based approach is idiomatic React and follows the existing pattern (useAuth, useGraph, usePlaylists). Component-level instrumentation is explicit and easy to audit — you can grep for `track(` to see every instrumented interaction. Zustand for debounce state avoids prop-drilling and is already a project dependency.

**Alternatives considered**:
- Global event listener (click/navigation interception): Rejected — fragile, hard to map DOM events to meaningful feature areas.
- Higher-order component wrapper: Rejected — less ergonomic than hooks in a function-component codebase.
- Analytics middleware in the router: Rejected — only captures page views, not feature interactions.
