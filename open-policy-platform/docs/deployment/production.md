# Production Deployment

See the step-by-step runbook: `production-runbook.md`

Summary:
- Prepare `.env` with prod values
- Start/PostgreSQL ready
- Run backend with uvicorn/systemd/container
- Build/serve frontend with correct `VITE_API_URL`
- Configure monitoring with health endpoints