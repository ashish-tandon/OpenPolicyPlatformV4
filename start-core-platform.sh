#!/bin/bash

# Open Policy Platform V4 - Core Platform Startup Script
# Deploys 5 stable, well-managed services with resource limits

set -e

echo "🚀 Starting Open Policy Platform V4 - Core Platform"
echo "=================================================="
echo "Services: 5 core services (Database, Cache, API, Web, Gateway)"
echo "Resource Limits: 1.2GB memory, 1.2 CPU cores total"
echo "Target: Stable, sustainable platform"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose -f docker-compose.core.yml down 2>/dev/null || true
docker container prune -f > /dev/null 2>&1 || true

# Start core services
echo "🚀 Starting core services..."
docker-compose -f docker-compose.core.yml up -d

echo ""
echo "⏳ Waiting for services to start and stabilize..."
sleep 45

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.core.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Checking service health..."

# Check database
if curl -s http://localhost:5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Running on port 5432"
else
    echo "❌ PostgreSQL: Not accessible"
fi

# Check Redis
if curl -s http://localhost:6379 > /dev/null 2>&1; then
    echo "✅ Redis: Running on port 6379"
else
    echo "❌ Redis: Not accessible"
fi

# Check API
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API: Running on port 8000"
else
    echo "❌ API: Not accessible"
fi

# Check Web
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Web: Running on port 3000"
else
    echo "❌ Web: Not accessible"
fi

# Check Gateway
if curl -s http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Gateway: Running on port 80"
else
    echo "❌ Gateway: Not accessible"
fi

echo ""
echo "📈 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep openpolicy-core

echo ""
echo "🎯 Core Platform Access Points:"
echo "   🌐 Main Application: http://localhost:80"
echo "   🔌 API Endpoints: http://localhost:8000"
echo "   📱 Web Frontend: http://localhost:3000"
echo "   🗄️  Database: localhost:5432"
echo "   🚀 Cache: localhost:6379"

echo ""
echo "📋 Health Check Commands:"
echo "   docker-compose -f docker-compose.core.yml ps"
echo "   docker stats --no-stream"
echo "   curl http://localhost:80/health"
echo "   curl http://localhost:8000/health"

echo ""
echo "🎉 Core Platform Started Successfully!"
echo "   This is a stable, sustainable foundation that can grow incrementally."
echo "   Next step: Add business services one by one as needed."
echo ""
echo "⚠️  Remember: 5 stable services > 37 overloaded services!"
