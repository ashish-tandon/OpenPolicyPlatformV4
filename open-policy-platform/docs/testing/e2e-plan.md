# End-to-End Test Plan

## Scope
- Auth flows (login, refresh, me)
- Policies (list, details, search, stats)
- Scraper monitoring (status, stats, logs)
- Data (tables, records, export)
- Admin (dashboard, logs)

## Setup
- Start services locally with `.env` and sample data
- Ensure latest scraper report/log present (or mock)

## Tests
- Health liveness/readiness
- Auth: login -> authorized requests -> refresh
- Policies: list->detail->search->stats->analysis
- Scrapers: status->stats->logs
- Data: tables->records->search->export (mock)
- Admin: dashboard->logs

## Non-functional
- Check P95 latency for policies list (< 500ms)
- Validate proper security headers