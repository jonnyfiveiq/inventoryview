# Quickstart: Drift Calendar Heatmap

**Feature**: 004-drift-calendar-heatmap | **Date**: 2026-03-22

## Prerequisites

- Backend running (port 8080) with seeded data (96 resources, 44 drift entries)
- Frontend running (port 5173)
- Logged in as admin

## Test Scenarios

### Scenario 1: Resource Calendar Renders

1. Navigate to a resource detail page for a resource with known drift history (e.g., click a resource from the landing page)
2. **Verify**: A GitHub-style calendar heatmap appears on the resource detail page
3. **Verify**: The grid shows 53 columns (weeks) × 7 rows (days of week)
4. **Verify**: Month labels appear along the top
5. **Verify**: Some cells are coloured (days with drift) and most are neutral/empty

### Scenario 2: Discovery Day Colour

1. Navigate to a resource detail page
2. Find the resource's `first_seen` date
3. **Verify**: The calendar cell for the discovery date is coloured blue/teal
4. **Verify**: This colour is visually distinct from the warm drift colours (yellow/orange/red)

### Scenario 3: Drift Day Colours

1. Navigate to a resource with multiple drift events on different days
2. **Verify**: Days with drift events are coloured in warm tones (yellow → orange → red)
3. **Verify**: Days with more events appear warmer/redder than days with fewer events

### Scenario 4: Relative Intensity

1. Find two resources: one with many total drift events, one with few
2. Navigate to the high-drift resource's detail page
3. **Verify**: Calendar cells appear generally warmer (more red/orange)
4. Navigate to the low-drift resource's detail page
5. **Verify**: Calendar cells appear generally cooler (more yellow/light) even for days with events

### Scenario 5: Tooltip on Hover

1. Navigate to a resource with drift history
2. Hover over a coloured (non-discovery) cell
3. **Verify**: Tooltip shows the date, number of drift events, and which fields changed
4. Hover over the discovery cell
5. **Verify**: Tooltip shows the date and indicates it was the discovery date

### Scenario 6: Click-Through to Drift Modal

1. Navigate to a resource with drift history
2. Click on a coloured drift cell
3. **Verify**: The drift modal opens showing only the changes from that specific day
4. Close the modal
5. Click on an empty/neutral cell
6. **Verify**: Nothing happens (no modal opens)

### Scenario 7: Fleet Calendar on Landing Page

1. Navigate to the landing page (/)
2. **Verify**: A fleet-wide calendar heatmap is displayed
3. **Verify**: Cell colours reflect aggregate drift activity across all resources
4. Hover over a coloured cell
5. **Verify**: Tooltip shows the total drift event count for that day and fields changed

### Scenario 8: Fleet Calendar on Analytics Page

1. Navigate to the analytics page (/analytics)
2. **Verify**: A fleet-wide calendar heatmap is displayed (same data as landing page)
3. **Verify**: Cell colours match the landing page fleet calendar

### Scenario 9: Resource with No Drift

1. Navigate to a resource that has never had any drift events
2. **Verify**: The calendar shows only the discovery-day cell coloured (blue/teal)
3. **Verify**: All other cells are neutral/empty
4. **Verify**: No error or broken UI
