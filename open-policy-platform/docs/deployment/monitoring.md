# Monitoring

## Probes
- Liveness: `GET /api/v1/health`
- Readiness: `GET /api/v1/health/detailed`

## Metrics
- Use `/api/v1/health/metrics` for ad-hoc pull

## Alerts
- CPU/memory/disk thresholds as per code; integrate with your monitoring stack

## Logs
- Aggregate backend logs and `*.log` files in repo root (backup/export runs)