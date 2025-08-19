#!/bin/bash

# OpenPolicy Platform Deployment Script
# This script deploys the entire platform with all services

set -e

echo "🚀 OpenPolicy Platform Deployment Script"
echo "======================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to wait for service
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo "✅ $service is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to start after $max_attempts attempts"
    return 1
}

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start infrastructure services first
echo "🏗️  Starting infrastructure services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "http://localhost:5432" || exit 1

# Wait for Redis
sleep 5

# Start API service
echo "🚀 Starting API service..."
docker-compose up -d api

# Wait for API to be ready
wait_for_service "API" "http://localhost:8000/api/v1/health" || exit 1

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T api php artisan migrate --force

# Start remaining services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for all services to be ready
wait_for_service "Nginx Gateway" "http://localhost:80/api/v1/health" || exit 1
wait_for_service "Web Application" "http://localhost:3000" || exit 1
wait_for_service "Admin Dashboard" "http://localhost:3001" || exit 1

# Display service status
echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🌐 Access URLs:"
echo "   - Main Application: http://localhost"
echo "   - Admin Dashboard: http://localhost:3001"
echo "   - API Health: http://localhost/api/v1/health"
echo "   - API Docs: http://localhost/api/documentation"
echo ""
echo "📧 Login Credentials:"
echo "   Admin: admin@openpolicy.ca / admin123"
echo "   User: user@example.com / user123"
echo ""
echo "📝 Useful Commands:"
echo "   - View logs: docker-compose logs -f [service-name]"
echo "   - Stop all: docker-compose down"
echo "   - Restart service: docker-compose restart [service-name]"
echo "   - Run scrapers: docker-compose exec scraper python orchestrator.py"
echo ""