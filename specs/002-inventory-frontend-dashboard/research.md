# Research: InventoryView Frontend Dashboard

**Feature**: 002-inventory-frontend-dashboard
**Date**: 2026-03-22

## Decision 1: Graph Visualization Library

**Decision**: Cytoscape.js

**Rationale**: Cytoscape.js is purpose-built for network/graph visualization with first-class support for:
- Node and edge rendering with automatic layout algorithms (cola, dagre, breadthfirst)
- Built-in pan, zoom, box selection, and tap events
- Compound nodes (for grouping by vendor/category if needed later)
- Extensions ecosystem: `cytoscape-popper` for tooltips, `cytoscape-cola` for force-directed layouts
- TypeScript definitions available (`@types/cytoscape`)
- Lightweight (~400KB gzipped) with no DOM dependency — renders to canvas
- Well-suited for 50-500 node graphs typical of infrastructure topology

**Alternatives considered**:
- **D3.js**: More flexible but lower-level. Requires building graph interactions (pan, zoom, drag, click events) from scratch using `d3-force`, `d3-zoom`, `d3-drag`. Better for custom statistical visualizations (heatmaps, charts) but significantly more work for interactive graph navigation. Would use D3 for heatmaps separately.
- **vis.js/vis-network**: Good graph viz but larger bundle, less active maintenance, weaker TypeScript support.
- **React Flow**: Designed for flowchart/diagram editors, not topology graph exploration. Overkill node chrome for simple resource cards.
- **Sigma.js**: Optimized for very large graphs (10k+ nodes) but more complex API for small/medium graphs.

## Decision 2: State Management

**Decision**: Zustand (minimal store) + TanStack Query (server state)

**Rationale**: The frontend is primarily a server-state consumer — most state lives in the backend API. TanStack Query handles fetching, caching, invalidation, and pagination out of the box. Zustand provides a lightweight store for the few pieces of client state needed (auth token, sidebar collapsed state, graph overlay open/closed). This avoids the boilerplate of Redux or the complexity of MobX for what is essentially a read-heavy dashboard.

**Alternatives considered**:
- **Redux Toolkit**: Overkill for this use case. Mostly read-only data from API.
- **Jotai/Recoil**: Atom-based models add unnecessary abstraction when there are only 2-3 pieces of global client state.
- **React Context alone**: Sufficient for auth but would require manual caching logic for API data.

## Decision 3: HTTP Client

**Decision**: Axios

**Rationale**: Axios provides interceptors for automatic auth token injection and 401 → redirect-to-login handling. The interceptor pattern cleanly separates auth concerns from API call sites. Response/request interceptors also allow consistent error formatting.

**Alternatives considered**:
- **fetch + wrapper**: Viable but requires building interceptor pattern manually. No built-in timeout, retry, or request cancellation.
- **ky**: Lighter than Axios but less ecosystem adoption and no interceptor chain.

## Decision 4: Heatmap Rendering

**Decision**: Custom components using Tailwind CSS utility classes + lightweight D3 scales

**Rationale**: The heatmaps in the spec are relatively simple — category counts, state distributions, and activity recency indicators. These don't require a full charting library. Coloured grid cells with Tailwind's bg-opacity utilities and D3's colour scales (`d3-scale-chromatic`) provide the exact heat gradient needed. Tooltips via Shadcn/UI `Tooltip` component.

**Alternatives considered**:
- **Recharts/Nivo**: Full charting libraries. Would pull in significant bundle size for what amounts to coloured grid cells with counts.
- **Chart.js**: Canvas-based, good for time-series but awkward for heatmap grids.
- **Pure CSS**: Possible but D3 colour scales provide perceptually uniform gradients that pure CSS can't match easily.

## Decision 5: Carousel Implementation

**Decision**: Custom carousel with CSS scroll-snap + arrow buttons

**Rationale**: The Netflix-style carousel is a horizontal scrollable container. CSS `scroll-snap-type: x mandatory` with `scroll-snap-align: start` on cards provides native smooth scrolling with snapping. Arrow buttons use `scrollBy()` for keyboard/mouse navigation. This avoids a carousel library dependency and gives full control over card sizing, spacing, and the overall aesthetic.

**Alternatives considered**:
- **Embla Carousel**: Feature-rich but adds a dependency for behaviour achievable with CSS scroll-snap.
- **Swiper**: Heavy (40KB+), mobile-first focus, complex API for simple horizontal scroll.
- **Shadcn/UI Carousel**: Built on Embla — reasonable option but custom CSS scroll-snap is simpler for this use case and avoids the dependency.

## Decision 6: Routing

**Decision**: React Router v6

**Rationale**: De facto standard for React SPA routing. Supports nested layouts (sidebar persists across pages), route guards (auth check), and URL parameters for provider/resource views.

**Alternatives considered**:
- **TanStack Router**: Type-safe routing but newer, smaller ecosystem. Unnecessary complexity for 5-6 routes.

## Decision 7: Token Storage

**Decision**: In-memory (Zustand store) + sessionStorage fallback

**Rationale**: Storing JWT in memory prevents XSS-based token theft (no localStorage). sessionStorage is used only to survive page refreshes within a tab — cleared when the tab closes. This matches the spec's requirement for graceful session management without persistent login.

**Alternatives considered**:
- **localStorage**: Persists across tabs/sessions but vulnerable to XSS reads.
- **httpOnly cookie**: Would require backend changes to set cookies. Backend currently returns token in response body.
- **Memory only**: Cleanest but forces re-login on every page refresh, which is poor UX.
