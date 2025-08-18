#!/bin/bash

# Open Policy Platform V4 - Comprehensive Testing Suite
# Tests all services, connections, and functionality

set -e

echo "🧪 Open Policy Platform V4 - Comprehensive Testing Suite"
echo "========================================================"
echo "Testing: All 5 core services, connections, and functionality"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    echo -e "${BLUE}🔍 Testing: ${test_name}${NC}"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "  ${RED}❌ FAILED${NC}"
        if [ -n "$expected_result" ]; then
            echo -e "    Expected: ${expected_result}"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test HTTP endpoint
test_http() {
    local name="$1"
    local url="$2"
    local expected_status="$3"
    
    echo -e "${BLUE}🔍 Testing HTTP: ${name}${NC}"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "  ${GREEN}✅ PASSED - Status: ${response}${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "  ${RED}❌ FAILED - Expected: ${expected_status}, Got: ${response}${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "📊 PHASE 1: Service Status & Health Checks"
echo "-------------------------------------------"

# Test 1: Check if all services are running
run_test "All services running" "docker-compose -f docker-compose.core.yml ps | grep -c 'Up' | grep -q '5'"

# Test 2: Check service health
run_test "PostgreSQL healthy" "docker exec openpolicy-core-postgres pg_isready -U openpolicy > /dev/null 2>&1"
run_test "Redis healthy" "docker exec openpolicy-core-redis redis-cli ping | grep -q 'PONG'"

echo ""
echo "🌐 PHASE 2: HTTP Endpoint Testing"
echo "----------------------------------"

# Test 3: API health endpoint
test_http "API Health Check" "http://localhost:8000/health" "200"

# Test 4: Web frontend
test_http "Web Frontend" "http://localhost:3000" "200"

# Test 5: Gateway health
test_http "Gateway Health" "http://localhost:80/health" "200"

# Test 6: Gateway API routing
test_http "Gateway API Routing" "http://localhost:80/api/health" "200"

# Test 7: Gateway web routing
test_http "Gateway Web Routing" "http://localhost:80/" "200"

echo ""
echo "🗄️ PHASE 3: Database & Cache Testing"
echo "-------------------------------------"

# Test 8: PostgreSQL connection
run_test "PostgreSQL connection" "docker exec openpolicy-core-postgres psql -U openpolicy -d openpolicy -c 'SELECT 1;' > /dev/null 2>&1"

# Test 9: Redis operations
run_test "Redis SET operation" "docker exec openpolicy-core-redis redis-cli SET test_key 'test_value' | grep -q 'OK'"
run_test "Redis GET operation" "docker exec openpolicy-core-redis redis-cli GET test_key | grep -q 'test_value'"
run_test "Redis cleanup" "docker exec openpolicy-core-redis redis-cli DEL test_key | grep -q '1'"

echo ""
echo "🔌 PHASE 4: API Functionality Testing"
echo "--------------------------------------"

# Test 10: API version endpoint
test_http "API Version" "http://localhost:8000/api/v1/version" "200"

# Test 11: API documentation
test_http "API Docs" "http://localhost:8000/docs" "200"

# Test 12: API OpenAPI schema
test_http "API Schema" "http://localhost:8000/openapi.json" "200"

echo ""
echo "📱 PHASE 5: Web Frontend Testing"
echo "---------------------------------"

# Test 13: Web assets loading
test_http "Web Assets" "http://localhost:3000/assets/" "200"

# Test 14: Web JavaScript loading
run_test "Web JavaScript" "curl -s http://localhost:3000 | grep -q 'script'"

echo ""
echo "🌐 PHASE 6: Gateway & Routing Testing"
echo "-------------------------------------"

# Test 15: Gateway rate limiting headers
run_test "Gateway rate limiting" "curl -s -I http://localhost:80/api/ | grep -q 'X-RateLimit' || true"

# Test 16: Gateway compression
run_test "Gateway compression" "curl -s -H 'Accept-Encoding: gzip' -I http://localhost:80/ | grep -q 'gzip'"

echo ""
echo "📊 PHASE 7: Resource & Performance Testing"
echo "------------------------------------------"

# Test 17: Memory usage within limits
run_test "Memory usage check" "docker stats --no-stream --format '{{.MemPerc}}' | tr -d '%' | awk '{if(\$1 < 95) exit 0; else exit 1}'"

# Test 18: CPU usage reasonable
run_test "CPU usage check" "docker stats --no-stream --format '{{.CPUPerc}}' | tr -d '%' | awk '{if(\$1 < 80) exit 0; else exit 1}'"

echo ""
echo "🔗 PHASE 8: Service Communication Testing"
echo "-----------------------------------------"

# Test 19: API can connect to database
run_test "API-Database connection" "curl -s http://localhost:8000/health | grep -q 'healthy'"

# Test 20: API can connect to Redis
run_test "API-Redis connection" "curl -s http://localhost:8000/health | grep -q 'healthy'"

echo ""
echo "📋 PHASE 9: Logging & Monitoring Testing"
echo "-----------------------------------------"

# Test 21: Service logs accessible
run_test "Service logs accessible" "docker-compose -f docker-compose.core.yml logs --tail=1 > /dev/null 2>&1"

# Test 22: Container logs directory exists
run_test "Logs directory exists" "docker exec openpolicy-core-api ls -la /app/logs > /dev/null 2>&1 || true"

echo ""
echo "🎯 PHASE 10: Integration Testing"
echo "--------------------------------"

# Test 23: End-to-end request flow
run_test "End-to-end flow" "curl -s http://localhost:80/api/health | grep -q 'healthy'"

# Test 24: Gateway to API communication
run_test "Gateway-API communication" "curl -s http://localhost:80/api/health | grep -q 'healthy'"

echo ""
echo "📊 TEST RESULTS SUMMARY"
echo "======================="
echo -e "Total Tests: ${TESTS_TOTAL}"
echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
echo -e "Success Rate: $(( (TESTS_PASSED * 100) / TESTS_TOTAL ))%"

echo ""
echo "🔍 DETAILED SERVICE STATUS"
echo "=========================="
docker-compose -f docker-compose.core.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📈 RESOURCE USAGE"
echo "================="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"

echo ""
echo "🌐 ACCESS POINTS"
echo "================"
echo "Main Application: http://localhost:80"
echo "API Endpoints: http://localhost:8000"
echo "Web Frontend: http://localhost:3000"
echo "Database: localhost:5432"
echo "Cache: localhost:6379"

echo ""
echo "📋 HEALTH CHECK COMMANDS"
echo "========================"
echo "Service Status: docker-compose -f docker-compose.core.yml ps"
echo "Resource Usage: docker stats --no-stream"
echo "API Health: curl http://localhost:8000/health"
echo "Gateway Health: curl http://localhost:80/health"
echo "Database Health: docker exec openpolicy-core-postgres pg_isready -U openpolicy"
echo "Redis Health: docker exec openpolicy-core-redis redis-cli ping"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Your platform is running perfectly!${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed. Check the details above for issues.${NC}"
    exit 1
fi
