# Reference Cards

## Backend API
- Base URL: http://localhost:8000
- Docs: /docs
- Start: `uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`
- Env: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, `LOG_LEVEL`

## Frontend
- Dev: `cd web && npm install && npm run dev`
- Build: `cd web && npm run build`
- Env: `VITE_API_URL`

## Health
- Liveness: `GET /api/v1/health`
- Readiness: `GET /api/v1/health/detailed`

## Scrapers
- Inventory: `GET /api/v1/scrapers`
- Run one: `POST /api/v1/scrapers/{id}/run`
- Logs: `GET /api/v1/scrapers/{id}/logs`

## Data
- Tables: `GET /api/v1/data/tables`
- Export: `POST /api/v1/data/export`

## Admin (admin)
- Dashboard: `GET /api/v1/admin/dashboard`
- Logs: `GET /api/v1/admin/logs?log_type=all&limit=100`

## Scripts
- Setup: `./scripts/setup-unified.sh`
- Start all: `./scripts/start-all.sh`
- Deploy w/ migration: `./scripts/deploy-with-migration.sh`
- Docs check: `./scripts/check-docs-links.sh`
- Export OpenAPI: `./scripts/export-openapi.sh`

## CI
- Workflow: `.github/workflows/docs-openapi.yml`
- Artifacts: `dist/openapi.json`