# Variable and Configuration Flow

## Definition
- Define in `.env` based on `env.example`
- Backend reads via `pydantic_settings` in `backend/api/config.py`
- Frontend reads `VITE_*` at build/runtime

## Propagation
- `.env` → backend (`Settings.*`) → middleware/routers
- `.env` → frontend (`VITE_API_URL`) → API client base URL
- `.env` → scripts (exported in shell) → deployment behavior

## Critical variables
- Secrets: `SECRET_KEY`, `OPENAI_API_KEY`
- Networking: `API_HOST`, `API_PORT`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`
- Database: `DATABASE_URL`
- Performance: rate limits, cache TTL (tunable via env in future)

## Constraints
- No secrets committed
- Production must override `DEBUG=False`, tighten CORS/hosts

## Validation
- On start, log current environment (non-secret) and fail fast if required vars missing
- Add CI check for `.env` completeness in non-prod