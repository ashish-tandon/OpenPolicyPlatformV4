#!/bin/bash

# 🚀 Open Policy Platform - Full Deployment Script
# Deploys all 23 microservices with comprehensive monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.full.yml"
SERVICES_COUNT=23
HEALTH_CHECK_TIMEOUT=300  # 5 minutes

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

step() {
    echo -e "${PURPLE}🔹 $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    step "Checking prerequisites..."
    
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    success "All prerequisites are met"
}

# Function to validate docker-compose file
validate_compose_file() {
    step "Validating docker-compose configuration..."
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if ! docker-compose -f "$COMPOSE_FILE" config --quiet; then
        error "Docker compose file validation failed"
        exit 1
    fi
    
    success "Docker compose file is valid"
}

# Function to check service directories
check_service_directories() {
    step "Checking service directories..."
    
    local missing_services=()
    local services=(
        "auth-service" "policy-service" "search-service" "notification-service"
        "config-service" "monitoring-service" "etl-service" "scraper-service"
        "mobile-api" "legacy-django" "committees-service" "debates-service"
        "votes-service" "representatives-service" "files-service" "dashboard-service"
        "data-management-service" "analytics-service" "reporting-service"
        "workflow-service" "integration-service" "plotly-service" "mcp-service"
        "api-gateway"
    )
    
    for service in "${services[@]}"; do
        if [ ! -d "services/$service" ]; then
            missing_services+=("$service")
        fi
    done
    
    if [ ${#missing_services[@]} -gt 0 ]; then
        warning "Missing service directories: ${missing_services[*]}"
        info "Some services may not be fully implemented yet"
    else
        success "All service directories found"
    fi
}

# Function to stop existing services
stop_existing_services() {
    step "Stopping existing services..."
    
    if docker-compose -f "$COMPOSE_FILE" ps --services | grep -q .; then
        info "Stopping existing services..."
        docker-compose -f "$COMPOSE_FILE" down --remove-orphans
        success "Existing services stopped"
    else
        info "No existing services to stop"
    fi
}

# Function to clean up resources
cleanup_resources() {
    step "Cleaning up Docker resources..."
    
    # Remove unused containers
    docker container prune -f >/dev/null 2>&1 || true
    
    # Remove unused networks
    docker network prune -f >/dev/null 2>&1 || true
    
    # Remove unused volumes (be careful with this in production)
    # docker volume prune -f >/dev/null 2>&1 || true
    
    success "Docker resources cleaned up"
}

# Function to build and start infrastructure services
start_infrastructure() {
    step "Starting infrastructure services..."
    
    info "Starting PostgreSQL and Redis..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for PostgreSQL to be healthy
    info "Waiting for PostgreSQL to be healthy..."
    local timeout=60
    local counter=0
    
    while [ $counter -lt $timeout ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U openpolicy -d openpolicy >/dev/null 2>&1; then
            success "PostgreSQL is healthy"
            break
        fi
        counter=$((counter + 5))
        info "Waiting for PostgreSQL... ($counter/$timeout seconds)"
        sleep 5
    done
    
    if [ $counter -ge $timeout ]; then
        error "PostgreSQL health check timeout"
        exit 1
    fi
    
    success "Infrastructure services started"
}

# Function to build and start core services
start_core_services() {
    step "Building and starting core services..."
    
    local core_services=(
        "auth-service" "policy-service" "search-service" "notification-service"
        "config-service" "monitoring-service" "etl-service" "scraper-service"
    )
    
    for service in "${core_services[@]}"; do
        info "Building and starting $service..."
        docker-compose -f "$COMPOSE_FILE" up -d --build "$service"
        
        # Wait a bit between services to avoid overwhelming the system
        sleep 2
    done
    
    success "Core services started"
}

# Function to build and start specialized services
start_specialized_services() {
    step "Building and starting specialized services..."
    
    local specialized_services=(
        "mobile-api" "legacy-django" "committees-service" "debates-service"
        "votes-service"
    )
    
    for service in "${specialized_services[@]}"; do
        info "Building and starting $service..."
        docker-compose -f "$COMPOSE_FILE" up -d --build "$service"
        sleep 2
    done
    
    success "Specialized services started"
}

# Function to build and start business services
start_business_services() {
    step "Building and starting business services..."
    
    local business_services=(
        "representatives-service" "files-service" "dashboard-service"
        "data-management-service" "analytics-service" "reporting-service"
        "workflow-service" "integration-service"
    )
    
    for service in "${business_services[@]}"; do
        info "Building and starting $service..."
        docker-compose -f "$COMPOSE_FILE" up -d --build "$service"
        sleep 2
    done
    
    success "Business services started"
}

# Function to build and start utility services
start_utility_services() {
    step "Building and starting utility services..."
    
    local utility_services=(
        "plotly-service" "mcp-service"
    )
    
    for service in "${utility_services[@]}"; do
        info "Building and starting $service..."
        docker-compose -f "$COMPOSE_FILE" up -d --build "$service"
        sleep 2
    done
    
    success "Utility services started"
}

# Function to start API Gateway
start_api_gateway() {
    step "Building and starting API Gateway..."
    
    info "Building and starting API Gateway..."
    docker-compose -f "$COMPOSE_FILE" up -d --build api-gateway
    
    success "API Gateway started"
}

# Function to start remaining services
start_remaining_services() {
    step "Starting remaining services..."
    
    local remaining_services=(
        "api" "web" "prometheus" "grafana" "celery-worker"
        "celery-beat" "flower" "scraper-runner"
    )
    
    for service in "${remaining_services[@]}"; do
        info "Starting $service..."
        docker-compose -f "$COMPOSE_FILE" up -d "$service"
        sleep 1
    done
    
    success "Remaining services started"
}

# Function to check service health
check_service_health() {
    step "Checking service health..."
    
    local healthy_services=0
    local total_services=0
    
    # Get list of all services
    local services=$(docker-compose -f "$COMPOSE_FILE" ps --services)
    
    for service in $services; do
        total_services=$((total_services + 1))
        
        # Check if service is running
        if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            healthy_services=$((healthy_services + 1))
            success "$service is running"
        else
            error "$service is not running"
        fi
    done
    
    info "Health check summary: $healthy_services/$total_services services running"
    
    if [ $healthy_services -eq $total_services ]; then
        success "All services are healthy! 🎉"
    else
        warning "Some services may need attention"
    fi
}

# Function to display service status
display_service_status() {
    step "Displaying service status..."
    
    echo ""
    echo "🚀 Open Policy Platform - Service Status"
    echo "=========================================="
    docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🌐 Service Endpoints:"
    echo "====================="
    echo "API Gateway:        http://localhost:9000"
    echo "Frontend:           http://localhost:5173"
    echo "Legacy API:         http://localhost:8000"
    echo "PostgreSQL:         localhost:5432"
    echo "Redis:              localhost:6379"
    echo "Prometheus:         http://localhost:9090"
    echo "Grafana:            http://localhost:3000 (admin/admin)"
    echo "Flower (Celery):    http://localhost:5555"
    echo ""
    echo "🔍 Individual Service Ports:"
    echo "============================="
    echo "Auth Service:       9001"
    echo "Policy Service:     9002"
    echo "Search Service:     9003"
    echo "Notification:       9004"
    echo "Config Service:     9005"
    echo "Monitoring:         9006"
    echo "ETL Service:        9007"
    echo "Scraper Service:    9008"
    echo "Mobile API:         8009"
    echo "Legacy Django:      8010"
    echo "Committees:         9011"
    echo "Debates:            9012"
    echo "Votes:              9013"
    echo "Representatives:    8014"
    echo "Files Service:      8015"
    echo "Dashboard:          8016"
    echo "Data Management:    8017"
    echo "Analytics:          8018"
    echo "Reporting:          8019"
    echo "Workflow:           8020"
    echo "Integration:        8021"
    echo "Plotly Service:     9019"
    echo "MCP Service:        9020"
}

# Function to run smoke tests
run_smoke_tests() {
    step "Running smoke tests..."
    
    # Test API Gateway
    if curl -s http://localhost:9000/healthz >/dev/null; then
        success "API Gateway health check passed"
    else
        warning "API Gateway health check failed"
    fi
    
    # Test a few key services
    local test_services=(
        "http://localhost:9001/healthz"
        "http://localhost:9005/healthz"
        "http://localhost:8000/api/v1/health"
    )
    
    for endpoint in "${test_services[@]}"; do
        if curl -s "$endpoint" >/dev/null; then
            success "Health check passed: $endpoint"
        else
            warning "Health check failed: $endpoint"
        fi
    done
    
    success "Smoke tests completed"
}

# Main deployment function
main() {
    echo ""
    echo "🚀 Open Policy Platform - Full Deployment"
    echo "=========================================="
    echo "This script will deploy all $SERVICES_COUNT microservices"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Validate compose file
    validate_compose_file
    
    # Check service directories
    check_service_directories
    
    # Stop existing services
    stop_existing_services
    
    # Clean up resources
    cleanup_resources
    
    # Start infrastructure
    start_infrastructure
    
    # Start services in order
    start_core_services
    start_specialized_services
    start_business_services
    start_utility_services
    start_api_gateway
    start_remaining_services
    
    # Wait for all services to be ready
    info "Waiting for all services to be ready..."
    sleep 30
    
    # Check health
    check_service_health
    
    # Display status
    display_service_status
    
    # Run smoke tests
    run_smoke_tests
    
    echo ""
    success "🎉 Open Policy Platform deployment completed!"
    echo ""
    info "Next steps:"
    echo "1. Access the frontend at http://localhost:5173"
    echo "2. Use the API Gateway at http://localhost:9000"
    echo "3. Monitor services at http://localhost:3000 (Grafana)"
    echo "4. Check service logs: docker-compose -f $COMPOSE_FILE logs -f [service-name]"
    echo ""
    info "To stop all services: docker-compose -f $COMPOSE_FILE down"
    echo "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo ""
}

# Run main function
main "$@"
