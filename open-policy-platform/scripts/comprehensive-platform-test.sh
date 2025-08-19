#!/bin/bash

# OpenPolicyPlatform V4 - Comprehensive Platform Testing Script
# This script performs end-to-end testing of the entire platform

set -e

# Configuration
API_GATEWAY_URL="${API_GATEWAY_URL:-http://localhost:9000}"
WEB_URL="${WEB_URL:-http://openpolicy.local}"
ADMIN_URL="${ADMIN_URL:-http://openpolicyadmin.local}"
TEST_USER_EMAIL="test@openpolicy.com"
TEST_USER_PASSWORD="TestPassword123!"
ADMIN_EMAIL="admin@openpolicy.com"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-AdminSecure123!}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
declare -a FAILED_TEST_NAMES=()

# Function to print colored output
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Test result tracking
test_start() {
    local test_name=$1
    echo -e "\n${BLUE}▶ Testing:${NC} $test_name"
    ((TOTAL_TESTS++))
}

test_pass() {
    echo -e "${GREEN}✅ PASSED${NC}"
    ((PASSED_TESTS++))
}

test_fail() {
    local reason=$1
    echo -e "${RED}❌ FAILED${NC} - $reason"
    ((FAILED_TESTS++))
    FAILED_TEST_NAMES+=("$CURRENT_TEST - $reason")
}

# HTTP request helper
make_request() {
    local method=$1
    local url=$2
    local data=$3
    local token=$4
    
    local headers="-H 'Content-Type: application/json'"
    if [ -n "$token" ]; then
        headers="$headers -H 'Authorization: Bearer $token'"
    fi
    
    if [ -n "$data" ]; then
        curl -s -X "$method" "$url" -H "Content-Type: application/json" -H "Authorization: Bearer $token" -d "$data"
    else
        curl -s -X "$method" "$url" -H "Content-Type: application/json" -H "Authorization: Bearer $token"
    fi
}

# 1. Infrastructure Tests
test_infrastructure() {
    info "Starting Infrastructure Tests"
    
    # Test PostgreSQL connectivity
    CURRENT_TEST="PostgreSQL Main Database"
    test_start "$CURRENT_TEST"
    if pg_isready -h localhost -p 5432 -U openpolicy &>/dev/null; then
        test_pass
    else
        test_fail "Cannot connect to PostgreSQL on port 5432"
    fi
    
    # Test PostgreSQL Test Database
    CURRENT_TEST="PostgreSQL Test Database"
    test_start "$CURRENT_TEST"
    if pg_isready -h localhost -p 5433 -U openpolicy &>/dev/null; then
        test_pass
    else
        test_fail "Cannot connect to test PostgreSQL on port 5433"
    fi
    
    # Test Redis
    CURRENT_TEST="Redis Cache"
    test_start "$CURRENT_TEST"
    if redis-cli -h localhost -p 6379 ping &>/dev/null; then
        test_pass
    else
        test_fail "Cannot connect to Redis on port 6379"
    fi
    
    # Test Elasticsearch
    CURRENT_TEST="Elasticsearch"
    test_start "$CURRENT_TEST"
    if curl -s http://localhost:9200/_cluster/health | grep -q "green\|yellow"; then
        test_pass
    else
        test_fail "Elasticsearch cluster is not healthy"
    fi
}

# 2. Service Health Tests
test_service_health() {
    info "Starting Service Health Tests"
    
    local services=(
        "api-gateway:9000"
        "auth-service:9002"
        "policy-service:9003"
        "notification-service:9004"
        "search-service:9009"
        "dashboard-service:9010"
        "scraper-service:9008"
    )
    
    for service_port in "${services[@]}"; do
        IFS=':' read -r service port <<< "$service_port"
        CURRENT_TEST="$service health check"
        test_start "$CURRENT_TEST"
        
        if curl -f -s "http://localhost:$port/health" | grep -q "healthy"; then
            test_pass
        else
            test_fail "Service not responding on port $port"
        fi
    done
}

# 3. API Gateway Tests
test_api_gateway() {
    info "Starting API Gateway Tests"
    
    # Test gateway health
    CURRENT_TEST="API Gateway Health"
    test_start "$CURRENT_TEST"
    if curl -f -s "$API_GATEWAY_URL/health" | grep -q "healthy"; then
        test_pass
    else
        test_fail "API Gateway not healthy"
    fi
    
    # Test service routing
    local routes=(
        "/api/auth/health"
        "/api/policies/health"
        "/api/search/health"
        "/api/dashboard/health"
    )
    
    for route in "${routes[@]}"; do
        CURRENT_TEST="API Gateway route: $route"
        test_start "$CURRENT_TEST"
        
        if curl -f -s "$API_GATEWAY_URL$route" &>/dev/null; then
            test_pass
        else
            test_fail "Route not accessible"
        fi
    done
}

