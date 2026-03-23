# Quickstart: Resource Playlists

**Feature**: 005-resource-playlists
**Date**: 2026-03-22

## Scenario 1: Create a Playlist and Add Resources (P1 MVP)

1. Log in to InventoryView
2. In the left sidebar, find the "Playlists" section
3. Click the "+" or "New Playlist" button
4. A new playlist appears with an editable default name — type "Production OCP Cluster"
5. Navigate to a resource detail page (e.g., `master-0.ocp-prod-rdu`)
6. Click "Add to Playlist" button
7. Check "Production OCP Cluster" in the dropdown
8. Resource is added — navigate back to the playlist via sidebar
9. Verify the resource appears in the playlist members table

**Expected result**: Playlist visible in sidebar, resource listed in playlist detail page.

## Scenario 2: External Client Consumes Playlist via REST (P2)

1. Create a playlist "DMZ Network Devices" and add several resources
2. On the playlist detail page, note the endpoint URL displayed (e.g., `/api/v1/playlists/dmz-network-devices`)
3. Click "JSON" button to preview the response
4. From a terminal or external tool, make a GET request:
   ```
   curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/playlists/dmz-network-devices
   ```
5. Verify the JSON matches the preview shown in the UI
6. Try with `?detail=full` to get raw_properties included

**Expected result**: JSON response contains playlist metadata + member resources. Summary by default, full detail with query param.

## Scenario 3: Track Playlist Activity Over Time (P3)

1. Create a playlist and add/remove several resources over multiple days
2. Navigate to the playlist detail page
3. View the activity log — verify each add/remove action is recorded
4. View the calendar heatmap — days with changes should be highlighted
5. Click a highlighted day — activity log filters to that day
6. Delete a resource from the system — verify the playlist activity shows "resource deleted from system"

**Expected result**: Complete audit trail of all playlist changes. Calendar heatmap shows change frequency visually.

## Scenario 4: Infrastructure Composition View (P3)

1. Build a playlist containing resources from multiple vendors (VMware VMs, OpenShift nodes, Cisco switches, NetApp storage)
2. Navigate to the playlist detail page
3. View the infrastructure donut charts
4. Verify Private Cloud shows VMware + OpenShift resources, Public Cloud shows AWS/Azure, Networking shows Cisco, Storage shows NetApp

**Expected result**: Donut charts accurately reflect the infrastructure type breakdown of the playlist's members.

## Seed Data Recommendations

To test this feature effectively, the existing seed data should be extended with:
- At least 2 pre-created playlists (e.g., "Production Cluster", "Development Environment")
- 5-10 resources added to each playlist
- Activity log entries spanning multiple days for each playlist
- This enables immediate testing of all scenarios without manual setup
