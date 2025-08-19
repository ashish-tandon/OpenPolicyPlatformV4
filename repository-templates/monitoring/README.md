# 📊 OpenPolicyPlatform Monitoring

Monitoring, logging, and observability for OpenPolicyPlatform V5.

## Services
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Elasticsearch**: Log storage and search
- **Logstash**: Log processing pipeline
- **Fluentd**: Log aggregation

## Quick Start
```bash
# Start monitoring stack
docker-compose up -d

# Access Grafana
open http://localhost:3001
# Default: admin/admin

# Access Prometheus
open http://localhost:9090
```

## Dashboards
- Platform Overview
- Service Health
- Performance Metrics
- Error Tracking