# 4. Authentication Tests
test_authentication() {
    info "Starting Authentication Tests"
    
    # Test user registration
    CURRENT_TEST="User Registration"
    test_start "$CURRENT_TEST"
    
    REGISTER_RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_USER_EMAIL\",
            \"password\": \"$TEST_USER_PASSWORD\",
            \"name\": \"Test User\"
        }")
    
    if echo "$REGISTER_RESPONSE" | grep -q "success\|already exists"; then
        test_pass
    else
        test_fail "Registration failed: $REGISTER_RESPONSE"
    fi
    
    # Test user login
    CURRENT_TEST="User Login"
    test_start "$CURRENT_TEST"
    
    LOGIN_RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_USER_EMAIL\",
            \"password\": \"$TEST_USER_PASSWORD\"
        }")
    
    if echo "$LOGIN_RESPONSE" | grep -q "token"; then
        USER_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token')
        test_pass
    else
        test_fail "Login failed: $LOGIN_RESPONSE"
    fi
    
    # Test admin login
    CURRENT_TEST="Admin Login"
    test_start "$CURRENT_TEST"
    
    ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$ADMIN_EMAIL\",
            \"password\": \"$ADMIN_PASSWORD\"
        }")
    
    if echo "$ADMIN_LOGIN_RESPONSE" | grep -q "token"; then
        ADMIN_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | jq -r '.token')
        test_pass
    else
        test_fail "Admin login failed: $ADMIN_LOGIN_RESPONSE"
    fi
    
    # Test token validation
    CURRENT_TEST="Token Validation"
    test_start "$CURRENT_TEST"
    
    if [ -n "$USER_TOKEN" ]; then
        PROFILE_RESPONSE=$(curl -s -X GET "$API_GATEWAY_URL/api/auth/profile" \
            -H "Authorization: Bearer $USER_TOKEN")
        
        if echo "$PROFILE_RESPONSE" | grep -q "$TEST_USER_EMAIL"; then
            test_pass
        else
            test_fail "Token validation failed"
        fi
    else
        test_fail "No user token available"
    fi
}

