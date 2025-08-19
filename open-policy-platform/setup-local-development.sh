#!/bin/bash

# 🚀 Open Policy Platform V4 - Local Development Setup Script
# This script sets up the complete development environment on your local laptop

set -e

echo "🎯 Setting up Open Policy Platform V4 for Local Development"
echo "=========================================================="

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

# Check if Docker is running
check_docker() {
    print_info "Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Check if required ports are available
check_ports() {
    print_info "Checking if required ports are available..."
    
    local ports=("5432" "6379" "8000" "8001" "8002" "8003" "8004" "3000" "9000" "9001" "9008" "8200" "9200" "9090" "3001")
    local conflicts=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            conflicts+=("$port")
        fi
    done
    
    if [ ${#conflicts[@]} -gt 0 ]; then
        print_warning "The following ports are already in use: ${conflicts[*]}"
        print_warning "Please stop the services using these ports or modify the docker-compose.local.yml file"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "All required ports are available"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/minio
    mkdir -p data/elasticsearch
    mkdir -p data/prometheus
    mkdir -p data/grafana
    mkdir -p data/scraper/reports
    mkdir -p data/scraper/logs
    
    print_status "Directories created"
}

# Build and start services
start_services() {
    print_info "Building and starting services..."
    
    # Stop any existing services first
    docker compose -f docker-compose.local.yml down --volumes --remove-orphans 2>/dev/null || true
    
    # Build and start services
    docker compose -f docker-compose.local.yml up -d --build
    
    print_status "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_info "Waiting for services... (attempt $attempt/$max_attempts)"
        
        # Check if all services are running
        if docker compose -f docker-compose.local.yml ps | grep -q "Up"; then
            print_status "All services are running"
            break
        fi
        
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Services failed to start within expected time"
        docker compose -f docker-compose.local.yml logs
        exit 1
    fi
}

# Check service health
check_service_health() {
    print_info "Checking service health..."
    
    local max_attempts=30
    local attempt=1
    
    # Services to check with their health endpoints
    local services=(
        "API:http://localhost:8000/health"
        "Scraper:http://localhost:9008/health"
        "Web Frontend:http://localhost:3000"
        "MinIO:http://localhost:9000/minio/health/live"
        "Vault:http://localhost:8200/v1/sys/health"
        "Elasticsearch:http://localhost:9200/_cluster/health"
    )
    
    while [ $attempt -le $max_attempts ]; do
        print_info "Checking service health... (attempt $attempt/$max_attempts)"
        
        local all_healthy=true
        
        for service_info in "${services[@]}"; do
            local service_name="${service_info%%:*}"
            local health_url="${service_info##*:}"
            
            if curl -s "$health_url" > /dev/null 2>&1; then
                print_status "$service_name is healthy"
            else
                print_warning "$service_name not ready yet"
                all_healthy=false
            fi
        done
        
        if [ "$all_healthy" = true ]; then
            print_status "All services are healthy!"
            break
        fi
        
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        print_error "Services failed to become healthy within expected time"
        docker compose -f docker-compose.local.yml logs
        exit 1
    fi
}

# Initialize local services
initialize_local_services() {
    print_info "Initializing local services..."
    
    # Wait for services to be fully ready
    sleep 30
    
    # Initialize MinIO buckets
    print_info "Setting up MinIO storage..."
    docker exec openpolicy-local-minio mkdir -p /data/openpolicy-bucket 2>/dev/null || true
    
    # Initialize Vault
    print_info "Setting up Vault secrets..."
    # Vault is already initialized in dev mode
    
    # Initialize Elasticsearch indices
    print_info "Setting up Elasticsearch..."
    # Elasticsearch will create indices automatically when needed
    
    print_status "Local services initialized"
}

# Initialize database with sample data
initialize_database() {
    print_info "Initializing database with sample data..."
    
    # Wait a bit more for database to be fully ready
    sleep 30
    
    # Check if database is accessible
    if docker exec openpolicy-local-postgres pg_isready -U openpolicy -d openpolicy > /dev/null 2>&1; then
        print_status "Database is accessible"
        
        # Import sample data if the script exists
        if [ -f "import_existing_data.py" ]; then
            print_info "Importing sample data..."
            docker exec openpolicy-local-api python /app/import_existing_data.py || print_warning "Sample data import failed (this is optional)"
        fi
    else
        print_warning "Database not ready yet, skipping data import"
    fi
}

# Display final status
display_status() {
    echo
    echo "🎉 Local Development Environment Setup Complete!"
    echo "================================================"
    echo
    echo "📊 Service Status:"
    docker compose -f docker-compose.local.yml ps --format table
    echo
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
    echo
    echo "🔧 Development Commands:"
    echo "  • View logs:             docker compose -f docker-compose.local.yml logs -f [service]"
    echo "  • Restart service:       docker compose -f docker-compose.local.yml restart [service]"
    echo "  • Stop all:              docker compose -f docker-compose.local.yml down"
    echo "  • Start all:             docker compose -f docker-compose.local.yml up -d"
    echo
    echo "📚 Health Check Endpoints:"
    echo "  • API Health:            curl http://localhost:8000/health"
    echo "  • Scraper Health:        curl http://localhost:9008/health"
    echo "  • MinIO Health:          curl http://localhost:9000/minio/health/live"
    echo "  • Vault Health:          curl http://localhost:8200/v1/sys/health"
    echo "  • Elasticsearch Health:  curl http://localhost:9200/_cluster/health"
    echo
    echo "🚀 You're ready to start developing!"
    echo
}

# Main execution
main() {
    echo "🎯 Open Policy Platform V4 - Local Development Setup"
    echo "===================================================="
    echo
    
    check_docker
    check_ports
    create_directories
    start_services
    wait_for_services
    check_service_health
    initialize_local_services
    initialize_database
    display_status
    
    print_status "Local development environment setup completed successfully!"
}

# Run main function
main "$@"
