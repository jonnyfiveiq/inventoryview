# Data Model: Spotlight-Style Universal Search

**Feature**: 003-spotlight-search
**Date**: 2026-03-22

## Overview

This feature does not introduce new persistent entities. It operates on the existing Resource graph nodes and adds a search query parameter to the existing API. The data model below documents the transient structures used in the search flow.

## Existing Entities (Referenced)

### Resource (Graph Node — existing, no changes)

| Field | Type | Searchable | Description |
|-------|------|------------|-------------|
| uid | UUID | No | Unique identifier |
| name | string | Yes | Resource display name |
| vendor_id | string | Yes | Vendor-specific resource ID |
| vendor | string | Yes | Provider name (VMware, AWS, Azure, OpenShift) |
| vendor_type | string | No | Vendor-specific type |
| normalised_type | string | Yes | Universal taxonomy type |
| category | string | No | Resource category |
| region | string | No | Cloud region |
| state | string | Yes | Current resource state |
| first_seen | datetime | No | Discovery timestamp |
| last_seen | datetime | No | Last confirmation timestamp |

## Transient Structures (Frontend Only)

### SearchState

Represents the current state of the search overlay in the UI.

| Field | Type | Description |
|-------|------|-------------|
| isOpen | boolean | Whether the search overlay is visible |
| query | string | Current text in the search input |
| debouncedQuery | string | Query value after 300ms debounce |
| highlightedIndex | number | Currently keyboard-highlighted result index (-1 = none) |

### TaxonomyGroup

A client-side grouping of search results by normalised_type.

| Field | Type | Description |
|-------|------|-------------|
| type | string | Normalised taxonomy type (e.g., "virtual_machine") |
| label | string | Human-readable label (e.g., "Virtual Machine") |
| totalCount | number | Total matching resources in this group |
| items | SearchResult[] | Resources in this group (limited to 5 or 10) |
| isExpanded | boolean | Whether "Show more" has been clicked |

### SearchResult

A single result item within a taxonomy group.

| Field | Type | Description |
|-------|------|-------------|
| uid | string | Resource UID for navigation |
| name | string | Resource display name |
| vendor | string | Provider name |
| state | string | Current state |
| normalised_type | string | Taxonomy type (used for grouping) |
| vendor_id | string | Vendor-specific ID |

## API Changes

### GET /api/v1/resources — Extended Query Parameters

New parameter added to existing endpoint:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Case-insensitive substring match against name, vendor_id, state, vendor, and normalised_type. Minimum 2 characters. |

Existing parameters remain unchanged: vendor, category, region, state, cursor, page_size.

When `search` is provided, the Cypher query adds OR-chained `CONTAINS` clauses across the searchable fields.

## Relationships

No new relationships are introduced. Search results link to existing resource detail pages via the resource `uid`.
