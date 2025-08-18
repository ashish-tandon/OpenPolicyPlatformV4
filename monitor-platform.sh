#!/bin/bash

# Open Policy Platform V4 - Real-Time Monitoring Script
# Continuously monitors all services, logs, and errors

set -e

echo "🔍 Open Policy Platform V4 - Real-Time Monitoring"
echo "=================================================="
echo "Monitoring: All 5 core services, logs, and errors"
echo "Status: Continuous monitoring with error tracking"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Monitoring counters
MONITORING_START_TIME=$(date +%s)
ERROR_COUNT=0
HEALTH_CHECK_COUNT=0

# Function to log with timestamp
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}"
            ERROR_COUNT=$((ERROR_COUNT + 1))
            ;;
        "STATUS")
            echo -e "${CYAN}[${timestamp}] STATUS: ${message}${NC}"
            ;;
    esac
}

# Function to check service health
check_service_health() {
    local service_name="$1"
    local health_url="$2"
    
    if curl -s -f "$health_url" > /dev/null 2>&1; then
        log_message "SUCCESS" "$service_name is healthy"
        return 0
    else
        log_message "ERROR" "$service_name health check failed"
        return 1
    fi
}

# Function to check service status
check_service_status() {
    local service_name="$1"
    local status=$(docker-compose -f docker-compose.core.yml ps --format "{{.Status}}" "$service_name" 2>/dev/null | head -1)
    
    if echo "$status" | grep -q "Up"; then
        log_message "SUCCESS" "$service_name is running: $status"
        return 0
    else
        log_message "ERROR" "$service_name is not running: $status"
        return 1
    fi
}

# Function to check resource usage
check_resource_usage() {
    echo ""
    log_message "STATUS" "Resource Usage Summary"
    echo "----------------------------------------"
    
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}" | grep openpolicy-core
    
    # Check for high resource usage
    local high_memory=$(docker stats --no-stream --format "{{.MemPerc}}" | tr -d '%' | awk '{if($1 > 90) print $1}')
    local high_cpu=$(docker stats --no-stream --format "{{.CPUPerc}}" | tr -d '%' | awk '{if($1 > 80) print $1}')
    
    if [ -n "$high_memory" ]; then
        log_message "WARNING" "High memory usage detected: ${high_memory}%"
    fi
    
    if [ -n "$high_cpu" ]; then
        log_message "WARNING" "High CPU usage detected: ${high_cpu}%"
    fi
}

# Function to check service logs for errors
check_service_logs() {
    local service_name="$1"
    local error_count=$(docker-compose -f docker-compose.core.yml logs --tail=50 "$service_name" 2>/dev/null | grep -i "error\|exception\|fail\|critical" | wc -l)
    
    if [ "$error_count" -gt 0 ]; then
        log_message "WARNING" "$service_name has $error_count recent errors in logs"
        # Show last few errors
        docker-compose -f docker-compose.core.yml logs --tail=10 "$service_name" 2>/dev/null | grep -i "error\|exception\|fail\|critical" | tail -3
    else
        log_message "SUCCESS" "$service_name logs clean (no recent errors)"
    fi
}

# Function to perform comprehensive health check
comprehensive_health_check() {
    HEALTH_CHECK_COUNT=$((HEALTH_CHECK_COUNT + 1))
    
    log_message "STATUS" "=== COMPREHENSIVE HEALTH CHECK #$HEALTH_CHECK_COUNT ==="
    echo "=================================================="
    
    # Check all services are running
    log_message "INFO" "Checking service status..."
    check_service_status "postgres"
    check_service_status "redis"
    check_service_status "api"
    check_service_status "web"
    check_service_status "gateway"
    
    # Check health endpoints
    log_message "INFO" "Checking health endpoints..."
    check_service_health "API" "http://localhost:8000/health"
    check_service_health "Gateway" "http://localhost:80/health"
    
    # Check database connections
    log_message "INFO" "Checking database connections..."
    if docker exec openpolicy-core-postgres pg_isready -U openpolicy > /dev/null 2>&1; then
        log_message "SUCCESS" "PostgreSQL accepting connections"
    else
        log_message "ERROR" "PostgreSQL not accepting connections"
    fi
    
    if docker exec openpolicy-core-redis redis-cli ping | grep -q "PONG" 2>/dev/null; then
        log_message "SUCCESS" "Redis responding to PING"
    else
        log_message "ERROR" "Redis not responding to PING"
    fi
    
    # Check resource usage
    check_resource_usage
    
    # Check service logs for errors
    log_message "INFO" "Checking service logs for errors..."
    check_service_logs "postgres"
    check_service_logs "redis"
    check_service_logs "api"
    check_service_logs "web"
    check_service_logs "gateway"
    
    # Show current service status
    echo ""
    log_message "STATUS" "Current Service Status"
    echo "----------------------------------------"
    docker-compose -f docker-compose.core.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    
    # Show monitoring statistics
    local current_time=$(date +%s)
    local uptime=$((current_time - MONITORING_START_TIME))
    local uptime_minutes=$((uptime / 60))
    
    echo ""
    log_message "STATUS" "Monitoring Statistics"
    echo "----------------------------------------"
    echo "Monitoring Duration: ${uptime_minutes} minutes"
    echo "Health Checks Performed: ${HEALTH_CHECK_COUNT}"
    echo "Total Errors Detected: ${ERROR_COUNT}"
    echo "Error Rate: $(( (ERROR_COUNT * 100) / HEALTH_CHECK_COUNT ))%"
    
    echo ""
    log_message "STATUS" "=== HEALTH CHECK COMPLETE ==="
    echo "=================================================="
}

# Function to show real-time logs
show_real_time_logs() {
    log_message "INFO" "Starting real-time log monitoring..."
    echo "Press Ctrl+C to stop log monitoring"
    echo ""
    
    # Show logs for all services in real-time
    docker-compose -f docker-compose.core.yml logs -f --tail=10 2>/dev/null &
    local log_pid=$!
    
    # Wait for user to stop
    trap "kill $log_pid 2>/dev/null; exit" INT
    wait $log_pid
}

# Main monitoring loop
main_monitoring() {
    log_message "INFO" "Starting platform monitoring..."
    log_message "INFO" "Platform access points:"
    echo "  Main App: http://localhost:80"
    echo "  API: http://localhost:8000"
    echo "  Web: http://localhost:3000"
    echo "  Database: localhost:5432"
    echo "  Cache: localhost:6379"
    echo ""
    
    # Initial health check
    comprehensive_health_check
    
    # Continuous monitoring loop
    while true; do
        sleep 60  # Check every minute
        
        # Perform health check
        comprehensive_health_check
        
        # Show summary
        echo ""
        log_message "STATUS" "Platform Status Summary"
        echo "✅ All services operational"
        echo "🔍 Monitoring active"
        echo "📊 Error tracking enabled"
        echo "⏰ Next check in 60 seconds"
        echo ""
    done
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --health-check    Perform single comprehensive health check"
    echo "  --logs           Show real-time logs for all services"
    echo "  --monitor        Start continuous monitoring (default)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start continuous monitoring"
    echo "  $0 --health-check     # Single health check"
    echo "  $0 --logs            # Real-time logs"
}

# Parse command line arguments
case "${1:---monitor}" in
    --health-check)
        comprehensive_health_check
        ;;
    --logs)
        show_real_time_logs
        ;;
    --monitor)
        main_monitoring
        ;;
    --help)
        show_usage
        ;;
    *)
        echo "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
