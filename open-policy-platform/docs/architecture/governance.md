# Documentation Governance

## Rules
- Any API change must update `docs/api/endpoints.md` and relevant examples in `docs/api/schemas.md`
- Any configuration/networking change must update `docs/api/overview.md` and `docs/operations/environment-variables.md`
- Add or modify scripts? Update `docs/operations/scripts.md`
- Health behavior changes? Update `docs/operations/health-checks.md`

## Process
- PR must pass `scripts/check-docs-links.sh`
- PR must export OpenAPI via `scripts/export-openapi.sh` and attach artifact (handled by CI)
- Reviewer verifies endpoints vs code (`backend/api/*`)

## Versioning
- Bump version in `backend/api/config.py` and reflect in docs front matter where shown

## Archival
- Legacy or superseded docs moved to `docs/archive/` with note