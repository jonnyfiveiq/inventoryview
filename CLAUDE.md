# ScoreGraph Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-21

## Active Technologies
- TypeScript 5.4+, React 18 + Vite (build), React Router (routing), Shadcn/UI + Tailwind CSS (components/styling), Cytoscape.js (graph visualization), TanStack Query (data fetching/caching), Axios (HTTP client), Zustand (state management) (002-inventory-frontend-dashboard)
- N/A (all data from backend API; auth token in memory + sessionStorage) (002-inventory-frontend-dashboard)

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
- 002-inventory-frontend-dashboard: Added TypeScript 5.4+, React 18 + Vite (build), React Router (routing), Shadcn/UI + Tailwind CSS (components/styling), Cytoscape.js (graph visualization), TanStack Query (data fetching/caching), Axios (HTTP client), Zustand (state management)

- 001-foundation-core-api: Added Python 3.12+ (async-first) + FastAPI, uvicorn, psycopg[binary] (v3, async), PyJWT, cryptography (AES-256-GCM), argon2-cffi, pydantic, pydantic-settings, alembic

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
