#!/bin/bash

# Grafana Dashboard Setup Script
# Imports all custom dashboards and configures monitoring

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Configuration
GRAFANA_URL=${GRAFANA_URL:-"http://localhost:3000"}
GRAFANA_USER=${GRAFANA_USER:-"admin"}
GRAFANA_PASS=${GRAFANA_PASS:-"prom-operator"}
DASHBOARD_DIR="grafana-dashboards"

# Wait for Grafana to be ready
wait_for_grafana() {
    log "Waiting for Grafana to be ready..."
    
    for i in {1..30}; do
        if curl -s "$GRAFANA_URL/api/health" | grep -q "ok"; then
            log "✅ Grafana is ready"
            return 0
        fi
        sleep 2
    done
    
    error "Grafana is not responding after 60 seconds"
    return 1
}

# Create datasources
create_datasources() {
    log "Creating datasources..."
    
    # Prometheus datasource
    cat > /tmp/prometheus-datasource.json << EOF
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true,
  "jsonData": {
    "httpMethod": "POST",
    "timeInterval": "10s"
  }
}
EOF

    # Elasticsearch datasource for logs
    cat > /tmp/elasticsearch-datasource.json << EOF
{
  "name": "Elasticsearch",
  "type": "elasticsearch",
  "url": "http://elasticsearch:9200",
  "access": "proxy",
  "jsonData": {
    "esVersion": "7.10+",
    "timeField": "@timestamp",
    "logMessageField": "message",
    "logLevelField": "level"
  }
}
EOF

    # PostgreSQL datasource for business metrics
    cat > /tmp/postgres-datasource.json << EOF
{
  "name": "PostgreSQL",
  "type": "postgres",
  "url": "postgres:5432",
  "access": "proxy",
  "jsonData": {
    "sslmode": "disable",
    "postgresVersion": 1300,
    "timescaledb": false
  },
  "secureJsonData": {
    "password": "${POSTGRES_PASSWORD:-postgres}"
  },
  "user": "postgres",
  "database": "openpolicy_prod"
}
EOF

    # Create datasources via API
    for datasource in prometheus elasticsearch postgres; do
        log "Creating $datasource datasource..."
        
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "$GRAFANA_USER:$GRAFANA_PASS" \
            -d @/tmp/${datasource}-datasource.json \
            "$GRAFANA_URL/api/datasources" || true
    done
    
    log "✅ Datasources created"
}

# Import dashboards
import_dashboards() {
    log "Importing dashboards..."
    
    # Dashboard files
    DASHBOARDS=(
        "platform-overview-dashboard.json"
        "service-performance-dashboard.json"
        "business-kpi-dashboard.json"
        "database-monitoring-dashboard.json"
    )
    
    for dashboard_file in "${DASHBOARDS[@]}"; do
        if [ -f "$DASHBOARD_DIR/$dashboard_file" ]; then
            log "Importing $dashboard_file..."
            
            # Read dashboard JSON
            dashboard_json=$(cat "$DASHBOARD_DIR/$dashboard_file")
            
            # Create import payload
            cat > /tmp/import-payload.json << EOF
{
  "dashboard": $dashboard_json,
  "overwrite": true,
  "inputs": [
    {
      "name": "DS_PROMETHEUS",
      "type": "datasource",
      "pluginId": "prometheus",
      "value": "Prometheus"
    },
    {
      "name": "DS_ELASTICSEARCH",
      "type": "datasource",
      "pluginId": "elasticsearch",
      "value": "Elasticsearch"
    }
  ]
}
EOF
            
            # Import dashboard
            curl -s -X POST \
                -H "Content-Type: application/json" \
                -u "$GRAFANA_USER:$GRAFANA_PASS" \
                -d @/tmp/import-payload.json \
                "$GRAFANA_URL/api/dashboards/import"
            
            log "✅ Imported $dashboard_file"
        else
            info "Dashboard file not found: $dashboard_file"
        fi
    done
}

