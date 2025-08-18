# Environment Configuration

## Files
- `.env` — base variables
- Production overrides via orchestrator/secrets manager

## Required variables
- `DATABASE_URL`, `SECRET_KEY`, `API_HOST`, `API_PORT`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`

## Frontend
- `VITE_API_URL` must point to API base URL

## Validation
- `GET /api/v1/health` and `/api/v1/health/detailed`