# Service Dependencies and Requirements

## Backend API (FastAPI)
- Language: Python 3.8+
- Dependencies: `requirements.txt` (+ `backend/requirements.txt` if present)
- Services: PostgreSQL (required), Redis (optional)
- Env: see `docs/operations/environment-variables.md`
- Ports: 8000
- Start: `uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`

## Frontend (React + Vite)
- Node.js: v18+
- Dependencies: `web/package.json`
- Env: `VITE_API_URL` → backend base URL
- Port: 5173 (dev)
- Start (dev): `npm run dev` in `web/`
- Build: `npm run build` in `web/`

## Database (PostgreSQL)
- Version: 14+
- Connectivity: `DATABASE_URL`
- Users/Roles: provide app role with read/write as needed
- Indexing: consider indexes on hot fields (title, classification, created_at)

## Scrapers
- Language: Python (various), per subproject requirements
- Outputs: `scraper_test_report_*.json`, `collection_report_*.json`, `*.log`
- Integration: API reads reports/logs; DB writes are out-of-scope for API layer

## Infrastructure
- Optional Docker (compose) for api + db + nginx (see `docs/deployment/docker.md`)
- Monitoring via health endpoints (see `docs/operations/health-checks.md`)

## Security
- JWT secret from `SECRET_KEY`
- CORS/hosts per environment
- Rate limiting via middleware settings

## CI/CD
- GitHub Actions workflow: `.github/workflows/docs-openapi.yml`
  - Runs docs link checker and OpenAPI export
  - Publishes `dist/openapi.json` artifact