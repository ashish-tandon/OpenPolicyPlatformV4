#!/bin/bash

# OpenPolicy Platform Monitoring Script
# This script monitors the health of all services

set -e

echo "🔍 OpenPolicy Platform Health Monitor"
echo "===================================="
echo ""

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ $name: HEALTHY"
    else
        echo "❌ $name: UNHEALTHY"
    fi
}

# Function to get container stats
get_container_stats() {
    echo ""
    echo "📊 Container Resource Usage:"
    echo "----------------------------"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep openpolicy || true
}

# Function to check database
check_database() {
    echo ""
    echo "🗄️  Database Status:"
    echo "-------------------"
    docker-compose exec -T postgres pg_isready -U openpolicy || echo "❌ Database is not responding"
    
    # Get table counts
    docker-compose exec -T postgres psql -U openpolicy -d openpolicy -c "
        SELECT 
            'Bills' as table_name, COUNT(*) as count FROM bills
        UNION ALL
        SELECT 'Representatives', COUNT(*) FROM representatives
        UNION ALL
        SELECT 'Votes', COUNT(*) FROM parliament_votes
        UNION ALL
        SELECT 'Committees', COUNT(*) FROM committees
        UNION ALL
        SELECT 'Users', COUNT(*) FROM users;
    " 2>/dev/null || echo "Unable to query database"
}

# Function to check Redis
check_redis() {
    echo ""
    echo "💾 Redis Status:"
    echo "----------------"
    docker-compose exec -T redis redis-cli ping || echo "❌ Redis is not responding"
    docker-compose exec -T redis redis-cli info clients | grep connected_clients || true
}

# Function to check scrapers
check_scrapers() {
    echo ""
    echo "🤖 Scraper Status:"
    echo "------------------"
    
    # Check if scraper container is running
    if docker-compose ps scraper | grep -q "Up"; then
        echo "✅ Scraper container is running"
        
        # Get last scraper runs from database
        docker-compose exec -T postgres psql -U openpolicy -d openpolicy -c "
            SELECT 
                scraper_name,
                status,
                last_run,
                records_scraped
            FROM scraper_status
            ORDER BY last_run DESC
            LIMIT 5;
        " 2>/dev/null || echo "No scraper status available"
    else
        echo "❌ Scraper container is not running"
    fi
}

# Main monitoring loop
while true; do
    clear
    
    echo "🔍 OpenPolicy Platform Health Monitor"
    echo "===================================="
    echo "🕐 $(date)"
    echo ""
    
    echo "🌐 Service Health Checks:"
    echo "------------------------"
    check_service "Nginx Gateway" "http://localhost:80/api/v1/health"
    check_service "API Service" "http://localhost:8000/api/v1/health"
    check_service "Web Application" "http://localhost:3000"
    check_service "Admin Dashboard" "http://localhost:3001"
    
    get_container_stats
    check_database
    check_redis
    check_scrapers
    
    echo ""
    echo "📝 Recent Logs (last 5 lines):"
    echo "------------------------------"
    docker-compose logs --tail=5 api 2>/dev/null | tail -5 || echo "No recent API logs"
    
    echo ""
    echo "Press Ctrl+C to exit. Refreshing in 30 seconds..."
    
    # Break if not in continuous mode
    if [ "$1" != "--continuous" ]; then
        break
    fi
    
    sleep 30
done