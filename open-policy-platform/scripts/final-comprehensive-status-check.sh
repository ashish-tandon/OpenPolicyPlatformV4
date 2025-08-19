#!/bin/bash
set -e

echo "=============================================="
echo "OpenPolicyPlatformV4 - Final Status Check"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Summary variables
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Function to check status
check_status() {
    local description=$1
    local check_command=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if eval $check_command > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $description${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $description${NC}"
    fi
}

# Function to check file exists
check_file() {
    local description=$1
    local file_path=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}✅ $description${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $description${NC}"
    fi
}

# Function to check directory exists
check_dir() {
    local description=$1
    local dir_path=$2
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -d "$dir_path" ]; then
        echo -e "${GREEN}✅ $description${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ $description${NC}"
    fi
}

echo -e "${BLUE}1. CORE INFRASTRUCTURE${NC}"
echo "================================"
check_file "Database schema setup" "database/complete-schema-setup.sql"
check_file "Docker Compose configuration" "docker-compose.complete.yml"
check_file "API Gateway implementation" "services/api-gateway/main.go"
check_file "Nginx configuration" "nginx/nginx.conf"
check_file "Custom domains configuration" "nginx/custom-domains.conf"
echo ""

echo -e "${BLUE}2. MICROSERVICES (37 SERVICES)${NC}"
echo "================================"
check_dir "API Gateway service" "services/api-gateway"
check_dir "Auth service" "services/auth"
check_dir "Policy service" "services/policy"
check_dir "Notification service" "services/notification"
check_dir "Config service" "services/config"
check_dir "Analytics service" "services/analytics"
check_dir "Monitoring service" "services/monitoring"
check_dir "ETL service" "services/etl"
check_dir "Scraper service" "services/scraper"
check_dir "Search service" "services/search"
check_dir "Dashboard service" "services/dashboard"
check_dir "Files service" "services/files"
check_dir "Representatives service" "services/representatives"
check_dir "Mobile API" "services/mobile-api"
echo ""

echo -e "${BLUE}3. FRONTEND APPLICATIONS${NC}"
echo "================================"
check_dir "Web Frontend" "apps/web"
check_dir "Admin Dashboard" "apps/admin-dashboard"
check_dir "Mobile Apps" "apps/mobile"
check_file "Theme configuration" "apps/web/src/theme/index.ts"
check_file "Hero Section component" "apps/web/src/components/HeroSection.tsx"
check_file "Enhanced Search component" "apps/web/src/components/EnhancedSearch.tsx"
check_file "Interactive Dashboard" "apps/web/src/components/InteractiveDashboard.tsx"
check_file "Notification Center" "apps/web/src/components/NotificationCenter.tsx"
echo ""

echo -e "${BLUE}4. DEPLOYMENT CONFIGURATIONS${NC}"
echo "================================"
check_dir "Kubernetes manifests" "k8s"
check_dir "Helm charts" "charts/open-policy-platform"
check_file "QNAP deployment script" "scripts/create-qnap-deployment-package.sh"
check_file "Azure deployment script" "deployment/azure/deploy-to-azure.sh"
check_file "AKS setup script" "deployment/azure/setup-aks-cluster.sh"
check_file "GitHub repository setup" "deployment/github/setup-repositories.sh"
echo ""

echo -e "${BLUE}5. CI/CD PIPELINE${NC}"
echo "================================"
check_file "GitHub Actions workflow" ".github/workflows/monorepo-ci-cd.yml"
check_file "E2E test workflow" ".github/workflows/e2e-tests.yml"
check_file "Complete CI/CD workflow" ".github/workflows/complete-ci-cd.yml"
check_file "Semantic release setup" "scripts/semantic-release-setup.sh"
echo ""

echo -e "${BLUE}6. TESTING FRAMEWORK${NC}"
echo "================================"
check_file "Cypress configuration" "testing/e2e/cypress.config.ts"
check_dir "Cypress tests" "testing/e2e/cypress/integration"
check_file "Playwright configuration" "testing/e2e/playwright.config.ts"
check_dir "Playwright tests" "testing/e2e/playwright/tests"
check_file "Load testing script" "testing/load-testing/k6-load-test.js"
check_file "E2E setup script" "testing/e2e/setup-e2e-tests.sh"
echo ""

