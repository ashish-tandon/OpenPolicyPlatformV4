# API Quick Reference

## Auth
- Login: `POST /api/v1/auth/login` (form: `username`, `password`)
- Header: `Authorization: Bearer <access_token>`

## Health
- `GET /health`
- `GET /api/v1/health`

## Policies
- List: `GET /api/v1/policies?search=...&category=...&page=1&limit=10`
- Details: `GET /api/v1/policies/{id}`
- Create: `POST /api/v1/policies`

## Scrapers
- Inventory: `GET /api/v1/scrapers`
- Run one: `POST /api/v1/scrapers/{id}/run`
- Status: `GET /api/v1/scrapers/{id}/status`

## Data
- Tables: `GET /api/v1/data/tables`
- Records: `GET /api/v1/data/tables/{table}?limit=100`

## Admin (admin)
- Dashboard: `GET /api/v1/admin/dashboard`
- Logs: `GET /api/v1/admin/logs?log_type=all&limit=100`

Base URL: http://localhost:8000
Docs: http://localhost:8000/docs