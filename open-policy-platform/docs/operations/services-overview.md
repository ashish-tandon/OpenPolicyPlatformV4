# Services and Layers Overview

## Layers
- Backend API (FastAPI) — canonical REST at `/api/v1/*`
- Frontend (React + Vite) — consumes backend REST
- Database (PostgreSQL) — source of persisted policy and parliamentary data
- Scrapers — generate reports/logs, feed DB (via jobs/tools outside scope of unified API for now)
- Infrastructure — local dev scripts, optional containerization, monitoring
- Security — JWT auth, headers, validation, rate limiting

## Coordination points
- Frontend ↔ Backend: `VITE_API_URL` → `http://localhost:8000`
- Backend ↔ Database: `DATABASE_URL` (Settings.database_url)
- Backend ↔ Scrapers: reads `scraper_test_report_*.json`, `collection_report_*.json`, and `.log` files for status/metrics
- Admin workflows: `/api/v1/admin/*` for ops tasks

## Dependencies
- Python 3.8+, Node 18+, Postgres 14+
- Env vars defined in `docs/operations/environment-variables.md`

## Port map (default)
- API: 8000
- Web: 5173
- Postgres: 5432
- Redis: 6379 (optional)

## Data paths
- Exports/backups/logs written to repo root unless configured; ensure writable volume in production

## Ownership
- API contract: `docs/api/endpoints.md`
- Health/ops: `docs/operations/health-checks.md`
- Scripts: `docs/operations/scripts.md`
- Env: `docs/operations/environment-variables.md`