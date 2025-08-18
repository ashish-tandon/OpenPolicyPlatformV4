#!/bin/bash

# 🚀 COMPREHENSIVE SERVICE DEPLOYMENT SCRIPT
# Open Policy Platform - All Services Deployment

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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICES_DIR="$PROJECT_ROOT/services"
LOGS_DIR="$PROJECT_ROOT/logs"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Service configurations (macOS compatible)
SERVICES=(
    "api-gateway:9000"
    "auth-service:9001"
    "policy-service:9002"
    "search-service:9003"
    "notification-service:9004"
    "config-service:9005"
    "monitoring-service:9006"
    "etl-service:9007"
    "scraper-service:9008"
    "committees-service:9011"
    "debates-service:9012"
    "votes-service:9013"
)

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "PHASE") echo -e "${PURPLE}[PHASE]${NC} $message" ;;
        "SERVICE") echo -e "${CYAN}[SERVICE]${NC} $message" ;;
    esac
}

# Function to get service port
get_service_port() {
    local service_name=$1
    for service in "${SERVICES[@]}"; do
        if [[ "$service" == "$service_name:"* ]]; then
            echo "${service#*:}"
            return 0
        fi
    done
    echo ""
}

# Function to check if service is running
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    print_status "INFO" "Checking health of $service_name on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/healthz" > /dev/null 2>&1; then
            print_status "SUCCESS" "$service_name is healthy and responding on port $port"
            return 0
        fi
        
        print_status "INFO" "Attempt $attempt/$max_attempts: $service_name not ready yet, waiting 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    print_status "ERROR" "$service_name failed to become healthy after $max_attempts attempts"
    return 1
}

# Function to deploy a single service
deploy_service() {
    local service_name=$1
    local service_dir="$SERVICES_DIR/$service_name"
    
    if [ ! -d "$service_dir" ]; then
        print_status "WARNING" "Service directory $service_dir not found, skipping..."
        return 0
    fi
    
    print_status "SERVICE" "Deploying $service_name..."
    
    # Check if service has Dockerfile
    if [ -f "$service_dir/Dockerfile" ]; then
        print_status "INFO" "Building Docker image for $service_name..."
        
        # Build Docker image
        cd "$service_dir"
        docker build -t "openpolicy-$service_name:latest" . || {
            print_status "ERROR" "Failed to build Docker image for $service_name"
            return 1
        }
        
        print_status "SUCCESS" "Docker image built successfully for $service_name"
        cd "$PROJECT_ROOT"
    else
        print_status "INFO" "No Dockerfile found for $service_name, skipping Docker build"
    fi
    
    # Check if service has requirements.txt (Python service)
    if [ -f "$service_dir/requirements.txt" ]; then
        print_status "INFO" "Installing Python dependencies for $service_name..."
        
        # Create virtual environment if it doesn't exist
        if [ ! -d "$service_dir/venv" ]; then
            python3 -m venv "$service_dir/venv"
        fi
        
        # Activate virtual environment and install dependencies
        source "$service_dir/venv/bin/activate"
        pip install -r "$service_dir/requirements.txt" || {
            print_status "ERROR" "Failed to install Python dependencies for $service_name"
            return 1
        }
        deactivate
        
        print_status "SUCCESS" "Python dependencies installed for $service_name"
    fi
    
    print_status "SUCCESS" "$service_name deployment completed"
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$(get_service_port "$service_name")
    
    if [ -z "$port" ]; then
        print_status "WARNING" "No port configured for $service_name, skipping start"
        return 0
    fi
    
    print_status "SERVICE" "Starting $service_name on port $port..."
    
    # Check if port is already in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "WARNING" "Port $port is already in use, $service_name may already be running"
        return 0
    fi
    
    # Start service based on type
    local service_dir="$SERVICES_DIR/$service_name"
    
    if [ -f "$service_dir/Dockerfile" ]; then
        # Start with Docker
        cd "$service_dir"
        docker run -d \
            --name "openpolicy-$service_name" \
            -p "$port:$port" \
            -e "PORT=$port" \
            "openpolicy-$service_name:latest" || {
            print_status "ERROR" "Failed to start Docker container for $service_name"
            return 1
        }
        cd "$PROJECT_ROOT"
    else
        # Start with Python directly
        cd "$service_dir"
        if [ -f "requirements.txt" ] && [ -d "venv" ]; then
            source venv/bin/activate
            nohup python src/main.py > "$LOGS_DIR/services/$service_name.log" 2>&1 &
            deactivate
        elif [ -f "src/main.py" ]; then
            nohup python src/main.py > "$LOGS_DIR/services/$service_name.log" 2>&1 &
        else
            print_status "WARNING" "No main.py found for $service_name, cannot start"
            cd "$PROJECT_ROOT"
            return 0
        fi
        cd "$PROJECT_ROOT"
    fi
    
    # Wait for service to become healthy
    sleep 3
    check_service_health "$service_name" "$port"
}

