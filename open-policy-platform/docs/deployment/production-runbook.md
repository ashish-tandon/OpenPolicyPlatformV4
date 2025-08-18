# Production Deployment Runbook

## Prereqs
- PostgreSQL reachable with provisioned DB/user
- Host/container runtime with ports open
- `.env` populated (see `docs/operations/environment-variables.md`)

## Order of operations
1. Prepare environment
   - Copy `.env`; set `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, `LOG_LEVEL=INFO`
2. Database
   - Ensure DB up and reachable
   - Run migrations/imports as needed
3. Backend API
   - Start FastAPI:
     - With systemd or container: `uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 2`
   - Health check: `GET /api/v1/health` and `/api/v1/health/detailed`
4. Frontend
   - Build and serve (Vite build → served via nginx or static host)
   - Set `VITE_API_URL` to API base
5. Monitoring & logs
   - Point probes to `/api/v1/health` (liveness) and `/api/v1/health/detailed` (readiness)
   - Aggregate logs as per infra

## Scripts
- Setup (once): `./scripts/setup-unified.sh`
- Start (dev): `./scripts/start-all.sh`
- Deploy with DB migration: `./scripts/deploy-with-migration.sh` (review and adapt for prod)

## Configuration
- See `docs/operations/environment-variables.md`
- Security hardening:
  - Strong `SECRET_KEY`
  - Restrict `ALLOWED_ORIGINS`/`ALLOWED_HOSTS`
  - Enforce HTTPS at edge (nginx/ALB)

## Rollback
- Keep previous image/build
- DB backups before migration

## Validation checklist
- [ ] Health endpoints healthy
- [ ] Critical pages load (policies, dashboard)
- [ ] Admin endpoints gated
- [ ] Logs/alerts monitored