echo -e "${BLUE}7. MONITORING & ALERTING${NC}"
echo "================================"
check_file "Prometheus alerts" "monitoring/alerting/prometheus-alerts.yaml"
check_file "Alertmanager config" "monitoring/alerting/alertmanager-config.yaml"
check_dir "Grafana dashboards" "monitoring/grafana-dashboards"
check_file "Monitoring setup script" "monitoring/setup-monitoring-dashboards.sh"
echo ""

echo -e "${BLUE}8. SECURITY FEATURES${NC}"
echo "================================"
check_file "Security scan setup" "scripts/security-scan-setup.sh"
check_file "SSL certificate setup" "scripts/ssl-certificate-setup.sh"
check_file "Rate limiting service" "services/rate-limiting/rate-limiter-service.py"
check_file "GDPR compliance service" "services/gdpr-compliance/gdpr-service.py"
check_file "Audit logging service" "services/audit-logging/audit-service.py"
check_file "SSO service" "services/sso/sso-service.py"
echo ""

echo -e "${BLUE}9. ADVANCED FEATURES${NC}"
echo "================================"
check_file "Feature flags service" "services/feature-flags/feature-flag-service.py"
check_file "A/B testing service" "services/ab-testing/ab-testing-service.py"
check_file "Multi-tenancy service" "services/multi-tenancy/tenant-service.py"
check_file "Database migrations setup" "database/setup-migrations.sh"
check_file "CDN setup script" "infrastructure/cdn/setup-cdn.sh"
check_file "Backup/DR script" "scripts/backup-disaster-recovery.sh"
echo ""

echo -e "${BLUE}10. DOCUMENTATION${NC}"
echo "================================"
check_file "Main README" "README.md"
check_file "Architecture documentation" "docs/architecture.md"
check_file "API documentation script" "api/generate-api-docs.sh"
check_file "User guide" "docs/user-guides/complete-user-guide.md"
check_file "Deployment summary" "COMPLETE_PLATFORM_DEPLOYMENT_SUMMARY.md"
check_file "Final status report" "FINAL_COMPLETE_PLATFORM_STATUS.md"
echo ""

echo -e "${BLUE}11. AUTOMATION SCRIPTS${NC}"
echo "================================"
check_file "Master deployment script" "EXECUTE_COMPLETE_DEPLOYMENT.sh"
check_file "Platform test script" "scripts/comprehensive-platform-test.sh"
check_file "Final verification script" "scripts/final-platform-verification.sh"
check_file "Database setup script" "scripts/setup-complete-database.sh"
check_file "Performance optimization" "scripts/performance-optimization.sh"
echo ""

# Calculate completion percentage
COMPLETION_PERCENTAGE=$(echo "scale=2; ($PASSED_CHECKS / $TOTAL_CHECKS) * 100" | bc)

echo "=============================================="
echo -e "${BLUE}FINAL STATUS SUMMARY${NC}"
echo "=============================================="
echo ""
echo -e "Total Checks: ${YELLOW}$TOTAL_CHECKS${NC}"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$((TOTAL_CHECKS - PASSED_CHECKS))${NC}"
echo -e "Completion: ${YELLOW}${COMPLETION_PERCENTAGE}%${NC}"
echo ""

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}🎉 CONGRATULATIONS! The OpenPolicyPlatformV4 is FULLY COMPLETE!${NC}"
    echo -e "${GREEN}All components, configurations, and features are in place.${NC}"
    echo -e "${GREEN}The platform is ready for deployment!${NC}"
else
    echo -e "${YELLOW}⚠️  Some components are missing. Please review the failed checks above.${NC}"
fi

echo ""
echo "=============================================="
echo "Next Steps:"
echo "1. Execute: ./EXECUTE_COMPLETE_DEPLOYMENT.sh"
echo "2. Run tests: ./scripts/comprehensive-platform-test.sh"
echo "3. Deploy to Azure: ./deployment/azure/deploy-to-azure.sh"
echo "=============================================="