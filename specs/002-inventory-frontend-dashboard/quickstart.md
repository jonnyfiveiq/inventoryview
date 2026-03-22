# Quickstart: InventoryView Frontend Dashboard

**Feature**: 002-inventory-frontend-dashboard
**Date**: 2026-03-22

## Prerequisites

- Node.js 20+ and npm
- Running InventoryView backend at `http://localhost:8000` (via `docker compose up`)
- Seeded test data (run `./seed_test_data.sh --vendor=vmware` from repo root)

## Development Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` with hot module replacement. API requests are proxied to `http://localhost:8000` via Vite's proxy config.

## First Run Walkthrough

1. **Setup check**: App detects if setup is complete via `GET /api/v1/setup/status`.
   - If not, shows setup page to create admin account.

2. **Login**: Enter credentials on login page → `POST /api/v1/auth/login` → token stored in memory.

3. **Landing page**: Fetches all resources → groups by `normalised_type` → renders carousels.
   - Compact heatmap strip at top shows category counts and state distribution.

4. **Provider drill-down**: Click a vendor badge → navigates to `/providers/:vendor` → filtered resource table with pagination.

5. **Resource detail**: Click a resource card or table row → navigates to `/resources/:uid` → full properties + "View Graph" button.

6. **Graph overlay**: Click graph icon in resource table row or "View Graph" on detail page → full-screen overlay with Cytoscape.js graph. Adjust depth slider, click nodes to inspect, click peripheral nodes to expand.

7. **Analytics**: Click "Analytics" in sidebar → full heatmaps for category, state, and activity.

## Integration Test Scenarios

### Scenario 1: Landing Page Carousels
```
1. Login as admin
2. GET /api/v1/resources?page_size=200
3. Verify response groups into carousels by normalised_type
4. Verify each card shows: name, vendor badge, state indicator
5. Verify empty types have no carousel
```

### Scenario 2: Provider Drill-Down
```
1. Navigate to /providers/vmware
2. GET /api/v1/resources?vendor=vmware&page_size=50
3. Apply filter: category=compute
4. GET /api/v1/resources?vendor=vmware&category=compute&page_size=50
5. Verify filtered results
6. Scroll to trigger pagination (cursor from next_cursor)
```

### Scenario 3: Graph Visualization
```
1. Click graph icon on a resource row
2. GET /api/v1/resources/{uid}/graph?depth=1
3. Verify Cytoscape.js renders nodes and edges
4. Change depth slider to 2
5. GET /api/v1/resources/{uid}/graph?depth=2
6. Verify additional nodes appear
7. Click a peripheral node
8. GET /api/v1/resources/{peripheral_uid}/graph?depth=1
9. Verify graph expands with new connections
```

### Scenario 4: Auth Flow
```
1. Navigate to / without token → redirected to /login
2. POST /api/v1/auth/login with valid creds → redirected to /
3. Verify token in auth store
4. Wait for token expiry or POST /api/v1/auth/revoke
5. Next API call returns 401 → redirected to /login
```

### Scenario 5: Heatmaps
```
1. Load landing page
2. Verify compact heatmap strip shows category counts
3. Navigate to /analytics
4. Verify full heatmaps: category counts, state distribution, recent activity
5. Hover over a heatmap cell → verify tooltip shows exact count
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| VITE_API_BASE_URL | `/api/v1` | Backend API base URL |

## Build for Production

```bash
cd frontend
npm run build
```

Output in `frontend/dist/` — static files ready for serving via nginx, caddy, or the backend's static file handler.
