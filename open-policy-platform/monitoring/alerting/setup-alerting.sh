#!/bin/bash

# Alerting Setup Script
# Configures Prometheus alerts, Alertmanager, and notification channels

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check for required environment variables
    required_vars=("SLACK_WEBHOOK_URL" "PAGERDUTY_ROUTING_KEY")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            warn "$var is not set. Some notifications may not work."
        fi
    done
    
    # Check for kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is required but not installed"
        exit 1
    fi
    
    log "✅ Prerequisites checked"
}

# Create ConfigMaps
create_configmaps() {
    log "Creating ConfigMaps..."
    
    # Prometheus alerts ConfigMap
    kubectl create configmap prometheus-alerts \
        --from-file=prometheus-alerts.yaml \
        --namespace=monitoring \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Alertmanager config ConfigMap
    kubectl create configmap alertmanager-config \
        --from-file=alertmanager-config.yaml \
        --namespace=monitoring \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Templates ConfigMap
    kubectl create configmap alertmanager-templates \
        --from-file=templates/ \
        --namespace=monitoring \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log "✅ ConfigMaps created"
}

# Deploy Alertmanager
deploy_alertmanager() {
    log "Deploying Alertmanager..."
    
    cat > /tmp/alertmanager-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  namespace: monitoring
  labels:
    app: alertmanager
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:latest
        args:
          - '--config.file=/etc/alertmanager/alertmanager-config.yaml'
          - '--storage.path=/alertmanager'
          - '--cluster.advertise-address=0.0.0.0:9093'
          - '--web.external-url=https://alerts.openpolicy.com'
        ports:
        - name: web
          containerPort: 9093
        volumeMounts:
        - name: config
          mountPath: /etc/alertmanager
        - name: templates
          mountPath: /etc/alertmanager/templates
        - name: storage
          mountPath: /alertmanager
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
      volumes:
      - name: config
        configMap:
          name: alertmanager-config
      - name: templates
        configMap:
          name: alertmanager-templates
      - name: storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: alertmanager
  namespace: monitoring
spec:
  selector:
    app: alertmanager
  ports:
  - name: web
    port: 9093
    targetPort: 9093
  type: ClusterIP
EOF

    kubectl apply -f /tmp/alertmanager-deployment.yaml
    
    log "✅ Alertmanager deployed"
}

