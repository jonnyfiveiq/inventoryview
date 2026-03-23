# ScoreGraph Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-22

## Active Technologies
- TypeScript 5.4+, React 18 + Vite (build), React Router (routing), Shadcn/UI + Tailwind CSS (components/styling), Cytoscape.js (graph visualization), TanStack Query (data fetching/caching), Axios (HTTP client), Zustand (state management) (002-inventory-frontend-dashboard)
- N/A (all data from backend API; auth token in memory + sessionStorage) (002-inventory-frontend-dashboard)
- TypeScript 5.7 (frontend), Python 3.12 (backend) + React 18, TanStack Query v5, Axios, lucide-react (frontend); FastAPI, psycopg3, Apache AGE/Cypher (backend) (003-spotlight-search)
- PostgreSQL 16 + Apache AGE graph (existing, no schema changes) (003-spotlight-search)
- TypeScript 5.7 (frontend), Python 3.12 (backend) + React 18, TanStack Query v5, Axios, lucide-react (frontend); FastAPI, psycopg3 (backend) (004-drift-calendar-heatmap)
- PostgreSQL 16 + Apache AGE graph (existing `resource_drift` table, no schema changes) (004-drift-calendar-heatmap)
- Python 3.12+ (backend), TypeScript 5.4+ (frontend) + FastAPI, React 18, TanStack Query, Shadcn/UI + Tailwind CSS (005-resource-playlists)
- PostgreSQL 16+ (standard relational tables, not Apache AGE graph) (005-resource-playlists)
- Python 3.12+ (async-first) for backend; TypeScript 5.4+ for frontend + FastAPI, psycopg[binary] (v3, async), Pydantic v2, python-multipart (file uploads), zipfile/tarfile (stdlib), csv (stdlib); React 18 + Vite, TanStack Query, Zustand, Cytoscape.js, Axios (006-aap-automation-correlation)
- PostgreSQL 16+ with Apache AGE extension — relational tables for AAP data (hosts, jobs, pending matches, learned mappings), graph nodes (`AAPHost`) and edges (`AUTOMATED_BY`) for correlation (006-aap-automation-correlation)
- Python 3.12+ (backend), TypeScript 5.4+ (frontend) + FastAPI, psycopg (async), React 18, TanStack Query, Zustand, Tailwind CSS, Shadcn/UI (007-ui-usage-audit)
- PostgreSQL 16+ (relational tables — usage events and login audit are metadata, not graph data per Constitution Principle I) (007-ui-usage-audit)

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
- 007-ui-usage-audit: Added Python 3.12+ (backend), TypeScript 5.4+ (frontend) + FastAPI, psycopg (async), React 18, TanStack Query, Zustand, Tailwind CSS, Shadcn/UI
- 007-ui-usage-audit: Added Python 3.12+ (backend), TypeScript 5.4+ (frontend) + FastAPI, psycopg (async), React 18, TanStack Query, Zustand, Tailwind CSS, Shadcn/UI
- 006-aap-automation-correlation: Added Python 3.12+ (async-first) for backend; TypeScript 5.4+ for frontend + FastAPI, psycopg[binary] (v3, async), Pydantic v2, python-multipart (file uploads), zipfile/tarfile (stdlib), csv (stdlib); React 18 + Vite, TanStack Query, Zustand, Cytoscape.js, Axios


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
