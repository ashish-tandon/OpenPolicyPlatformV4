# Checklists

## Pre-commit
- [ ] Code formatted/linted
- [ ] Endpoint changes reflected in `docs/api/endpoints.md`
- [ ] Payload changes in `docs/api/schemas.md`
- [ ] Config changes in `docs/api/overview.md` and `docs/operations/environment-variables.md`

## Pre-PR
- [ ] `scripts/check-docs-links.sh` passes
- [ ] `scripts/export-openapi.sh` runs without error
- [ ] Local `/.env` does not include production secrets

## Pre-deploy
- [ ] `DATABASE_URL`, `SECRET_KEY` set
- [ ] `ALLOWED_ORIGINS`, `ALLOWED_HOSTS` set (no wildcard, no localhost)
- [ ] `VITE_API_URL` points to API base URL
- [ ] Health endpoints healthy
- [ ] Backups confirmed