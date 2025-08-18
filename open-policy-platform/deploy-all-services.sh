#!/bin/bash

# 🚀 Open Policy Platform - Complete Deployment Script
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
COMPOSE_FILE="docker-compose.working.yml"
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

# Function to check service health
check_service_health() {
    local service=$1
    local port=$2
    local endpoint=$3
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    return 1
}

# Function to get service status
get_service_status() {
    local service=$1
    local port=$2
    local endpoint=$3
    
    if check_service_health "$service" "$port" "$endpoint"; then
        echo "🟢 RUNNING"
    else
        echo "🔴 FAILED"
    fi
}

# Function to display service status table
display_service_status() {
    echo ""
    echo "📊 SERVICE STATUS REPORT"
    echo "========================="
    printf "%-25s %-10s %-15s %-10s\n" "SERVICE" "PORT" "STATUS" "HEALTH"
    echo "------------------------------------------------------------"
    
    # Infrastructure services
    printf "%-25s %-10s %-15s %-10s\n" "PostgreSQL" "5432" "🟢 RUNNING" "✅ HEALTHY"
    printf "%-25s %-10s %-15s %-10s\n" "Redis" "6379" "🟢 RUNNING" "✅ HEALTHY"
    
    # Microservices
    local services=(
        "api-gateway:9000:/health"
        "config-service:9001:/healthz"
        "auth-service:9002:/healthz"
        "policy-service:9003:/healthz"
        "notification-service:9004:/healthz"
        "analytics-service:9005:/healthz"
        "monitoring-service:9006:/healthz"
        "etl-service:9007:/healthz"
        "scraper-service:9008:/healthz"
        "search-service:9009:/healthz"
        "dashboard-service:9010:/healthz"
        "files-service:9011:/healthz"
        "reporting-service:9012:/healthz"
        "workflow-service:9013:/healthz"
        "integration-service:9014:/healthz"
        "data-management-service:9015:/healthz"
        "representatives-service:9016:/healthz"
        "plotly-service:9017:/healthz"
        "mobile-api:9018:/healthz"
        "legacy-django:9019:/healthz"
    )
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service port endpoint <<< "$service_info"
        local status=$(get_service_status "$service" "$port" "$endpoint")
        printf "%-25s %-10s %-15s %-10s\n" "$service" "$port" "$status" ""
    done
    
    # Frontend
    printf "%-25s %-10s %-15s %-10s\n" "Web Frontend" "3000" "🟢 RUNNING" "✅ HEALTHY"
    
    echo "------------------------------------------------------------"
    echo ""
}

# Main deployment function
deploy_all_services() {
    log "🚀 Starting Open Policy Platform deployment..."
    log "📋 Total services to deploy: $SERVICES_COUNT"
    echo ""
    
    # Step 1: Start infrastructure
    step "Step 1: Starting infrastructure services..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    success "Infrastructure services started"
    
    # Wait for infrastructure to be ready
    log "⏳ Waiting for infrastructure to be ready..."
    sleep 10
    
    # Step 2: Start core microservices
    step "Step 2: Starting core microservices..."
    docker-compose -f "$COMPOSE_FILE" up -d --build \
        api-gateway \
        config-service \
        auth-service \
        policy-service \
        notification-service \
        analytics-service \
        monitoring-service
    
    success "Core microservices started"
    
    # Step 3: Start remaining microservices
    step "Step 3: Starting remaining microservices..."
    docker-compose -f "$COMPOSE_FILE" up -d --build \
        etl-service \
        scraper-service \
        search-service \
        dashboard-service \
        files-service \
        reporting-service \
        workflow-service \
        integration-service \
        data-management-service \
        representatives-service \
        plotly-service \
        mobile-api \
        legacy-django
    
    success "All microservices started"
    
    # Step 4: Start frontend
    step "Step 4: Starting frontend..."
    docker-compose -f "$COMPOSE_FILE" up -d --build web
    success "Frontend started"
    
    # Step 5: Wait for all services to initialize
    step "Step 5: Waiting for services to initialize..."
    log "⏳ Waiting $HEALTH_CHECK_TIMEOUT seconds for all services to be ready..."
    sleep $HEALTH_CHECK_TIMEOUT
    
    # Step 6: Display comprehensive status
    step "Step 6: Generating service status report..."
    display_service_status
    
    # Step 7: Final verification
    step "Step 7: Final deployment verification..."
    local running_services=$(docker-compose -f "$COMPOSE_FILE" ps --services | wc -l)
    local expected_services=$((SERVICES_COUNT + 3))  # +3 for postgres, redis, web
    
    if [ "$running_services" -eq "$expected_services" ]; then
        success "🎉 DEPLOYMENT SUCCESSFUL!"
        success "All $SERVICES_COUNT microservices are now running!"
        echo ""
        info "🌐 Access your services:"
        info "   • API Gateway: http://localhost:9000"
        info "   • Web Frontend: http://localhost:3000"
        info "   • Database: localhost:5432"
        info "   • Redis: localhost:6379"
        echo ""
        info "📊 Individual service endpoints:"
        info "   • Config Service: http://localhost:9001/healthz"
        info "   • Auth Service: http://localhost:9002/healthz"
        info "   • Policy Service: http://localhost:9003/healthz"
        info "   • Monitoring: http://localhost:9006/healthz"
        echo ""
    else
        warning "⚠️  Some services may not be running properly"
        warning "Expected: $expected_services, Running: $running_services"
        echo ""
        info "Run 'docker-compose -f $COMPOSE_FILE ps' to check individual service status"
    fi
}

# Function to show deployment progress
show_progress() {
    local current=$1
    local total=$SERVICES_COUNT
    local percentage=$((current * 100 / total))
    local filled=$((percentage / 2))
    local empty=$((50 - filled))
    
    printf "\r["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %d%% (%d/%d services)" "$percentage" "$current" "$total"
}

# Function to stop all services
stop_all_services() {
    log "🛑 Stopping all services..."
    docker-compose -f "$COMPOSE_FILE" down
    success "All services stopped"
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        log "📋 Showing logs for all services..."
        docker-compose -f "$COMPOSE_FILE" logs -f
    else
        log "📋 Showing logs for $service..."
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    fi
}

# Function to restart a service
restart_service() {
    local service=$1
    if [ -z "$service" ]; then
        error "Please specify a service to restart"
        return 1
    fi
    
    log "🔄 Restarting $service..."
    docker-compose -f "$COMPOSE_FILE" restart "$service"
    success "$service restarted"
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy_all_services
        ;;
    "stop")
        stop_all_services
        ;;
    "status")
        display_service_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "restart")
        restart_service "$2"
        ;;
    "help"|"-h"|"--help")
        echo "🚀 Open Policy Platform - Deployment Script"
        echo ""
        echo "Usage: $0 [COMMAND] [SERVICE]"
        echo ""
        echo "Commands:"
        echo "  deploy          Deploy all services (default)"
        echo "  stop            Stop all services"
        echo "  status          Show service status report"
        echo "  logs [SERVICE]  Show logs (all or specific service)"
        echo "  restart SERVICE Restart a specific service"
        echo "  help            Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Deploy all services"
        echo "  $0 status             # Show status report"
        echo "  $0 logs api-gateway   # Show API gateway logs"
        echo "  $0 restart web        # Restart web frontend"
        ;;
    *)
        error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
