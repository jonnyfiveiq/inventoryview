# ScoreGraph Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-22

## Active Technologies
- TypeScript 5.4+, React 18 + Vite (build), React Router (routing), Shadcn/UI + Tailwind CSS (components/styling), Cytoscape.js (graph visualization), TanStack Query (data fetching/caching), Axios (HTTP client), Zustand (state management) (002-inventory-frontend-dashboard)
- N/A (all data from backend API; auth token in memory + sessionStorage) (002-inventory-frontend-dashboard)
- TypeScript 5.7 (frontend), Python 3.12 (backend) + React 18, TanStack Query v5, Axios, lucide-react (frontend); FastAPI, psycopg3, Apache AGE/Cypher (backend) (003-spotlight-search)
- PostgreSQL 16 + Apache AGE graph (existing, no schema changes) (003-spotlight-search)

- Python 3.12+ (async-first) + FastAPI, uvicorn, psycopg[binary] (v3, async), PyJWT, cryptography (AES-256-GCM), argon2-cffi, pydantic, pydantic-settings, alembic (001-foundation-core-api)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12+ (async-first): Follow standard conventions

## Recent Changes
- 003-spotlight-search: Added TypeScript 5.7 (frontend), Python 3.12 (backend) + React 18, TanStack Query v5, Axios, lucide-react (frontend); FastAPI, psycopg3, Apache AGE/Cypher (backend)
- 002-inventory-frontend-dashboard: Added TypeScript 5.4+, React 18 + Vite (build), React Router (routing), Shadcn/UI + Tailwind CSS (components/styling), Cytoscape.js (graph visualization), TanStack Query (data fetching/caching), Axios (HTTP client), Zustand (state management)

- 001-foundation-core-api: Added Python 3.12+ (async-first) + FastAPI, uvicorn, psycopg[binary] (v3, async), PyJWT, cryptography (AES-256-GCM), argon2-cffi, pydantic, pydantic-settings, alembic

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
