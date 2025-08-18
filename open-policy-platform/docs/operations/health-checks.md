# Health Checks and Diagnostics

Service: FastAPI backend (`backend/api`)

## Endpoints
- `GET /api/v1/health`
  - Returns basic status and uptime
- `GET /api/v1/health/detailed`
  - Adds DB connectivity and system metrics
- `GET /api/v1/health/database`
  - DB size, table count, key record counts
- `GET /api/v1/health/scrapers`
  - Scraper success rate, last run
- `GET /api/v1/health/system`
  - CPU, memory, disk, network counters, processes, load, uptime
- `GET /api/v1/health/api`
  - API version, environment, uptime
- `GET /api/v1/health/comprehensive`
  - Aggregates all of the above and summarizes status
- `GET /api/v1/health/metrics`
  - System, database, scraper, network metrics snapshot

## Parameters and interpretations
- Status levels: `healthy`, `warning`, `unhealthy`
- System thresholds (defaults from code):
  - Warning when CPU/memory/disk > 80%
  - Unhealthy when CPU/memory/disk > 90%
- Database health:
  - Connectivity via `SELECT 1` (success = healthy)
  - Size via `pg_database_size`
  - Table count from `information_schema.tables`
- Scraper health:
  - Derived from latest `scraper_test_report_*.json` or collection reports
  - Success rate thresholds as in code: <50 critical, <70 warning

## Usage
- For probes: use `GET /api/v1/health` for liveness, `GET /api/v1/health/detailed` for readiness
- For dashboards/alerts: consume `/api/v1/health/comprehensive` and `/api/v1/health/metrics`

Notes:
- In production, protect detailed endpoints if needed (auth, IP allow-list)
- Paths and behavior documented in `docs/api/endpoints.md`