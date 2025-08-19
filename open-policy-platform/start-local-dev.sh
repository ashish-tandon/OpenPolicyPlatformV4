#!/bin/bash

# 🚀 Quick Start Local Development
# This script quickly starts the local development environment

echo "🚀 Starting Open Policy Platform V4 Local Development..."
echo "======================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Check if local compose file exists
if [ ! -f "docker-compose.local.yml" ]; then
    echo "❌ docker-compose.local.yml not found. Please run setup-local-development.sh first."
    exit 1
fi

# Start services
echo "📦 Starting services..."
docker compose -f docker-compose.local.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Service Status:"
docker compose -f docker-compose.local.yml ps

echo ""
echo "🌐 Access Points:"
echo "  • API Service:           http://localhost:8000"
echo "  • Web Frontend:          http://localhost:3000"
echo "  • Scraper Service:       http://localhost:9008"
echo "  • Auth Service:          http://localhost:8001"
echo "  • Policy Service:        http://localhost:8002"
echo "  • Data Management:       http://localhost:8003"
echo "  • Search Service:        http://localhost:8004"
echo "  • MinIO Storage:        http://localhost:9000"
echo "  • MinIO Console:        http://localhost:9001 (minioadmin/minio123)"
echo "  • Vault:                 http://localhost:8200 (token: vault123)"
echo "  • Elasticsearch:         http://localhost:9200"
echo "  • Prometheus:            http://localhost:9090"
echo "  • Grafana:               http://localhost:3001 (admin/admin)"
echo "  • PostgreSQL:            localhost:5432"
echo "  • Redis:                 localhost:6379"
echo ""
echo "🔧 Commands:"
echo "  • View logs:  docker compose -f docker-compose.local.yml logs -f [service]"
echo "  • Stop all:   docker compose -f docker-compose.local.yml down"
echo "  • Status:     docker compose -f docker-compose.local.yml ps"
echo ""
echo "📚 Health Checks:"
echo "  • API:        curl http://localhost:8000/health"
echo "  • Scraper:    curl http://localhost:9008/health"
echo "  • MinIO:      curl http://localhost:9000/minio/health/live"
echo "  • Vault:      curl http://localhost:8200/v1/sys/health"
echo "  • ES:         curl http://localhost:9200/_cluster/health"
echo ""
echo "✅ Local development environment started!"
echo "🚀 Start developing in the ./backend/ and ./web/ directories!"
echo "🔐 Use local services instead of Azure: MinIO for storage, Vault for secrets, Elasticsearch for search!"
