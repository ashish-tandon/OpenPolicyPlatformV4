#!/bin/bash

# OpenPolicy Platform Test Script
# This script tests all platform functionality

set -e

echo "🧪 OpenPolicy Platform Test Suite"
echo "================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local auth_token=$4
    
    echo -n "Testing $name... "
    
    if [ -n "$auth_token" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $auth_token" "$url" || true)
    else
        response=$(curl -s -w "\n%{http_code}" "$url" || true)
    fi
    
    status_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (Status: $status_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected: $expected_status, Got: $status_code)"
        echo "  Response: ${body:0:100}..."
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test authentication
test_auth() {
    echo ""
    echo "🔐 Testing Authentication..."
    echo "----------------------------"
    
    # Test login
    echo -n "Testing login endpoint... "
    response=$(curl -s -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=user@example.com&password=user123" \
        "http://localhost/api/v1/auth/login" || true)
    
    if echo "$response" | grep -q "access_token"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        # Extract token for further tests
        AUTH_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        export AUTH_TOKEN
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Response: $response"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        AUTH_TOKEN=""
    fi
    
    # Test getting current user
    if [ -n "$AUTH_TOKEN" ]; then
        test_endpoint "Get current user" "http://localhost/api/v1/auth/me" 200 "$AUTH_TOKEN"
    fi
}

# Function to test data endpoints
test_data_endpoints() {
    echo ""
    echo "📊 Testing Data Endpoints..."
    echo "----------------------------"
    
    test_endpoint "Bills list" "http://localhost/api/v1/bills"
    test_endpoint "Representatives list" "http://localhost/api/v1/representatives"
    test_endpoint "Votes list" "http://localhost/api/v1/votes"
    test_endpoint "Committees list" "http://localhost/api/v1/committees"
    test_endpoint "Search" "http://localhost/api/v1/search?q=parliament"
}

# Function to test admin endpoints
test_admin_endpoints() {
    echo ""
    echo "👨‍💼 Testing Admin Endpoints..."
    echo "------------------------------"
    
    # Login as admin
    echo -n "Testing admin login... "
    response=$(curl -s -X POST \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=admin@openpolicy.ca&password=admin123" \
        "http://localhost/api/v1/auth/login" || true)
    
    if echo "$response" | grep -q "access_token"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        ADMIN_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        
        # Test admin dashboard
        test_endpoint "Admin dashboard" "http://localhost/api/v1/admin/dashboard" 200 "$ADMIN_TOKEN"
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test database connectivity
test_database() {
    echo ""
    echo "🗄️  Testing Database..."
    echo "----------------------"
    
    echo -n "Testing database connection... "
    if docker-compose exec -T postgres pg_isready -U openpolicy > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        
        # Test data exists
        echo -n "Testing data exists... "
        count=$(docker-compose exec -T postgres psql -U openpolicy -d openpolicy -t -c "SELECT COUNT(*) FROM bills;" 2>/dev/null | tr -d ' ')
        if [ "$count" -gt 0 ]; then
            echo -e "${GREEN}✓ PASSED${NC} ($count bills found)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${YELLOW}⚠ WARNING${NC} (No bills found - run scrapers)"
        fi
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test Redis
test_redis() {
    echo ""
    echo "💾 Testing Redis..."
    echo "-------------------"
    
    echo -n "Testing Redis connection... "
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to test scrapers
test_scrapers() {
    echo ""
    echo "🤖 Testing Scrapers..."
    echo "----------------------"
    
    echo -n "Testing scraper container... "
    if docker-compose ps scraper | grep -q "Up"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠ WARNING${NC} (Scraper not running)"
    fi
}

# Function to test web interfaces
test_web_interfaces() {
    echo ""
    echo "🌐 Testing Web Interfaces..."
    echo "-----------------------------"
    
    test_endpoint "Web application" "http://localhost:3000" 200
    test_endpoint "Admin dashboard" "http://localhost:3001" 200
}

# Function to run performance test
test_performance() {
    echo ""
    echo "⚡ Testing Performance..."
    echo "-------------------------"
    
    echo -n "Testing API response time... "
    start_time=$(date +%s%N)
    curl -s "http://localhost/api/v1/health" > /dev/null
    end_time=$(date +%s%N)
    response_time=$(( ($end_time - $start_time) / 1000000 ))
    
    if [ "$response_time" -lt 200 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (${response_time}ms)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠ WARNING${NC} (${response_time}ms - slower than 200ms target)"
    fi
}

# Main test execution
echo "🚀 Starting tests..."
echo ""

# Health checks
echo "💚 Testing Health Endpoints..."
echo "------------------------------"
test_endpoint "Gateway health" "http://localhost/api/v1/health"
test_endpoint "Detailed health" "http://localhost/api/v1/health/detailed"

# Run all test suites
test_auth
test_data_endpoints
test_admin_endpoints
test_database
test_redis
test_scrapers
test_web_interfaces
test_performance

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed! The platform is ready to use.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed. Please check the logs above.${NC}"
    exit 1
fi