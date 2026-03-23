# Research: Drift Calendar Heatmap

**Feature**: 004-drift-calendar-heatmap | **Date**: 2026-03-22

## Decision 1: Backend Aggregation Strategy

**Decision**: Add a new SQL aggregation endpoint rather than fetching all raw drift entries and aggregating client-side.

**Rationale**: A resource with 1,000 drift entries over a year means transferring and processing all 1,000 records on the client just to count per-day totals. A SQL `GROUP BY DATE(changed_at)` is far more efficient — returns at most 365 rows per resource regardless of event volume. For the fleet calendar, client-side aggregation of raw events across all resources would be prohibitively expensive.

**Alternatives considered**:
- Client-side aggregation of existing `GET /resources/{uid}/drift` — rejected due to data transfer volume and client computation cost at scale
- Materialised view or pre-aggregated table — rejected as premature optimisation; the query is fast enough with an index on `(resource_uid, changed_at)`

## Decision 2: Calendar Rendering Approach

**Decision**: Build a custom SVG-based calendar grid component using React, matching the GitHub contribution graph layout (weeks as columns, days as rows, 53 columns × 7 rows).

**Rationale**: The GitHub contribution graph is a well-understood visual pattern. Building it as a custom SVG component gives full control over the dark-theme colour scheme, tooltip positioning, click handlers, and responsive behaviour. External calendar heatmap libraries either bring unwanted dependencies or don't match the project's Tailwind/dark-theme styling.

**Alternatives considered**:
- External library (react-calendar-heatmap, nivo) — rejected because they add bundle weight and require theme overrides that fight the existing design system
- CSS Grid with `<div>` cells — viable but SVG provides better control for consistent cell sizing, tooltips, and the colour-fill rendering path

## Decision 3: Two-Layer Colour Intensity Model

**Decision**: Compute cell colour using two factors: (1) the resource's total lifetime drift count divided by the fleet average lifetime drift count produces a base intensity multiplier (0.0–1.0), and (2) the day's event count produces a spike factor. The final intensity = `clamp(baseIntensity * 0.4 + spikeIntensity * 0.6, 0, 1)` mapped onto a 5-step colour scale.

**Rationale**: This satisfies the user's requirement that "resources with more changes compared to everything else in the db go more red." The lifetime component ensures consistently noisy resources appear warmer even on low-drift days; the daily spike component ensures sudden change storms are visually prominent.

**Alternatives considered**:
- Pure per-day absolute thresholds — rejected because it loses the "compared to everything else" relative context
- Pure lifetime-only comparison — rejected because it makes all days the same colour for a given resource, losing temporal detail
- Percentile-based ranking — considered but adds complexity; simple ratio to fleet mean is sufficient for the current scale

## Decision 4: Fleet Statistics Delivery

**Decision**: The fleet-wide drift timeline endpoint returns pre-aggregated daily totals plus the fleet average lifetime drift count. The frontend uses these directly without additional fleet-level queries.

**Rationale**: A single endpoint (`GET /drift/fleet-timeline`) returning `{ days: [{date, count, fields}], fleet_avg_lifetime: number, total_resources_with_drift: number }` gives the frontend everything it needs for both the fleet calendar and the per-resource relative colouring in one round-trip.

**Alternatives considered**:
- Separate endpoints for fleet stats and fleet timeline — rejected to reduce round-trips
- Embed fleet stats in each per-resource timeline response — rejected because it couples concerns; the fleet calendar needs fleet data without a resource context

## Decision 5: Drift Modal Date Filtering

**Decision**: Extend the existing DriftModal to accept an optional `filterDate` prop. When provided, the modal fetches drift entries as usual but filters them client-side to the specified date. This avoids a new backend endpoint for date-filtered drift.

**Rationale**: The existing `GET /resources/{uid}/drift` already returns all entries. Filtering client-side by date is trivial and avoids backend changes for a P3 feature. At scale, if the full drift history becomes too large, a server-side `date` query parameter can be added later.

**Alternatives considered**:
- New backend endpoint with date filter — deferred; not needed at current scale
- New modal component — rejected; the existing DriftModal already groups by date, just needs a filter prop
