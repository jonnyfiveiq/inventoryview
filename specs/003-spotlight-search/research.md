# Research: Spotlight-Style Universal Search

**Feature**: 003-spotlight-search
**Date**: 2026-03-22

## Research Topics

### 1. Backend Search Capability

**Decision**: Add a `search` query parameter to the existing `GET /api/v1/resources` endpoint.

**Rationale**: The current endpoint supports only exact-match filters (vendor, category, region, state) with cursor-based pagination. There is no substring/text search capability. Adding a `search` parameter that performs case-insensitive ILIKE matching against name, vendor_id, state, vendor, and normalised_type is the simplest approach that meets FR-007. The Cypher query in `services/graph.py` (`query_resource_nodes`) needs to be extended with optional WHERE clauses for text matching.

**Alternatives considered**:
- Full-text search (PostgreSQL tsvector): Overkill for substring matching on short string fields. Would require schema migration and index creation.
- Dedicated search endpoint: Unnecessary complexity — the existing endpoint already handles filtering and pagination. Adding one more parameter is cleaner.
- Client-side filtering only: Would require fetching all resources (could be 10,000+), defeating the purpose of cursor-based pagination.

### 2. Frontend Search Pattern

**Decision**: Use a global keyboard listener + React portal overlay component with TanStack Query for debounced search requests.

**Rationale**: The existing frontend uses TanStack Query for all data fetching (useResources, useGraph hooks). A new `useSearch` hook following the same pattern provides consistency. The overlay should be a portal mounted at the document body level to avoid z-index stacking context issues with the sidebar layout.

**Alternatives considered**:
- Zustand store for search state: Unnecessary — TanStack Query already handles caching, loading, and error states. Search query text is local component state.
- React Router search route: Not needed — the search overlay is a modal, not a page. No URL change required.
- cmdk library: Would add a dependency but provides excellent keyboard navigation out of the box. However, the project doesn't currently use it, and the feature is simple enough to implement with native event handlers.

### 3. Grouping Strategy

**Decision**: Group results client-side by `normalised_type` after fetching from the backend.

**Rationale**: The backend returns resources with `normalised_type` as a field. Client-side grouping using a simple `reduce()` is trivial and avoids backend complexity. The backend search endpoint returns all matching resources (up to a reasonable page_size), and the frontend groups and limits display (5 initially, expandable to 10, then link to provider page).

**Alternatives considered**:
- Backend-side grouping with counts: Would require a new endpoint returning `{type: string, count: number, items: Resource[]}[]`. More complex, and the frontend already has all the data it needs.
- GraphQL with nested types: Not applicable — project uses REST.

### 4. Debounce Strategy

**Decision**: 300ms debounce on the search input, implemented via a `useDebouncedValue` hook that wraps `useState` + `useEffect` with a timeout.

**Rationale**: 300ms is the standard balance between responsiveness and avoiding excessive API calls. TanStack Query's `enabled` option ensures the query only fires when the debounced value is non-empty and at least 2 characters long (to avoid overly broad searches).

**Alternatives considered**:
- No debounce (search on every keystroke): Would flood the backend with requests during fast typing.
- 500ms debounce: Too sluggish — users perceive >300ms as noticeable delay.
- lodash.debounce: Adds a dependency for something achievable in 10 lines of React.

### 5. Backend Search Implementation Detail

**Decision**: Use Cypher `WHERE` clause with `toLower()` and `CONTAINS` for case-insensitive substring matching across multiple fields in the AGE graph query.

**Rationale**: Apache AGE supports Cypher's `toLower()` and `CONTAINS` string functions. The query pattern:
```
WHERE toLower(r.name) CONTAINS toLower($search)
   OR toLower(r.vendor_id) CONTAINS toLower($search)
   OR toLower(r.state) CONTAINS toLower($search)
   OR toLower(r.vendor) CONTAINS toLower($search)
   OR toLower(r.normalised_type) CONTAINS toLower($search)
```
This is simple, correct, and performant for datasets up to 10,000 resources (per SC-002).

**Alternatives considered**:
- PostgreSQL `ILIKE`: Would require switching from Cypher to SQL for this query, breaking the graph-first principle.
- Full-text search indexes: Over-engineered for the current scale requirements.
