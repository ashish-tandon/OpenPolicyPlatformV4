#!/bin/bash

# 🚀 Fix All Ports Script
# Fixes port conflicts in all Dockerfiles

echo "🔧 Fixing all service ports..."

# Function to fix a service port
fix_service_port() {
    local service=$1
    local port=$2
    local dockerfile="services/$service/Dockerfile"
    
    if [ -f "$dockerfile" ]; then
        echo "🔧 Fixing $service port to $port..."
        
        # Update EXPOSE line
        sed -i '' "s/EXPOSE [0-9]*/EXPOSE $port/" "$dockerfile"
        
        # Update CMD line port
        sed -i '' "s/--port\", \"[0-9]*/--port\", \"$port/" "$dockerfile"
        
        echo "✅ $service port fixed to $port"
    else
        echo "❌ $dockerfile not found"
    fi
}

# Fix all service ports
fix_service_port "api-gateway" "9000"
fix_service_port "config-service" "9001"
fix_service_port "auth-service" "9002"
fix_service_port "policy-service" "9003"
fix_service_port "notification-service" "9004"
fix_service_port "analytics-service" "9005"
fix_service_port "monitoring-service" "9006"
fix_service_port "etl-service" "9007"
fix_service_port "scraper-service" "9008"
fix_service_port "search-service" "9009"
fix_service_port "dashboard-service" "9010"
fix_service_port "files-service" "9011"
fix_service_port "reporting-service" "9012"
fix_service_port "workflow-service" "9013"
fix_service_port "integration-service" "9014"
fix_service_port "data-management-service" "9015"
fix_service_port "representatives-service" "9016"
fix_service_port "plotly-service" "9017"
fix_service_port "mobile-api" "9018"
fix_service_port "legacy-django" "9019"

echo "🎉 All service ports fixed!"