# Create dashboard folders
create_folders() {
    log "Creating dashboard folders..."
    
    folders=("Platform Overview" "Service Monitoring" "Business Analytics" "Infrastructure")
    
    for folder in "${folders[@]}"; do
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "$GRAFANA_USER:$GRAFANA_PASS" \
            -d "{\"title\": \"$folder\"}" \
            "$GRAFANA_URL/api/folders" || true
    done
    
    log "✅ Folders created"
}

# Configure alerts
configure_alerts() {
    log "Configuring alerts..."
    
    # Create notification channels
    cat > /tmp/slack-channel.json << EOF
{
  "name": "Slack Alerts",
  "type": "slack",
  "settings": {
    "url": "${SLACK_WEBHOOK_URL:-https://hooks.slack.com/services/YOUR/WEBHOOK/URL}",
    "username": "Grafana"
  },
  "isDefault": true
}
EOF

    cat > /tmp/email-channel.json << EOF
{
  "name": "Email Alerts",
  "type": "email",
  "settings": {
    "addresses": "alerts@openpolicy.com"
  },
  "isDefault": false
}
EOF

    # Create channels
    for channel in slack email; do
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "$GRAFANA_USER:$GRAFANA_PASS" \
            -d @/tmp/${channel}-channel.json \
            "$GRAFANA_URL/api/alert-notifications" || true
    done
    
    log "✅ Alert channels configured"
}

# Set up dashboard provisioning
setup_provisioning() {
    log "Setting up dashboard provisioning..."
    
    # Create provisioning configuration
    cat > /tmp/dashboard-provisioning.yaml << 'EOF'
apiVersion: 1

providers:
  - name: 'OpenPolicy Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    # Copy to Grafana provisioning directory
    if [ -d "/etc/grafana/provisioning/dashboards" ]; then
        cp /tmp/dashboard-provisioning.yaml /etc/grafana/provisioning/dashboards/
        log "✅ Dashboard provisioning configured"
    else
        info "Grafana provisioning directory not found"
    fi
}

# Create custom panels
create_custom_panels() {
    log "Creating custom panels..."
    
    # Platform health panel
    cat > /tmp/platform-health-panel.json << 'EOF'
{
  "dashboard": {
    "title": "Platform Health Score",
    "panels": [
      {
        "datasource": "Prometheus",
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "mappings": [],
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "color": "red",
                  "value": null
                },
                {
                  "color": "yellow",
                  "value": 80
                },
                {
                  "color": "green",
                  "value": 95
                }
              ]
            },
            "unit": "percent"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        },
        "id": 100,
        "options": {
          "orientation": "auto",
          "reduceOptions": {
            "values": false,
            "calcs": ["lastNotNull"],
            "fields": ""
          },
          "showThresholdLabels": false,
          "showThresholdMarkers": true,
          "text": {
            "titleSize": 30,
            "valueSize": 50
          }
        },
        "pluginVersion": "8.0.0",
        "targets": [
          {
            "expr": "(sum(up{job=~\".*-service\"}) / count(up{job=~\".*-service\"})) * 100",
            "refId": "A"
          }
        ],
        "title": "Overall Platform Health",
        "type": "gauge"
      }
    ],
    "schemaVersion": 30,
    "tags": ["health"],
    "timezone": "browser",
    "title": "Platform Health Score",
    "uid": "platform-health",
    "version": 0
  }
}
EOF

    # Import custom panel
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d @/tmp/platform-health-panel.json \
        "$GRAFANA_URL/api/dashboards/db"
    
    log "✅ Custom panels created"
}

# Configure home dashboard
configure_home_dashboard() {
    log "Configuring home dashboard..."
    
    # Set platform overview as home
    curl -s -X PUT \
        -H "Content-Type: application/json" \
        -u "$GRAFANA_USER:$GRAFANA_PASS" \
        -d '{"homeDashboardId": 1}' \
        "$GRAFANA_URL/api/org/preferences"
    
    log "✅ Home dashboard configured"
}

