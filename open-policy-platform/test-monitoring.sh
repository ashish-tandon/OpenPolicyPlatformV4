#!/bin/bash

echo "🔍 Testing Open Policy Platform Monitoring Stack..."
echo "================================================"

# Test Prometheus
echo "📊 Testing Prometheus..."
if curl -s http://localhost:9090/-/healthy | grep -q "Healthy"; then
    echo "✅ Prometheus: HEALTHY"
else
    echo "❌ Prometheus: UNHEALTHY"
fi

# Test Grafana
echo "📈 Testing Grafana..."
if curl -s http://localhost:3001/api/health | grep -q "ok"; then
    echo "✅ Grafana: HEALTHY"
else
    echo "❌ Grafana: UNHEALTHY"
fi

# Test AlertManager
echo "🔔 Testing AlertManager..."
if curl -s http://localhost:9093/api/v2/status | grep -q "ready"; then
    echo "✅ AlertManager: HEALTHY"
else
    echo "❌ AlertManager: UNHEALTHY"
fi

# Test Node Exporter
echo "🖥️ Testing Node Exporter..."
if curl -s http://localhost:9100/metrics | grep -q "go_gc_duration_seconds"; then
    echo "✅ Node Exporter: HEALTHY"
else
    echo "❌ Node Exporter: UNHEALTHY"
fi

# Test cAdvisor
echo "🐳 Testing cAdvisor..."
if curl -s http://localhost:8080/healthz | grep -q "ok"; then
    echo "✅ cAdvisor: HEALTHY"
else
    echo "❌ cAdvisor: UNHEALTHY"
fi

# Test API Metrics
echo "🔌 Testing API Metrics..."
if curl -s http://localhost:8000/metrics | grep -q "python_gc_objects_collected_total"; then
    echo "✅ API Metrics: HEALTHY"
else
    echo "❌ API Metrics: UNHEALTHY"
fi

echo ""
echo "🎉 Monitoring Stack Test Complete!"
