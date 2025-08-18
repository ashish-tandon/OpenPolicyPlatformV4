# Runbooks

## Local Development
1. `cp env.example .env` and update minimal variables
2. `./scripts/setup-unified.sh`
3. `./scripts/start-all.sh`
4. Verify: http://localhost:8000/docs and http://localhost:5173

## Staging
1. Provision PostgreSQL and set `DATABASE_URL`
2. Set `SECRET_KEY`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS` (non-wildcard)
3. Start API (uvicorn/systemd/container)
4. Build/serve frontend with `VITE_API_URL`
5. Verify health and dashboards

## Production
- Follow `docs/deployment/production-runbook.md`

## Incident Response
- Check `/api/v1/health/detailed` and `/api/v1/health/comprehensive`
- Fetch logs via `/api/v1/admin/logs` and `/api/v1/scrapers/logs`
- If DB down: restore connectivity; API will reflect status automatically
- Security/CORS issues: check `ALLOWED_ORIGINS` and `ALLOWED_HOSTS`