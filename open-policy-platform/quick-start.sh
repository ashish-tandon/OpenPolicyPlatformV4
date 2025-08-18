#!/bin/bash

# 🚀 Open Policy Platform - Quick Start Script
# Fast deployment for testing and development

set -e

echo "🚀 Open Policy Platform - Quick Start"
echo "====================================="
echo ""

# Check if docker-compose.full.yml exists
if [ ! -f "docker-compose.full.yml" ]; then
    echo "❌ docker-compose.full.yml not found!"
    echo "Please run the full deployment first: ./deploy-full.sh"
    exit 1
fi

# Check if deploy-full.sh exists
if [ ! -f "deploy-full.sh" ]; then
    echo "❌ deploy-full.sh not found!"
    echo "Please ensure you have the full deployment script"
    exit 1
fi

echo "✅ All required files found"
echo ""

# Ask user preference
echo "Choose deployment option:"
echo "1) 🚀 Full deployment (all 23 services) - Recommended for first time"
echo "2) 🔧 Core services only (faster, fewer services)"
echo "3) 📊 Infrastructure + monitoring only"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting full deployment..."
        echo "This will deploy all 23 microservices"
        echo "Expected time: 10-20 minutes"
        echo ""
        read -p "Press Enter to continue..."
        ./deploy-full.sh
        ;;
    2)
        echo ""
        echo "🔧 Starting core services deployment..."
        echo "This will deploy essential services only"
        echo "Expected time: 5-10 minutes"
        echo ""
        
        # Start infrastructure
        echo "Starting infrastructure..."
        docker-compose -f docker-compose.full.yml up -d postgres redis
        
        # Wait for database
        echo "Waiting for database..."
        sleep 10
        
        # Start core services
        echo "Starting core services..."
        docker-compose -f docker-compose.full.yml up -d --build \
            auth-service policy-service config-service monitoring-service
        
        # Start API Gateway
        echo "Starting API Gateway..."
        docker-compose -f docker-compose.full.yml up -d --build api-gateway
        
        # Start frontend
        echo "Starting frontend..."
        docker-compose -f docker-compose.full.yml up -d web
        
        echo ""
        echo "✅ Core services deployed!"
        echo "Access points:"
        echo "- API Gateway: http://localhost:9000"
        echo "- Frontend: http://localhost:5173"
        echo "- Database: localhost:5432"
        ;;
    3)
        echo ""
        echo "📊 Starting infrastructure and monitoring..."
        echo "This will deploy database, Redis, Prometheus, and Grafana"
        echo ""
        
        # Start infrastructure
        echo "Starting infrastructure..."
        docker-compose -f docker-compose.full.yml up -d postgres redis prometheus grafana
        
        echo ""
        echo "✅ Infrastructure deployed!"
        echo "Access points:"
        echo "- PostgreSQL: localhost:5432"
        echo "- Redis: localhost:6379"
        echo "- Prometheus: http://localhost:9090"
        echo "- Grafana: http://localhost:3000 (admin/admin)"
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "Useful commands:"
echo "- View status: docker-compose -f docker-compose.full.yml ps"
echo "- View logs: docker-compose -f docker-compose.full.yml logs -f"
echo "- Stop services: docker-compose -f docker-compose.full.yml down"
echo ""
echo "Happy coding! 🚀"