# Function to create logs directory structure
setup_logs() {
    print_status "INFO" "Setting up logs directory structure..."
    
    mkdir -p "$LOGS_DIR"/{application,audit,errors,infrastructure,monitoring,performance,run,services}
    
    # Create service-specific log files
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        touch "$LOGS_DIR/services/$service_name.log"
    done
    
    print_status "SUCCESS" "Logs directory structure created"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "INFO" "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_status "WARNING" "Docker not found, some services may not start properly"
    else
        print_status "SUCCESS" "Docker found"
    fi
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        print_status "ERROR" "Python 3 not found, required for service deployment"
        exit 1
    else
        print_status "SUCCESS" "Python 3 found"
    fi
    
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        print_status "ERROR" "curl not found, required for health checks"
        exit 1
    else
        print_status "SUCCESS" "curl found"
    fi
    
    print_status "SUCCESS" "All prerequisites satisfied"
}

# Function to display deployment summary
show_deployment_summary() {
    print_status "PHASE" "=== DEPLOYMENT SUMMARY ==="
    echo
    print_status "INFO" "Services deployed:"
    
    local deployed_count=0
    local total_count=${#SERVICES[@]}
    
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        local port="${service#*:}"
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_status "SUCCESS" "  ✅ $service_name (Port $port) - RUNNING"
            ((deployed_count++))
        else
            print_status "ERROR" "  ❌ $service_name (Port $port) - NOT RUNNING"
        fi
    done
    
    echo
    print_status "PHASE" "Deployment Status: $deployed_count/$total_count services running"
    
    if [ $deployed_count -eq $total_count ]; then
        print_status "SUCCESS" "🎉 ALL SERVICES SUCCESSFULLY DEPLOYED!"
    else
        print_status "WARNING" "⚠️  Some services failed to deploy. Check logs for details."
    fi
    
    echo
    print_status "INFO" "Service URLs:"
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        local port="${service#*:}"
        echo "  🌐 $service_name: http://localhost:$port"
        echo "  📊 Health Check: http://localhost:$port/healthz"
        echo "  📈 Metrics: http://localhost:$port/metrics"
        echo
    done
    
    print_status "INFO" "Logs available in: $LOGS_DIR"
    print_status "INFO" "Docker containers: docker ps | grep openpolicy"
}

# Main deployment function
main() {
    print_status "PHASE" "🚀 STARTING COMPREHENSIVE SERVICE DEPLOYMENT"
    echo
    
    # Check prerequisites
    check_prerequisites
    echo
    
    # Setup logs
    setup_logs
    echo
    
    # Phase 1: Deploy all services
    print_status "PHASE" "📦 PHASE 1: DEPLOYING ALL SERVICES"
    echo
    
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        deploy_service "$service_name"
        echo
    done
    
    # Phase 2: Start all services
    print_status "PHASE" "🚀 PHASE 2: STARTING ALL SERVICES"
    echo
    
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        start_service "$service_name"
        echo
    done
    
    # Phase 3: Verify deployment
    print_status "PHASE" "✅ PHASE 3: VERIFYING DEPLOYMENT"
    echo
    
    # Wait for all services to be ready
    print_status "INFO" "Waiting for all services to become ready..."
    sleep 10
    
    # Show deployment summary
    show_deployment_summary
}

# Function to stop all services
stop_all_services() {
    print_status "PHASE" "🛑 STOPPING ALL SERVICES"
    
    # Stop Docker containers
    docker stop $(docker ps -q --filter "name=openpolicy-") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=openpolicy-") 2>/dev/null || true
    
    # Kill Python processes
    pkill -f "python.*main.py" 2>/dev/null || true
    
    print_status "SUCCESS" "All services stopped"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  deploy     Deploy and start all services (default)"
    echo "  stop       Stop all running services"
    echo "  status     Show status of all services"
    echo "  logs       Show logs for all services"
    echo "  help       Show this help message"
    echo
    echo "Examples:"
    echo "  $0              # Deploy all services"
    echo "  $0 deploy       # Deploy all services"
    echo "  $0 stop         # Stop all services"
    echo "  $0 status       # Show service status"
    echo "  $0 logs         # Show service logs"
}

# Function to show service status
show_service_status() {
    print_status "PHASE" "📊 SERVICE STATUS"
    echo
    
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        local port="${service#*:}"
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_status "SUCCESS" "$service_name (Port $port): RUNNING"
        else
            print_status "ERROR" "$service_name (Port $port): STOPPED"
        fi
    done
}

# Function to show service logs
show_service_logs() {
    print_status "PHASE" "📋 SERVICE LOGS"
    echo
    
    for service in "${SERVICES[@]}"; do
        local service_name="${service%:*}"
        local log_file="$LOGS_DIR/services/$service_name.log"
        if [ -f "$log_file" ]; then
            print_status "INFO" "=== $service_name logs ==="
            tail -20 "$log_file" 2>/dev/null || echo "No logs available"
            echo
        fi
    done
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        stop_all_services
        ;;
    "status")
        show_service_status
        ;;
    "logs")
        show_service_logs
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
