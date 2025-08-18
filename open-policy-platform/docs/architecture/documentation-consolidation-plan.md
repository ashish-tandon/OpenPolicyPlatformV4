# Documentation Consolidation Plan

## Goals
- Single source of truth for APIs, networking, services, and I/O
- Remove/flag duplicate or misleading docs
- Align docs with current code mounted in `backend/api`

## Canonical sources
- API endpoints: `docs/api/endpoints.md`
- API overview and networking: `docs/api/overview.md`
- Auth flows: `docs/api/authentication.md`
- Quick reference: `docs/api/quick-reference.md`
- Runtime configuration: `backend/api/config.py` (+ `.env` via `env.example`)

## Deprecated/legacy docs (retain for history, not authoritative)
- `backend/COMPREHENSIVE_TESTING_AND_API_SUMMARY.md` — contains endpoints not mounted in current service (GraphQL/parliamentary). Keep as archive reference.
- `backend/OpenPolicyAshBack/**` docs — legacy alternative backend; not part of unified API unless re-integrated.
- `scrapers/openparliament/parliament/**` Django URLs — legacy endpoints not mounted; scrapers remain as data sources.

## Gaps to fill (before code changes)
- Create DB schema reference for tables touched by API: `core_politician`, `bills_bill`, `hansards_statement`, etc. Suggested: `docs/database/schema.md`
- Define request/response schemas for key endpoints using Pydantic models or JSON examples per route in `docs/api/endpoints.md`
- Add environment/ops docs: `docs/deployment/environment.md`, `docs/deployment/monitoring.md` (if missing)

## Consistency rules
- Any new API route must be added to `docs/api/endpoints.md`
- Networking defaults must reflect `backend/api/config.py` (host, port, CORS)
- Test/dev servers (`test_server.py`, `simple_api_server.py`) are not part of prod docs
- Legacy subsystems must be clearly prefixed as legacy and out-of-scope

## Proposed file moves (optional)
- Move top-level “COMPREHENSIVE_*.md” status reports into `docs/archive/` to reduce clutter

## Review checklist
- [ ] `docs/README.md` links resolve to real files (now added)
- [ ] API endpoints list matches routers in `backend/api`
- [ ] Auth doc matches `backend/api/routers/auth.py`
- [ ] Networking settings documented from `backend/api/config.py`
- [ ] Quick reference present for day-to-day usage

## Next steps (then code changes)
1. Approve this plan and the new canonical docs
2. Migrate/archive legacy docs to `docs/archive/` (non-functional change)
3. Optionally, add OpenAPI export and publish step to CI (generate clients)
4. Then refactor code to align with docs where gaps exist (e.g., formal response models)