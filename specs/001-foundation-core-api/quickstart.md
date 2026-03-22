# Quickstart: Foundation Core API

**Feature**: 001-foundation-core-api
**Date**: 2026-03-21

## Prerequisites

- Docker (or Podman)
- Git
- Python 3.12+ (for local development)
- Node.js 20+ (for frontend, optional for M1)

## 1. Clone and Start (Docker)

```bash
git clone <repo-url> inventoryview
cd inventoryview

# Build the single-container image
docker build -t inventoryview:dev -f backend/Dockerfile .

# Run with vault passphrase (required)
docker run -d \
  --name inventoryview \
  -p 8080:8080 \
  -e IV_VAULT_PASSPHRASE="your-secure-passphrase" \
  -v inventoryview-data:/var/lib/postgresql/data \
  inventoryview:dev
```

The system starts within 60 seconds. PostgreSQL initialises automatically on first run.

## 2. Development Setup (Docker Compose)

```bash
# Start full dev stack with hot-reloading
docker compose -f docker/docker-compose.yml up -d

# Verify services
curl http://localhost:8080/api/v1/health
```

## 3. Local Development (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set required env vars
export IV_DATABASE_URL="postgresql://inventoryview:inventoryview@localhost:5432/inventoryview"
export IV_VAULT_PASSPHRASE="dev-passphrase"

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn inventoryview.main:app --host 0.0.0.0 --port 8080 --reload
```

**Note**: Local development requires a running PostgreSQL 16 instance with the
Apache AGE extension installed.

## 4. Initial Setup

After the system starts:

```bash
# Check if setup is needed
curl http://localhost:8080/api/v1/setup/status
# {"setup_complete": false}

# Create admin password
curl -X POST http://localhost:8080/api/v1/setup/init \
  -H "Content-Type: application/json" \
  -d '{"password": "your-admin-password"}'
```

## 5. Authenticate

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-admin-password"}' \
  | jq -r '.token')

# Use token for subsequent requests
curl http://localhost:8080/api/v1/resources \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Run Tests

```bash
cd backend

# Unit tests (fast, no DB needed)
pytest tests/unit/ -v

# Integration tests (requires Docker for testcontainers)
pytest tests/integration/ -v

# All tests
pytest -v

# Linting
ruff check src/
ruff format --check src/
```

## 7. Makefile Targets

```bash
make dev        # Start development stack
make test       # Run all tests
make lint       # Run linter
make build      # Build Docker image
```

## 8. Key Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| IV_VAULT_PASSPHRASE | Yes | — | Passphrase for credential vault encryption |
| IV_DATABASE_URL | No | embedded PG | External PostgreSQL connection string |
| IV_TOKEN_EXPIRY_HOURS | No | 24 | JWT token expiry in hours |
| IV_HOST | No | 0.0.0.0 | API server bind address |
| IV_PORT | No | 8080 | API server port |
| IV_GRAPH_NAME | No | inventory_graph | AGE graph name |
| IV_MAX_TRAVERSAL_DEPTH | No | 5 | Max graph traversal depth |

## 9. API Documentation

Once running, visit:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- Health check: http://localhost:8080/api/v1/health