# Configure Prometheus to use alerts
configure_prometheus() {
    log "Configuring Prometheus..."
    
    # Update Prometheus configuration
    cat > /tmp/prometheus-patch.yaml << 'EOF'
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: 'openpolicy-prod'
        
    alerting:
      alertmanagers:
      - static_configs:
        - targets:
          - alertmanager:9093
          
    rule_files:
      - /etc/prometheus/alerts/*.yaml
      
    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
        - targets: ['localhost:9090']
        
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
        - role: pod
        relabel_configs:
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
          action: keep
          regex: true
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
          action: replace
          target_label: __metrics_path__
          regex: (.+)
        - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
          action: replace
          regex: ([^:]+)(?::\d+)?;(\d+)
          replacement: $1:$2
          target_label: __address__
EOF

    kubectl patch configmap prometheus-config \
        --namespace=monitoring \
        --patch "$(cat /tmp/prometheus-patch.yaml)"
    
    # Mount alerts in Prometheus
    kubectl patch deployment prometheus \
        --namespace=monitoring \
        --type='json' \
        -p='[
          {
            "op": "add",
            "path": "/spec/template/spec/volumes/-",
            "value": {
              "name": "alerts",
              "configMap": {
                "name": "prometheus-alerts"
              }
            }
          },
          {
            "op": "add",
            "path": "/spec/template/spec/containers/0/volumeMounts/-",
            "value": {
              "name": "alerts",
              "mountPath": "/etc/prometheus/alerts"
            }
          }
        ]'
    
    # Reload Prometheus
    kubectl rollout restart deployment/prometheus -n monitoring
    
    log "✅ Prometheus configured"
}

# Set up notification channels
setup_notification_channels() {
    log "Setting up notification channels..."
    
    # Create secrets for sensitive data
    kubectl create secret generic alerting-secrets \
        --from-literal=slack-webhook-url="${SLACK_WEBHOOK_URL}" \
        --from-literal=pagerduty-routing-key="${PAGERDUTY_ROUTING_KEY}" \
        --namespace=monitoring \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Patch Alertmanager to use secrets
    kubectl set env deployment/alertmanager \
        --namespace=monitoring \
        SLACK_WEBHOOK_URL=secretKeyRef:alerting-secrets:slack-webhook-url \
        PAGERDUTY_ROUTING_KEY=secretKeyRef:alerting-secrets:pagerduty-routing-key
    
    log "✅ Notification channels configured"
}

# Create runbooks
create_runbooks() {
    log "Creating runbooks..."
    
    mkdir -p runbooks
    
    # Service down runbook
    cat > runbooks/service-down.md << 'EOF'
# Service Down Runbook

## Alert: ServiceDown

### Impact
- Service is completely unavailable
- Users cannot access functionality
- Dependent services may fail

### Diagnosis Steps
1. Check service logs:
   ```bash
   kubectl logs -n default deployment/<service-name> --tail=100
   ```

2. Check pod status:
   ```bash
   kubectl get pods -n default -l app=<service-name>
   kubectl describe pod <pod-name>
   ```

3. Check recent deployments:
   ```bash
   kubectl rollout history deployment/<service-name>
   ```

4. Check resource usage:
   ```bash
   kubectl top pod -n default -l app=<service-name>
   ```

### Resolution Steps
1. **If pods are in CrashLoopBackOff:**
   - Check logs for startup errors
   - Verify environment variables
   - Check database connectivity

2. **If pods are OOMKilled:**
   - Increase memory limits
   - Check for memory leaks
   - Review recent code changes

3. **If deployment failed:**
   - Rollback to previous version:
     ```bash
     kubectl rollout undo deployment/<service-name>
     ```

4. **Emergency restart:**
   ```bash
   kubectl rollout restart deployment/<service-name>
   ```

### Escalation
- After 5 minutes: Page on-call engineer
- After 15 minutes: Page team lead
- After 30 minutes: Incident commander

### Post-Incident
1. Create incident report
2. Update runbook if needed
3. Add monitoring for root cause
EOF

    # High error rate runbook
    cat > runbooks/high-error-rate.md << 'EOF'
# High Error Rate Runbook

## Alert: HighErrorRate

### Impact
- Users experiencing failures
- Degraded service quality
- Potential data loss

### Diagnosis Steps
1. Check error logs:
   ```bash
   kubectl logs -n default deployment/<service-name> | grep ERROR
   ```

2. Check metrics:
   - Error rate by endpoint
   - Error types (4xx vs 5xx)
   - Correlation with deployments

3. Check dependencies:
   - Database connectivity
   - External API availability
   - Network issues

### Resolution Steps
1. **For 5xx errors:**
   - Check application logs
   - Verify database queries
   - Check memory/CPU usage

2. **For 4xx errors:**
   - Check for API changes
   - Verify authentication
   - Review request validation

3. **Quick mitigation:**
   - Enable circuit breakers
   - Increase timeouts
   - Scale up replicas

### Escalation
- Error rate > 10%: Page on-call
- Error rate > 25%: Incident commander
- Customer impact: Customer success team
EOF

    log "✅ Runbooks created"
}

# Test alerting
test_alerting() {
    log "Testing alerting setup..."
    
    # Send test alert via Alertmanager API
    curl -X POST http://alertmanager:9093/api/v1/alerts \
        -H "Content-Type: application/json" \
        -d '[{
            "labels": {
                "alertname": "TestAlert",
                "service": "test",
                "severity": "info"
            },
            "annotations": {
                "summary": "This is a test alert",
                "description": "Testing alerting pipeline"
            }
        }]'
    
    log "✅ Test alert sent"
}

# Generate alert documentation
generate_documentation() {
    log "Generating alert documentation..."
    
    cat > alerting-documentation.md << 'EOF'
# OpenPolicy Platform - Alerting Configuration

## Overview
The alerting system monitors platform health and notifies teams of issues.

## Alert Severity Levels

### Critical (P1)
- **Response Time**: Immediate
- **Notification**: PagerDuty + Slack
- **Examples**: Service down, data loss risk
- **On-Call**: Required response

### High (P2)
- **Response Time**: 30 minutes
- **Notification**: Slack ops channel
- **Examples**: High error rate, performance degradation
- **On-Call**: Best effort

### Medium (P3)
- **Response Time**: 2 hours
- **Notification**: Slack team channel
- **Examples**: Resource warnings, slow queries
- **On-Call**: Business hours

### Low (P4)
- **Response Time**: Next business day
- **Notification**: Email/ticket
- **Examples**: Capacity planning, trends
- **On-Call**: Not required

## Alert Categories

### Service Alerts
- ServiceDown
- HighErrorRate
- HighResponseTime

### Resource Alerts
- HighCPUUsage
- HighMemoryUsage
- DiskSpaceLow

### Database Alerts
- PostgreSQLConnectionPoolExhausted
- PostgreSQLSlowQueries
- RedisMemoryHigh
- ElasticsearchClusterRed

### Business KPI Alerts
- LowUserEngagement
- APIUsageDrop
- SearchLatencyHigh

### Security Alerts
- HighFailedLoginRate
- UnusualAPIActivity

### Kubernetes Alerts
- PodCrashLooping
- DeploymentReplicaMismatch
- PersistentVolumeNearFull

## Notification Channels

### Slack
- **#critical-alerts**: P1 alerts
- **#ops-alerts**: P2 alerts
- **#database-alerts**: Database issues
- **#business-metrics**: KPI alerts
- **#alerts**: All other alerts

### PagerDuty
- Critical alerts only
- Escalation policy:
  1. Primary on-call (immediately)
  2. Secondary on-call (5 minutes)
  3. Team lead (15 minutes)
  4. Engineering manager (30 minutes)

### Email
- Database team for DB alerts
- Business team for KPI alerts
- Daily summary for all teams

## Alert Response Process

1. **Acknowledge**: Respond in channel/PagerDuty
2. **Assess**: Check runbook and impact
3. **Communicate**: Update status channel
4. **Resolve**: Fix issue using runbook
5. **Document**: Create incident report

## Maintenance

### Silence Alerts
```bash
# Silence specific alert
amtool silence add alertname="ServiceDown" service="test-service" --duration="2h"

# List silences
amtool silence query

# Expire silence
amtool silence expire <silence-id>
```

### Update Alert Rules
1. Edit prometheus-alerts.yaml
2. Apply changes: `kubectl apply -f prometheus-alerts.yaml`
3. Verify in Prometheus UI

### Test Alerts
```bash
# Send test alert
./test-alert.sh <alertname> <severity>

# Check delivery
- Verify Slack message
- Check PagerDuty incident
- Confirm email receipt
```

## Troubleshooting

### Alert Not Firing
1. Check Prometheus targets
2. Verify alert expression
3. Check evaluation time
4. Review inhibition rules

### Alert Not Delivered
1. Check Alertmanager logs
2. Verify webhook URLs
3. Test notification channel
4. Check network connectivity

### Too Many Alerts
1. Review alert thresholds
2. Add inhibition rules
3. Group related alerts
4. Implement silence windows

## Best Practices

1. **Alert Fatigue Prevention**
   - Set appropriate thresholds
   - Use alert grouping
   - Implement smart routing
   - Regular threshold review

2. **Runbook Quality**
   - Clear diagnosis steps
   - Specific resolution actions
   - Include relevant commands
   - Update after incidents

3. **On-Call Health**
   - Limit P1 alerts
   - Ensure even distribution
   - Provide clear escalation
   - Regular rotation review

4. **Continuous Improvement**
   - Monthly alert review
   - Quarterly threshold tuning
   - Post-incident updates
   - Team feedback sessions
EOF

    log "✅ Documentation generated: alerting-documentation.md"
}

# Main execution
main() {
    log "Starting alerting setup..."
    
    check_prerequisites
    create_configmaps
    deploy_alertmanager
    configure_prometheus
    setup_notification_channels
    create_runbooks
    test_alerting
    generate_documentation
    
    log "✅ Alerting setup complete!"
    log ""
    log "Next steps:"
    log "1. Verify test alert in Slack/PagerDuty"
    log "2. Review alerting-documentation.md"
    log "3. Configure team schedules in PagerDuty"
    log "4. Train team on runbooks"
    log ""
    log "Alertmanager UI: http://localhost:9093"
    log "Prometheus Alerts: http://localhost:9090/alerts"
}

# Run main function
main "$@"