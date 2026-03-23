# InventoryView

Infrastructure inventory dashboard with a graph-based data model. Discover, browse, and visualise relationships across your entire infrastructure — VMware, AWS, Azure, OpenShift — from a single pane of glass.

![Dark Theme](https://img.shields.io/badge/theme-dark-1a1a2e)
![React 19](https://img.shields.io/badge/React-19-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16%20%2B%20AGE-336791)
![License](https://img.shields.io/badge/license-MIT-green)

## What it does

- **Netflix-style landing page** — horizontal carousels of resources grouped by normalised type (virtual machines, hypervisors, datastores, clusters, networks, etc.)
- **Spotlight search** — macOS Spotlight-style universal search overlay (Cmd+K / Ctrl+K) with real-time results grouped by taxonomy type across all providers, keyboard navigation, and sidebar search icon
- **Vendor carousel** — colour-coded cards for each provider with resource counts; click through to a vendor drill-down page
- **Resource playlists** — Spotify-style curated resource collections. Create playlists from the sidebar, add/remove resources from any resource detail page, view members in a detail page with infrastructure donut charts, activity calendar heatmap, and activity log. Playlists are available as JSON on a REST endpoint for external clients (Ansible, Nexus, etc.) to consume as guardrailed inventories
- **Resources Discovered heatmap** — at-a-glance summary showing counts by type, provider bar charts, and state distribution
- **Drift calendar heatmap** — GitHub-style contribution calendar showing drift activity across the fleet or per-resource, with click-to-filter day drill-down
- **Interactive graph visualisation** — Cytoscape.js overlay showing resource relationships (DEPENDS_ON, HOSTED_ON, MEMBER_OF, CONTAINS, CONNECTED_TO, ATTACHED_TO, MANAGES, etc.) with type-based node shapes, adjustable depth, pan/zoom, and click-to-expand
- **Drift tracking** — see how resource configuration changes over time (state, CPU, memory, IP, etc.) in a date-grouped modal
- **Provider drill-down** — filterable, paginated resource tables per vendor with inline graph access
- **Dark theme throughout** — modern, clean aesthetic

## Architecture

```
┌─────────────┐       ┌─────────────┐       ┌──────────────────────┐
│   Frontend   │──────▶│   Backend   │──────▶│  PostgreSQL 16       │
│  React SPA   │ REST  │   FastAPI   │  SQL  │  + Apache AGE graph  │
│  Vite + TS   │       │  Python 3.12│       │                      │
└─────────────┘       └─────────────┘       └──────────────────────┘
```

**Frontend**: React 19, TypeScript 5.7, Vite 6, Tailwind CSS v3, Cytoscape.js, TanStack Query v5, Zustand, Axios

**Backend**: FastAPI, psycopg3, Alembic, PyJWT, Argon2, Pydantic v2

**Database**: PostgreSQL 16 with [Apache AGE](https://age.apache.org/) graph extension for relationship traversal via Cypher queries

## Try it now

Pull and run a single container — no build required, batteries included:

```bash
docker pull quay.io/jhardy/inventoryview:latest
docker run -d --name inventoryview -p 8080:8080 quay.io/jhardy/inventoryview:latest
```

On first boot the container automatically:
1. Starts PostgreSQL 16 with Apache AGE
2. Runs database migrations
3. Creates the admin account
4. Seeds demo data (96 resources, 146 relationships, 44 drift entries, 4 playlists across VMware, AWS, Azure, OpenShift)

Open **http://localhost:8080** and log in with `admin` / `SuperSecretPass123`.

To stop and clean up:

```bash
docker stop inventoryview && docker rm inventoryview
```

> Works with both `docker` and `podman` — just substitute the command.

### Container environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IV_SEED_ON_BOOT` | `true` | Auto-seed demo data on first start |
| `IV_VAULT_PASSPHRASE` | `default-dev-passphrase` | Encryption key for stored credentials |
| `SEED_PASSWORD` | `SuperSecretPass123` | Admin password |

### Persist data across restarts

```bash
docker run -d --name inventoryview -p 8080:8080 \
  -v inventoryview-data:/var/lib/pgsql/data \
  quay.io/jhardy/inventoryview:latest
```

---

## Development setup

For working on the codebase with hot-reload:

### Prerequisites

- [Podman](https://podman.io/) or [Docker](https://www.docker.com/) with Compose
- [Node.js](https://nodejs.org/) 18+ and npm

### 1. Build the container images

```bash
# PostgreSQL + Apache AGE
podman build -t inventoryview-db:latest -f docker/Dockerfile.postgres docker/

# Backend
podman build -t inventoryview-backend:latest -f backend/Dockerfile.dev backend/
```

### 2. Start the services

```bash
podman compose -f docker/docker-compose.yml up -d
```

This starts PostgreSQL (port 5432) and the backend API (port 8080). Alembic migrations run automatically on startup.

### 3. Seed test data

```bash
# Seed all vendors (VMware, AWS, Azure, OpenShift)
./seed_test_data.sh --vendor=all

# Or seed individually
./seed_test_data.sh --vendor=vmware
./seed_test_data.sh --vendor=aws
./seed_test_data.sh --vendor=azure
./seed_test_data.sh --vendor=openshift
```

The seed script creates an admin account (`admin` / `SuperSecretPass123`), then populates:
- **96 resources** across 4 vendors
- **146 relationships** modelling real infrastructure topology
- **44 drift entries** showing configuration changes over time
- **4 playlists** with curated resource collections and activity history

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and log in with `admin` / `SuperSecretPass123`.

## Project structure

```
.
├── backend/                    # FastAPI backend
│   ├── src/inventoryview/
│   │   ├── api/v1/            # REST endpoints (auth, resources, relationships, playlists, drift, health, setup, credentials)
│   │   ├── services/          # Business logic (resources, graph, drift, playlists, auth, credentials, vault)
│   │   ├── models/            # Data models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── middleware/        # Auth middleware
│   ├── alembic/versions/      # Database migrations
│   └── pyproject.toml
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── api/               # Axios client, API functions, TypeScript types
│   │   ├── components/
│   │   │   ├── carousel/      # ResourceCarousel, ResourceCard, VendorCarousel
│   │   │   ├── graph/         # GraphOverlay, GraphCanvas, GraphControls
│   │   │   ├── drift/         # DriftCalendar, CalendarGrid, CalendarCell, CalendarNav, CalendarLegend
│   │   │   ├── heatmap/       # HeatmapStrip, HeatmapDetail, DonutChart
│   │   │   ├── layout/        # Sidebar, AppLayout (layout route), ErrorBanner
│   │   │   ├── playlist/      # AddToPlaylistButton, PlaylistActivityLog
│   │   │   ├── provider/      # ResourceTable, FilterBar
│   │   │   ├── resource/      # DriftModal
│   │   │   └── search/        # SpotlightOverlay, SearchInput, SearchResults, TaxonomyGroup, SearchResultItem
│   │   ├── hooks/             # TanStack Query hooks (useResources, useSearch, useGraph, useAuth, usePlaylists)
│   │   ├── pages/             # LoginPage, LandingPage, VendorPage, ProviderPage, ResourceDetailPage, PlaylistDetailPage, AnalyticsPage
│   │   ├── stores/            # Zustand auth store
│   │   └── router/            # React Router config, ProtectedRoute
│   └── package.json
├── docker/                     # Container definitions
│   ├── docker-compose.yml
│   └── Dockerfile.postgres    # PostgreSQL 16 + Apache AGE
├── specs/                      # Feature specifications (speckit)
│   ├── 001-foundation-core-api/
│   ├── 002-inventory-frontend-dashboard/
│   ├── 003-spotlight-search/
│   ├── 004-drift-calendar-heatmap/
│   └── 005-resource-playlists/
├── seed_test_data.sh          # Multi-vendor test data seeder
└── Makefile
```

## API overview

All endpoints under `/api/v1/`. Authentication via JWT bearer token.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth) |
| `/setup/status` | GET | Check if initial setup is complete (no auth) |
| `/setup/init` | POST | Create initial admin account (no auth) |
| `/auth/login` | POST | Authenticate and receive JWT |
| `/auth/revoke` | POST | Revoke a token |
| `/resources` | GET | List resources with filtering, search, and cursor pagination |
| `/resources/{uid}` | GET | Get full resource detail |
| `/resources/{uid}/relationships` | GET | List relationships for a resource |
| `/resources/{uid}/graph` | GET | Graph traversal (BFS) with configurable depth |
| `/resources/{uid}/drift` | GET | Drift history for a resource |
| `/resources/{uid}/drift/exists` | GET | Check if drift entries exist |
| `/resources/{uid}/drift` | POST | Record a drift entry |
| `/resources/{uid}/drift/timeline` | GET | Aggregated daily drift timeline |
| `/resources/{uid}/playlists` | GET | Playlists containing this resource |
| `/playlists` | GET | List all playlists with member counts |
| `/playlists` | POST | Create a new playlist |
| `/playlists/{identifier}` | GET | Get playlist detail by slug or UUID (`?detail=full` for raw properties) |
| `/playlists/{identifier}` | PATCH | Update playlist name/description |
| `/playlists/{identifier}` | DELETE | Delete a playlist |
| `/playlists/{identifier}/members` | POST | Add a resource to a playlist |
| `/playlists/{identifier}/members/{uid}` | DELETE | Remove a resource from a playlist |
| `/playlists/{identifier}/activity` | GET | Activity log for a playlist (filterable by date) |
| `/playlists/{identifier}/activity/timeline` | GET | Aggregated daily activity timeline |
| `/fleet/drift/timeline` | GET | Fleet-wide aggregated drift timeline |
| `/credentials` | GET/POST | Manage collector credentials |

## Graph model

Resources are stored as nodes in an Apache AGE graph. Relationships are typed, directed edges:

```
DEPENDS_ON, HOSTED_ON, MEMBER_OF, CONTAINS, CONNECTED_TO,
ATTACHED_TO, MANAGES, ROUTES_TO, PEERS_WITH
```

The graph API performs iterative BFS traversal per depth level, returning nodes and edges for Cytoscape.js rendering. Each node carries `normalised_type` which determines its visual shape in the graph overlay (ellipse, hexagon, barrel, diamond, triangle, pentagon, etc.).

## Normalised taxonomy

Resources from any vendor are classified into a universal type system:

`virtual_machine`, `hypervisor`, `datastore`, `virtual_switch`, `port_group`, `cluster`, `datacenter`, `resource_pool`, `management_plane`, `folder`, `network`, `subnet`, `security_group`, `load_balancer`, `object_store`, `managed_database`, `kubernetes_cluster`, `kubernetes_node`, `namespace`, `deployment`, `statefulset`, `ingress`, `service`, `persistent_volume`, `route`, `virtual_network`, `network_gateway`

## Building the container image

Build and push with the included script:

```bash
./build-and-push.sh            # build + push to quay.io/jhardy/inventoryview:latest
./build-and-push.sh --no-push  # build only, don't push
./build-and-push.sh --tag v1.0 # custom tag
./build-and-push.sh --docker   # force docker (default: auto-detects podman/docker)
```

Or manually:

```bash
docker build -t inventoryview:latest -f backend/Dockerfile .
docker tag inventoryview:latest quay.io/jhardy/inventoryview:latest
docker push quay.io/jhardy/inventoryview:latest
```

> Multi-stage build: Node 18 (frontend) + CentOS Stream 9 (AGE compile) + CentOS Stream 9 (runtime with PostgreSQL 16, Python 3.12, compiled frontend).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IV_DATABASE_URL` | `postgresql://postgres@127.0.0.1:5432/inventoryview` | PostgreSQL connection string |
| `IV_VAULT_PASSPHRASE` | `default-dev-passphrase` | Encryption key for stored credentials |
| `IV_SEED_ON_BOOT` | `true` | Auto-seed demo data on first start |
| `IV_UI_DIR` | `/app/ui` | Path to frontend static files |
| `SEED_PASSWORD` | `SuperSecretPass123` | Admin password for seeding |
| `VITE_API_BASE_URL` | `/api/v1` | Backend API base URL (frontend dev only) |
| `SEED_BASE_URL` | `http://localhost:8080/api/v1` | Backend URL for seed script |

## Useful commands

```bash
# Run backend tests
cd backend && python -m pytest -v

# Lint backend
cd backend && python -m ruff check src/ tests/

# Build frontend for production
cd frontend && npm run build
```

## Licence

MIT
