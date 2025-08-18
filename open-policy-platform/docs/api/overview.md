# Open Policy Platform API — Overview

## Base URLs
- Development: http://localhost:8000
- Documentation (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## Versioning
- REST base prefix: `/api/v1`
- App version: 1.0.0 (source of truth: `backend/api/config.py` → `Settings.version`)

## Services in scope (canonical)
- FastAPI service: `backend/api` (single source of truth for REST)
- Test/dev servers: `backend/test_server.py`, `backend/simple_api_server.py` (non-production)
- Legacy/experimental: `backend/OpenPolicyAshBack` (GraphQL + alternative REST) — not part of the unified service; treat as archive unless explicitly re-integrated
- Legacy Django endpoints: `scrapers/openparliament/parliament` — used by historical tools; not mounted in unified API

## Security
- Authentication: Bearer JWT (obtained via `POST /api/v1/auth/login`)
- Authorization: role-based (admin vs user), enforced in selected routes
- Headers set by security middleware (see `backend/api/middleware/security.py`):
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security: max-age=31536000; includeSubDomains
  - Content-Security-Policy, Referrer-Policy, Permissions-Policy

## Rate limiting and performance
- Global rate limiting and response caching via `PerformanceMiddleware` (TTL 300s default)
- Additional request validation and per-IP rate limits via `SecurityMiddleware` and `RateLimitMiddleware`

## CORS and networking
- Host/port: 0.0.0.0:8000 (source: `backend/api/config.py`)
- Allowed origins (development defaults):
  - http://localhost:3000, http://localhost:5173, http://127.0.0.1:3000, http://127.0.0.1:5173
- Allowed hosts: `*` (tighten in production)

## Environments
- `Settings.environment` controls docs availability (docs disabled in production)
- `.env` file supported (see `env.example`) for overriding defaults

## Data stores
- Primary database: PostgreSQL (URL in `Settings.database_url`)
- File exports/backups/logs: on application filesystem

## Canonical API namespaces (mounted)
- `/api/v1/health` — health and diagnostics
- `/api/v1/auth` — authentication and user info
- `/api/v1/policies` — policy CRUD, search, analytics
- `/api/v1/scrapers` — scraper inventory, runs, monitoring
- `/api/v1/data` — data management utilities
- `/api/v1/admin` — administrative operations
- `/api/v1/dashboard` — aggregate metrics

Note: Root convenience endpoints also exist: `GET /` and `GET /health`.