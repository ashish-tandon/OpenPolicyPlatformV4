# API Endpoints (Canonical Reference)

This list is generated from the mounted routers in `backend/api/main.py` and their route definitions.

## Root
- `GET /` — service summary
- `GET /health` — basic health

## Health — `/api/v1/health`
- `GET /api/v1/health` — basic health
- `GET /api/v1/health/detailed` — DB + system metrics
- `GET /api/v1/health/database` — DB size/tables/record counts
- `GET /api/v1/health/scrapers` — scraper health summary
- `GET /api/v1/health/system` — CPU/memory/disk/network
- `GET /api/v1/health/api` — API meta
- `GET /api/v1/health/comprehensive` — composite
- `GET /api/v1/health/metrics` — metrics bundle

## Auth — `/api/v1/auth`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/refresh`
- `GET  /api/v1/auth/me`
- `PUT  /api/v1/auth/me`
- `POST /api/v1/auth/change-password`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/forgot-password`
- `GET  /api/v1/auth/users` (admin)
- `GET  /api/v1/auth/permissions`

## Policies — `/api/v1/policies`
- `GET  /api/v1/policies` — list with filters/pagination
- `GET  /api/v1/policies/{policy_id}` — details
- `GET  /api/v1/policies/search/advanced`
- `GET  /api/v1/policies/search` — alias of advanced
- `GET  /api/v1/policies/categories`
- `GET  /api/v1/policies/jurisdictions`
- `GET  /api/v1/policies/stats`
- `GET  /api/v1/policies/{policy_id}/analysis`
- `POST /api/v1/policies` — create
- `PUT  /api/v1/policies/{policy_id}` — update
- `DELETE /api/v1/policies/{policy_id}` — delete

## Scrapers — `/api/v1/scrapers`
- `GET  /api/v1/scrapers` — inventory with status
- `GET  /api/v1/scrapers/categories`
- `POST /api/v1/scrapers/{scraper_id}/run` (admin)
- `GET  /api/v1/scrapers/{scraper_id}/status`
- `GET  /api/v1/scrapers/{scraper_id}/logs`
- `POST /api/v1/scrapers/run/category/{category}` (admin)
- `GET  /api/v1/scrapers/performance`
- `GET  /api/v1/scrapers/status` — aggregate status (monitoring)
- `GET  /api/v1/scrapers/health` — system health (monitoring)
- `GET  /api/v1/scrapers/stats` — data collection stats (monitoring)
- `POST /api/v1/scrapers/run` — manual run (monitoring)
- `GET  /api/v1/scrapers/logs` — recent logs (monitoring)
- `GET  /api/v1/scrapers/failures` — failure analysis (monitoring)
- `GET  /api/v1/scrapers/database/status` — DB status (monitoring)

## Data management — `/api/v1/data`
- `GET  /api/v1/data/tables`
- `GET  /api/v1/data/tables/{table_name}/records`
- `POST /api/v1/data/export`
- `GET  /api/v1/data/analysis/politicians`
- `GET  /api/v1/data/analysis/bills`
- `GET  /api/v1/data/analysis/hansards`
- `GET  /api/v1/data/search`
- `GET  /api/v1/data/database/size`

## Admin — `/api/v1/admin` (admin only)
- `GET  /api/v1/admin/dashboard`
- `GET  /api/v1/admin/system/status`
- `POST /api/v1/admin/system/restart`
- `GET  /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `GET  /api/v1/admin/logs`
- `POST /api/v1/admin/backup`
- `GET  /api/v1/admin/backups`
- `GET  /api/v1/admin/performance`
- `GET  /api/v1/admin/alerts`

## Dashboard — `/api/v1/dashboard`
- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/system`
- `GET /api/v1/dashboard/scrapers`
- `GET /api/v1/dashboard/database`
- `GET /api/v1/dashboard/alerts`
- `GET /api/v1/dashboard/recent-activity`
- `GET /api/v1/dashboard/performance`

## Legacy/Out of scope for unified API
- GraphQL and alternative REST in `backend/OpenPolicyAshBack` (not mounted)
- Django URLs under `scrapers/openparliament/parliament` (not mounted)

This document is the single source of truth for endpoint paths. If code changes, update this file and regenerate client integrations accordingly.