# Generate dashboard documentation
generate_documentation() {
    log "Generating dashboard documentation..."
    
    cat > dashboard-documentation.md << 'EOF'
# OpenPolicy Platform - Grafana Dashboards

## Available Dashboards

### 1. Platform Overview Dashboard
- **Purpose**: High-level view of entire platform health
- **Key Metrics**: Service status, CPU/Memory usage, Request rates, Error rates
- **Use Case**: Operations team monitoring, incident response
- **Refresh Rate**: 10 seconds

### 2. Service Performance Dashboard
- **Purpose**: Detailed performance metrics per service
- **Key Metrics**: Response times, Request distribution, Resource usage
- **Use Case**: Performance optimization, capacity planning
- **Variables**: Service selector
- **Refresh Rate**: 10 seconds

### 3. Business KPIs Dashboard
- **Purpose**: Business metrics and user analytics
- **Key Metrics**: User registrations, Active users, API usage, Search trends
- **Use Case**: Business reporting, growth tracking
- **Refresh Rate**: 30 seconds

### 4. Database Monitoring Dashboard
- **Purpose**: Database health and performance
- **Key Metrics**: Connections, Query performance, Cache hit rates
- **Databases**: PostgreSQL, Redis, Elasticsearch
- **Variables**: Database selector
- **Refresh Rate**: 30 seconds

## Dashboard Features

### Templating Variables
- **Service**: Select specific service for detailed view
- **Database**: Choose database instance
- **Time Range**: Flexible time selection

### Annotations
- Deployment markers
- Incident markers
- Maintenance windows

### Alerting Rules
1. **Service Down**: Any service unavailable > 2 minutes
2. **High Error Rate**: Error rate > 5% for 5 minutes
3. **High Response Time**: p95 latency > 1s for 10 minutes
4. **Database Connection Pool**: > 80% connections used
5. **Low Cache Hit Rate**: < 80% cache hits

## Best Practices

### Dashboard Usage
1. Start with Platform Overview for general health
2. Drill down to Service Performance for specifics
3. Check Business KPIs daily
4. Monitor Database dashboard during peak hours

### Alert Response
1. Check Platform Overview first
2. Identify affected service
3. Review service-specific metrics
4. Check database performance
5. Review recent deployments

### Performance Optimization
1. Monitor query latency trends
2. Track cache hit rates
3. Analyze request patterns
4. Review resource utilization

## Customization

### Adding Panels
1. Edit dashboard
2. Add panel
3. Configure query
4. Set visualization
5. Save dashboard

### Creating Alerts
1. Edit panel
2. Alert tab
3. Create alert rule
4. Set conditions
5. Configure notifications

## Access Control

### Viewer Role
- View all dashboards
- Cannot edit

### Editor Role
- View and edit dashboards
- Create new dashboards

### Admin Role
- Full dashboard access
- Manage permissions
- Configure datasources

## Troubleshooting

### No Data
- Check datasource connection
- Verify Prometheus targets
- Check time range

### Slow Loading
- Reduce time range
- Optimize queries
- Check Grafana resources

### Missing Metrics
- Verify exporters running
- Check scrape configuration
- Review metric names
EOF

    log "✅ Documentation generated: dashboard-documentation.md"
}

# Main execution
main() {
    log "Starting Grafana dashboard setup..."
    
    # Wait for services
    wait_for_grafana
    
    # Setup components
    create_datasources
    create_folders
    import_dashboards
    configure_alerts
    setup_provisioning
    create_custom_panels
    configure_home_dashboard
    generate_documentation
    
    # Summary
    log "✅ Grafana dashboard setup complete!"
    log ""
    log "Access Grafana at: $GRAFANA_URL"
    log "Username: $GRAFANA_USER"
    log "Password: $GRAFANA_PASS"
    log ""
    log "Available dashboards:"
    log "  - Platform Overview"
    log "  - Service Performance"
    log "  - Business KPIs"
    log "  - Database Monitoring"
    log ""
    log "Documentation: dashboard-documentation.md"
}

# Run main function
main "$@"