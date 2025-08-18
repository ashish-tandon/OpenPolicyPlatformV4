# Service Level Objectives (SLOs)

## Availability
- Health endpoints: 99.9% monthly
- Core API (`/api/v1/policies`, `/api/v1/data/*`): 99.5% monthly

## Latency (P95)
- `/api/v1/policies` list/search: < 500ms
- Health basic: < 100ms

## Error budget
- 0.1% for health, 0.5% for core APIs per month

## Monitoring
- Use `/api/v1/health/*` and logs; integrate into monitoring stack