#!/bin/bash

# Open Policy Platform V4 - Monitoring Stack Startup Script
# Comprehensive monitoring, alerting, and observability

set -e

echo "🔍 Starting Open Policy Platform V4 Monitoring Stack..."
echo "=================================================="

# Check if core platform is running
echo "📋 Checking core platform status..."
if ! docker-compose -f docker-compose.core.yml ps | grep -q "Up"; then
    echo "❌ Core platform is not running. Please start it first with:"
    echo "   docker-compose -f docker-compose.core.yml up -d"
    exit 1
fi

echo "✅ Core platform is running"

# Create monitoring directories if they don't exist
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/alertmanager

# Start monitoring stack
echo "🚀 Starting monitoring services..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to start
echo "⏳ Waiting for monitoring services to start..."
sleep 30

# Check service status
echo "📊 Checking monitoring service status..."
docker-compose -f docker-compose.monitoring.yml ps

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
for i in {1..12}; do
    echo "   Attempt $i/12..."
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "healthy"; then
        echo "✅ Some services are healthy"
        break
    fi
    sleep 10
done

# Display access information
echo ""
echo "🎉 Monitoring Stack Started Successfully!"
echo "=========================================="
echo ""
echo "📊 Access Points:"
echo "   • Prometheus:     http://localhost:9090"
echo "   • Grafana:        http://localhost:3001 (admin/OpenPolicySecure2024!)"
echo "   • AlertManager:   http://localhost:9093"
echo "   • Node Exporter:  http://localhost:9100"
echo "   • cAdvisor:       http://localhost:8080"
echo ""
echo "🔧 Configuration:"
echo "   • Prometheus Config: ./monitoring/prometheus/prometheus.yml"
echo "   • Alert Rules:       ./monitoring/prometheus/rules/alerts.yml"
echo "   • AlertManager:      ./monitoring/alertmanager/alertmanager.yml"
echo "   • Grafana Dashboards: ./monitoring/grafana/dashboards/"
echo ""
echo "📈 Next Steps:"
echo "   1. Open Grafana at http://localhost:3001"
echo "   2. Login with admin/OpenPolicySecure2024!"
echo "   3. Verify Prometheus datasource is working"
echo "   4. Check system overview dashboard"
echo "   5. Configure additional alerts as needed"
echo ""
echo "🛑 To stop monitoring: docker-compose -f docker-compose.monitoring.yml down"
echo "🔄 To restart: docker-compose -f docker-compose.monitoring.yml restart"
echo ""
echo "✅ Monitoring stack startup complete!"
