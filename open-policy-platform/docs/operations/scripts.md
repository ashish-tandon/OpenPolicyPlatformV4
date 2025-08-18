# Scripts Inventory and Usage

This inventory lists available scripts, their purpose, how to run them, inputs, and status.

## Setup
- `scripts/setup-unified.sh`
  - Purpose: One-shot setup for backend, web, env, and DB prerequisites
  - Usage: `./scripts/setup-unified.sh`
  - Inputs: `.env`, system dependencies; may prompt/assume defaults
  - Output: Installed deps, configured env
  - Status: Active

- `scripts/setup.sh`
  - Purpose: Legacy setup flow (pre-unification)
  - Usage: `./scripts/setup.sh`
  - Status: Legacy (prefer `setup-unified.sh`)

## Start/Stop
- `scripts/start-all.sh`
  - Purpose: Start backend (uvicorn) and web (Vite) for local dev
  - Usage: `./scripts/start-all.sh`
  - Inputs: `.env` (API_HOST/PORT, VITE_*), open ports 8000/5173
  - Status: Active

- `scripts/start-backend.sh`
  - Purpose: Start FastAPI backend only
  - Usage: `./scripts/start-backend.sh`
  - Status: Active

- `scripts/start-web.sh`
  - Purpose: Start React web only
  - Usage: `./scripts/start-web.sh`
  - Status: Active

- `scripts/start-mobile.sh`
  - Purpose: Start mobile app (future)
  - Usage: `./scripts/start-mobile.sh`
  - Status: Planned/Future

## Verification & Testing
- `scripts/verify-merge.sh`
  - Purpose: Validate post-merge structure/integrity
  - Usage: `./scripts/verify-merge.sh`
  - Status: Active (use for repo hygiene)

- `scripts/run-tests.sh`
  - Purpose: Run test suites and produce reports
  - Usage: `./scripts/run-tests.sh`
  - Outputs: Test logs/reports
  - Status: Active

## Deployment
- `scripts/deploy-with-migration.sh`
  - Purpose: Deploy application with database migrations
  - Usage: `./scripts/deploy-with-migration.sh`
  - Inputs: Environment (production), DB credentials
  - Status: Active (review before prod use)

## Utilities
- `scripts/people.py`
  - Purpose: Utility script (developer tool)
  - Usage: `python scripts/people.py`
  - Status: Needs review; if unused, move to `docs/archive/`

---
Notes:
- Always run scripts from repository root
- Review `.env` before running deployment scripts
- Prefer unified setup and start scripts for local development