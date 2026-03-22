# Quickstart: Spotlight-Style Universal Search

**Feature**: 003-spotlight-search
**Date**: 2026-03-22

## Prerequisites

- Running InventoryView instance with seeded data (96 resources across VMware, AWS, Azure, OpenShift)
- Authenticated user session

## Test Scenarios

### Scenario 1: Basic Search via Keyboard Shortcut

1. Log in to InventoryView
2. Press **Cmd+K** (Mac) or **Ctrl+K** (Windows/Linux)
3. Verify: Centered search overlay appears with blurred/dimmed background, input is focused
4. Type "esxi"
5. Verify: Results appear grouped by taxonomy (e.g., "Hypervisor (3)")
6. Verify: Each result shows name, provider (VMware), and state
7. Press **Escape**
8. Verify: Overlay closes

### Scenario 2: Cross-Provider Search

1. Open search overlay (Cmd+K)
2. Type "prod"
3. Verify: Results from multiple providers appear (e.g., VMware VMs, AWS instances, Azure VMs all with "prod" in the name)
4. Verify: Results are grouped by normalised_type, not by provider

### Scenario 3: Search by State

1. Open search overlay (Cmd+K)
2. Type "running"
3. Verify: All resources with state "running" appear, grouped by type

### Scenario 4: Keyboard Navigation

1. Open search overlay and type "vm"
2. Press **Down arrow** — first result highlights
3. Press **Down arrow** again — second result highlights (may cross taxonomy groups)
4. Press **Enter** — navigates to the highlighted resource's detail page
5. Verify: Overlay closes and resource detail page loads

### Scenario 5: Click Navigation

1. Open search overlay and type "cluster"
2. Click on any result
3. Verify: Navigates to that resource's detail page

### Scenario 6: Header Icon

1. Look for search icon in the sidebar/header
2. Hover over it — verify keyboard shortcut hint appears
3. Click the icon
4. Verify: Search overlay opens with input focused

### Scenario 7: No Results

1. Open search overlay
2. Type "zzzznonexistent"
3. Verify: "No results found" message appears

### Scenario 8: Show More / View All

1. Open search overlay
2. Type a broad term (e.g., "vm" which should match many virtual_machine resources)
3. Verify: Each taxonomy group shows up to 5 results with a "Show more" link
4. Click "Show more" — verify group expands to show up to 10
5. If more than 10 exist, verify "View all X on provider page" link appears
6. Click "View all" link — verify navigation to provider page with search pre-filled

### Scenario 9: Empty Input

1. Open search overlay
2. Verify: "Start typing to search..." prompt appears
3. Type "ab" then clear the input
4. Verify: Results clear and prompt reappears
