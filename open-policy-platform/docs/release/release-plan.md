# Release Plan

## Artifacts
- OpenAPI schema: `dist/openapi.json`
- Application images/bundles (if containerized)

## Branching
- main/master protected; release branches as needed

## Steps
1. Ensure docs and OpenAPI CI pass
2. Update version in `backend/api/config.py`
3. Tag release and publish artifacts
4. Deploy per `docs/deployment/production-runbook.md`

## Post-release
- Monitor health endpoints and logs
- Collect feedback and file issues