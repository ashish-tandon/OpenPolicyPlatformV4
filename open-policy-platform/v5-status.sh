#!/bin/bash

# Check OpenPolicyPlatform V5 status

echo "🔍 OpenPolicyPlatform V5 Status Check"
echo "======================================"

# Check if services are running
echo "📊 Service Status:"
docker-compose -f docker-compose.v5.yml ps

echo ""
echo "🌐 Service Health:"
echo "------------------"

# Check gateway
if curl -s http://localhost/health > /dev/null; then
    echo "✅ Gateway: Healthy"
else
    echo "❌ Gateway: Unhealthy"
fi

# Check API
if curl -s http://localhost:9000/health > /dev/null; then
    echo "✅ API Gateway: Healthy"
else
    echo "❌ API Gateway: Unhealthy"
fi

# Check web frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Web Frontend: Healthy"
else
    echo "❌ Web Frontend: Unhealthy"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus: Healthy"
else
    echo "❌ Prometheus: Unhealthy"
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana: Healthy"
else
    echo "❌ Grafana: Unhealthy"
fi

echo ""
echo "📈 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
