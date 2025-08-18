# Architecture Decision Records (ADRs)

Status: Living document

## ADR-0001: Single-source API under backend/api
- Decision: Use FastAPI (`backend/api`) as the canonical REST API; legacy backends archived
- Consequences: All docs and clients reference `/api/v1/*`

## ADR-0002: Documentation consolidation
- Decision: `docs/` is the single documentation source; duplicates archived under `docs/archive/`
- Consequences: CI link checker enforces integrity

## ADR-0003: Production startup guard
- Decision: Block startup if required envs missing or ALLOWED_HOSTS/ALLOWED_ORIGINS unsafe
- Consequences: Fail-fast in production

## ADR-0004: Scraper artifacts via configurable directories
- Decision: Use `settings.scraper_reports_dir` and `settings.scraper_logs_dir` for reading reports/logs
- Consequences: Cleaner containerization