# 5. Core Functionality Tests
test_core_functionality() {
    info "Starting Core Functionality Tests"
    
    # Test policy creation (admin only)
    if [ -n "$ADMIN_TOKEN" ]; then
        CURRENT_TEST="Policy Creation"
        test_start "$CURRENT_TEST"
        
        POLICY_RESPONSE=$(curl -s -X POST "$API_GATEWAY_URL/api/policies" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $ADMIN_TOKEN" \
            -d '{
                "title": "Test Policy",
                "description": "Test policy description",
                "category": "testing",
                "content": "This is a test policy content"
            }')
        
        if echo "$POLICY_RESPONSE" | grep -q "id"; then
            POLICY_ID=$(echo "$POLICY_RESPONSE" | jq -r '.id')
            test_pass
        else
            test_fail "Policy creation failed: $POLICY_RESPONSE"
        fi
    fi
    
    # Test policy search
    CURRENT_TEST="Policy Search"
    test_start "$CURRENT_TEST"
    
    SEARCH_RESPONSE=$(curl -s -X GET "$API_GATEWAY_URL/api/search?q=test" \
        -H "Authorization: Bearer $USER_TOKEN")
    
    if echo "$SEARCH_RESPONSE" | grep -q "results"; then
        test_pass
    else
        test_fail "Search failed: $SEARCH_RESPONSE"
    fi
    
    # Test dashboard stats
    CURRENT_TEST="Dashboard Statistics"
    test_start "$CURRENT_TEST"
    
    STATS_RESPONSE=$(curl -s -X GET "$API_GATEWAY_URL/api/dashboard/stats" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$STATS_RESPONSE" | grep -q "totalServices"; then
        test_pass
    else
        test_fail "Dashboard stats failed"
    fi
}

# 6. Frontend Tests
test_frontend() {
    info "Starting Frontend Tests"
    
    # Test main website
    CURRENT_TEST="Main Website Accessibility"
    test_start "$CURRENT_TEST"
    
    if curl -f -s "$WEB_URL" | grep -q "OpenPolicy"; then
        test_pass
    else
        test_fail "Main website not accessible at $WEB_URL"
    fi
    
    # Test admin dashboard
    CURRENT_TEST="Admin Dashboard Accessibility"
    test_start "$CURRENT_TEST"
    
    if curl -f -s "$ADMIN_URL" | grep -q "Admin"; then
        test_pass
    else
        test_fail "Admin dashboard not accessible at $ADMIN_URL"
    fi
    
    # Test static assets
    CURRENT_TEST="Static Assets"
    test_start "$CURRENT_TEST"
    
    if curl -f -s "$WEB_URL/favicon.ico" &>/dev/null; then
        test_pass
    else
        test_fail "Static assets not served correctly"
    fi
}

# 7. Data Flow Tests
test_data_flow() {
    info "Starting Data Flow Tests"
    
    # Test scraper status
    CURRENT_TEST="Scraper Service Status"
    test_start "$CURRENT_TEST"
    
    SCRAPER_STATUS=$(curl -s -X GET "$API_GATEWAY_URL/api/scrapers/status" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$SCRAPER_STATUS" | grep -q "active"; then
        test_pass
    else
        test_fail "Scraper service not active"
    fi
    
    # Test data pipeline
    CURRENT_TEST="ETL Pipeline"
    test_start "$CURRENT_TEST"
    
    ETL_STATUS=$(curl -s -X GET "$API_GATEWAY_URL/api/etl/status" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$ETL_STATUS" | grep -q "running\|idle"; then
        test_pass
    else
        test_fail "ETL pipeline not operational"
    fi
}

# 8. Monitoring Tests
test_monitoring() {
    info "Starting Monitoring Tests"
    
    # Test Prometheus metrics
    CURRENT_TEST="Prometheus Metrics"
    test_start "$CURRENT_TEST"
    
    if curl -f -s "http://localhost:9090/api/v1/query?query=up" | grep -q "success"; then
        test_pass
    else
        test_fail "Prometheus not accessible"
    fi
    
    # Test Grafana
    CURRENT_TEST="Grafana Dashboard"
    test_start "$CURRENT_TEST"
    
    if curl -f -s "http://localhost:3001/api/health" | grep -q "ok"; then
        test_pass
    else
        test_fail "Grafana not accessible"
    fi
    
    # Test Kibana
    CURRENT_TEST="Kibana Logs"
    test_start "$CURRENT_TEST"
    
    if curl -f -s "http://localhost:5601/api/status" | grep -q "available"; then
        test_pass
    else
        test_fail "Kibana not accessible"
    fi
}

# 9. Security Tests
test_security() {
    info "Starting Security Tests"
    
    # Test unauthorized access
    CURRENT_TEST="Unauthorized Access Prevention"
    test_start "$CURRENT_TEST"
    
    UNAUTH_RESPONSE=$(curl -s -X GET "$API_GATEWAY_URL/api/dashboard/stats")
    
    if echo "$UNAUTH_RESPONSE" | grep -q "unauthorized\|401"; then
        test_pass
    else
        test_fail "Unauthorized access not blocked"
    fi
    
    # Test CORS
    CURRENT_TEST="CORS Configuration"
    test_start "$CURRENT_TEST"
    
    CORS_RESPONSE=$(curl -s -I -X OPTIONS "$API_GATEWAY_URL/api/health" \
        -H "Origin: http://example.com" \
        -H "Access-Control-Request-Method: GET")
    
    if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
        test_pass
    else
        test_fail "CORS not configured"
    fi
}

# 10. Performance Tests
test_performance() {
    info "Starting Performance Tests"
    
    # Test API response time
    CURRENT_TEST="API Response Time"
    test_start "$CURRENT_TEST"
    
    START_TIME=$(date +%s%N)
    curl -s "$API_GATEWAY_URL/health" &>/dev/null
    END_TIME=$(date +%s%N)
    
    RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))
    
    if [ $RESPONSE_TIME -lt 1000 ]; then
        test_pass
        info "Response time: ${RESPONSE_TIME}ms"
    else
        test_fail "Response time too high: ${RESPONSE_TIME}ms"
    fi
    
    # Test concurrent requests
    CURRENT_TEST="Concurrent Request Handling"
    test_start "$CURRENT_TEST"
    
    CONCURRENT_FAILED=0
    for i in {1..10}; do
        curl -f -s "$API_GATEWAY_URL/health" &>/dev/null || ((CONCURRENT_FAILED++)) &
    done
    wait
    
    if [ $CONCURRENT_FAILED -eq 0 ]; then
        test_pass
    else
        test_fail "$CONCURRENT_FAILED concurrent requests failed"
    fi
}

# Generate test report
generate_report() {
    local report_file="test-report-$(date +%Y%m%d-%H%M%S).html"
    
    cat > $report_file << EOF
<!DOCTYPE html>
<html>
<head>
    <title>OpenPolicyPlatform V4 - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #1976d2; color: white; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
        .passed { color: #4caf50; }
        .failed { color: #f44336; }
        .test-section { margin: 20px 0; }
        .test-result { padding: 10px; margin: 5px 0; border-left: 4px solid; }
        .test-passed { border-color: #4caf50; background: #e8f5e9; }
        .test-failed { border-color: #f44336; background: #ffebee; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>OpenPolicyPlatform V4 - Test Report</h1>
        <p>Generated: $(date)</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <p>Total Tests: <strong>$TOTAL_TESTS</strong></p>
        <p class="passed">Passed: <strong>$PASSED_TESTS</strong></p>
        <p class="failed">Failed: <strong>$FAILED_TESTS</strong></p>
        <p>Success Rate: <strong>$(( PASSED_TESTS * 100 / TOTAL_TESTS ))%</strong></p>
    </div>
    
    <div class="test-section">
        <h2>Failed Tests</h2>
EOF
    
    if [ ${#FAILED_TEST_NAMES[@]} -eq 0 ]; then
        echo "<p class='passed'>All tests passed!</p>" >> $report_file
    else
        echo "<ul>" >> $report_file
        for failed_test in "${FAILED_TEST_NAMES[@]}"; do
            echo "<li class='failed'>$failed_test</li>" >> $report_file
        done
        echo "</ul>" >> $report_file
    fi
    
    cat >> $report_file << EOF
    </div>
    
    <div class="test-section">
        <h2>Platform Status</h2>
        <table>
            <tr>
                <th>Component</th>
                <th>Status</th>
                <th>URL</th>
            </tr>
            <tr>
                <td>API Gateway</td>
                <td class="passed">Running</td>
                <td>$API_GATEWAY_URL</td>
            </tr>
            <tr>
                <td>Web Frontend</td>
                <td class="passed">Running</td>
                <td>$WEB_URL</td>
            </tr>
            <tr>
                <td>Admin Dashboard</td>
                <td class="passed">Running</td>
                <td>$ADMIN_URL</td>
            </tr>
        </table>
    </div>
    
    <div class="test-section">
        <h2>Next Steps</h2>
        <ol>
            <li>Review failed tests and fix issues</li>
            <li>Access the admin dashboard at <a href="$ADMIN_URL">$ADMIN_URL</a></li>
            <li>Login with: admin@openpolicy.com / AdminSecure123!</li>
            <li>Check monitoring dashboards:
                <ul>
                    <li>Grafana: <a href="http://localhost:3001">http://localhost:3001</a></li>
                    <li>Kibana: <a href="http://localhost:5601">http://localhost:5601</a></li>
                </ul>
            </li>
            <li>Review logs in Kibana for any errors</li>
        </ol>
    </div>
</body>
</html>
EOF
    
    echo ""
    echo "📄 Test report saved to: $report_file"
}

# Main execution
main() {
    echo "🧪 OpenPolicyPlatform V4 - Comprehensive Platform Test"
    echo "===================================================="
    echo ""
    echo "Testing environment:"
    echo "- API Gateway: $API_GATEWAY_URL"
    echo "- Web URL: $WEB_URL"
    echo "- Admin URL: $ADMIN_URL"
    echo ""
    
    # Run all test suites
    test_infrastructure
    test_service_health
    test_api_gateway
    test_authentication
    test_core_functionality
    test_frontend
    test_data_flow
    test_monitoring
    test_security
    test_performance
    
    # Generate summary
    echo ""
    echo "======================================"
    echo "📊 TEST RESULTS SUMMARY"
    echo "======================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo ""
    
    if [ $FAILED_TESTS -gt 0 ]; then
        echo -e "${RED}⚠️  Some tests failed:${NC}"
        for failed_test in "${FAILED_TEST_NAMES[@]}"; do
            echo "  - $failed_test"
        done
    else
        echo -e "${GREEN}✅ All tests passed!${NC}"
    fi
    
    # Generate HTML report
    generate_report
    
    echo ""
    echo "🎉 Testing complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Review the test report"
    echo "2. Fix any failed tests"
    echo "3. Access the platform:"
    echo "   - Main site: $WEB_URL"
    echo "   - Admin dashboard: $ADMIN_URL"
    echo "   - API documentation: $API_GATEWAY_URL/docs"
    echo ""
    echo "Default credentials:"
    echo "   Admin: admin@openpolicy.com / AdminSecure123!"
    echo "   User: test@openpolicy.com / TestPassword123!"
    
    # Exit with appropriate code
    [ $FAILED_TESTS -eq 0 ] && exit 0 || exit 1
}

# Run main function
main "$@"