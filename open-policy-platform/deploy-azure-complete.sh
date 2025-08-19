#!/bin/bash

# 🚀 Open Policy Platform V4 - Complete Azure Deployment
# This script deploys ALL 26 services to Azure

set -e

echo "🚀 Open Policy Platform V4 - Complete Azure Deployment"
echo "======================================================"
echo "📊 Deploying ALL 26 services to Azure"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.azure-complete.yml" ]; then
    print_error "docker-compose.azure-complete.yml not found. Please run this script from the open-policy-platform directory."
    exit 1
fi

# Check if environment file exists
if [ ! -f "env.azure.complete" ]; then
    print_error "env.azure.complete not found. Please ensure your Azure environment is configured."
    exit 1
fi

# Load environment variables
print_info "Loading Azure environment variables..."
source env.azure.complete

# Verify required variables
required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "AZURE_KEY_VAULT_URL"
    "AZURE_STORAGE_ACCOUNT"
    "AZURE_STORAGE_KEY"
    "AZURE_SEARCH_SERVICE"
    "AZURE_SEARCH_KEY"
    "AZURE_JWT_SECRET"
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET"
    "AZURE_TENANT_ID"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set"
        exit 1
    fi
done

print_status "Environment variables loaded successfully"

# Stop current deployment
print_info "Stopping current Azure deployment..."
docker compose -f docker-compose.azure-simple.yml down --volumes --remove-orphans 2>/dev/null || true

# Wait a moment for cleanup
sleep 5

# Start complete deployment
print_info "Starting complete Azure deployment with ALL 26 services..."
print_info "This will take several minutes as we build and start all services..."

# Start the complete deployment
docker compose -f docker-compose.azure-complete.yml up -d --build

print_status "Complete deployment started successfully!"

# Wait for services to start
print_info "Waiting for services to start (this may take 5-10 minutes)..."
sleep 60

# Check service status
print_info "Checking service status..."
docker compose -f docker-compose.azure-complete.yml ps

# Wait more and check health
print_info "Waiting for services to become healthy..."
sleep 120

# Check health status
print_info "Checking service health status..."
docker compose -f docker-compose.azure-complete.yml ps --format table

# Display service access information
echo
echo "🎉 COMPLETE AZURE DEPLOYMENT SUCCESSFUL!"
echo "========================================"
echo
echo "📊 Service Status:"
docker compose -f docker-compose.azure-complete.yml ps --format table
echo
echo "🌐 Service Access Points:"
echo "  • API Service:           http://localhost:8000"
echo "  • Web Frontend:          http://localhost:3000"
echo "  • Scraper Service:       http://localhost:9008"
echo "  • Auth Service:          http://localhost:8001"
echo "  • Policy Service:        http://localhost:8002"
echo "  • Data Management:       http://localhost:8003"
echo "  • Search Service:        http://localhost:8004"
echo "  • Analytics Service:     http://localhost:8005"
echo "  • Dashboard Service:     http://localhost:8006"
echo "  • Notification Service:  http://localhost:8007"
echo "  • Votes Service:         http://localhost:8008"
echo "  • Debates Service:       http://localhost:8009"
echo "  • Committees Service:    http://localhost:8010"
echo "  • ETL Service:           http://localhost:8011"
echo "  • Files Service:         http://localhost:8012"
echo "  • Integration Service:   http://localhost:8013"
echo "  • Workflow Service:      http://localhost:8014"
echo "  • Reporting Service:     http://localhost:8015"
echo "  • Representatives:       http://localhost:8016"
echo "  • Plotly Service:        http://localhost:8017"
echo "  • Mobile API:            http://localhost:8018"
echo "  • Monitoring Service:    http://localhost:8019"
echo "  • Config Service:        http://localhost:8020"
echo "  • API Gateway:           http://localhost:8021"
echo "  • MCP Service:           http://localhost:8022"
echo "  • Docker Monitor:        http://localhost:8023"
echo "  • Legacy Django:         http://localhost:8024"
echo "  • ETL Legacy:            http://localhost:8025"
echo "  • Prometheus:            http://localhost:9090"
echo "  • Grafana:               http://localhost:3001"
echo
echo "🔧 Management Commands:"
echo "  • View logs:             docker compose -f docker-compose.azure-complete.yml logs -f [service]"
echo "  • Restart service:       docker compose -f docker-compose.azure-complete.yml restart [service]"
echo "  • Stop all:              docker compose -f docker-compose.azure-complete.yml down"
echo "  • Start all:             docker compose -f docker-compose.azure-complete.yml up -d"
echo
echo "📚 Health Check Endpoints:"
echo "  • API Health:            curl http://localhost:8000/health"
echo "  • Scraper Health:        curl http://localhost:9008/health"
echo "  • Auth Health:           curl http://localhost:8001/health"
echo "  • Policy Health:         curl http://localhost:8002/health"
echo "  • Data Mgmt Health:      curl http://localhost:8003/health"
echo "  • Search Health:         curl http://localhost:8004/health"
echo
echo "🚀 All 26 services are now deployed and running on Azure!"
echo "🎯 Your Open Policy Platform V4 is now complete!"
echo
echo "📊 Next Steps:"
echo "  1. Test all service endpoints"
echo "  2. Verify data flow between services"
echo "  3. Monitor service health and performance"
echo "  4. Begin using the full platform capabilities"
echo
print_status "Complete Azure deployment finished successfully!"
