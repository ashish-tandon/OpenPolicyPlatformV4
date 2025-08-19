#!/bin/bash

# Final Platform Verification Script
# Comprehensive check of all components, deployments, and configurations

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Result counters
PASSED=0
FAILED=0
WARNINGS=0

# Results array
declare -a RESULTS

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    FAILED=$((FAILED + 1))
    RESULTS+=("❌ $1")
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
    RESULTS+=("⚠️  $1")
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    PASSED=$((PASSED + 1))
    RESULTS+=("✅ $1")
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}▶ $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check GitHub repositories
check_github_repos() {
    section "GitHub Repositories"
    
    REPOS=(
        "opp-api-gateway"
        "opp-auth-service"
        "opp-web-frontend"
        "opp-scrapers"
        "opp-docs"
        "opp-infrastructure"
    )
    
    for repo in "${REPOS[@]}"; do
        if gh repo view "openpolicy-platform/$repo" &> /dev/null; then
            success "Repository $repo exists"
            
            # Check for CI/CD workflow
            if gh workflow list -R "openpolicy-platform/$repo" | grep -q "CI/CD"; then
                success "CI/CD workflow configured for $repo"
            else
                error "No CI/CD workflow found for $repo"
            fi
        else
            error "Repository $repo not found"
        fi
    done
}

# Check Docker images
check_docker_images() {
    section "Docker Images"
    
    IMAGES=(
        "opp-api-gateway:latest"
        "opp-auth-service:latest"
        "opp-policy-service:latest"
        "opp-notification-service:latest"
        "opp-config-service:latest"
        "opp-search-service:latest"
        "opp-dashboard-service:latest"
        "opp-web:latest"
        "opp-admin-dashboard:latest"
    )
    
    for image in "${IMAGES[@]}"; do
        if docker image inspect "$image" &> /dev/null; then
            success "Docker image $image exists"
        else
            warning "Docker image $image not found locally"
        fi
    done
}

# Check Kubernetes deployments
check_kubernetes_deployments() {
    section "Kubernetes Deployments"
    
    if ! kubectl cluster-info &> /dev/null; then
        warning "Kubernetes cluster not accessible"
        return
    fi
    
    # Check namespaces
    for ns in production staging development; do
        if kubectl get namespace $ns &> /dev/null; then
            success "Namespace $ns exists"
        else
            error "Namespace $ns not found"
        fi
    done
    
    # Check deployments
    DEPLOYMENTS=(
        "api-gateway"
        "auth-service"
        "policy-service"
        "notification-service"
        "config-service"
        "web-frontend"
        "admin-dashboard"
    )
    
    for deployment in "${DEPLOYMENTS[@]}"; do
        if kubectl get deployment $deployment -n production &> /dev/null; then
            # Check if deployment is ready
            READY=$(kubectl get deployment $deployment -n production -o jsonpath='{.status.readyReplicas}')
            DESIRED=$(kubectl get deployment $deployment -n production -o jsonpath='{.spec.replicas}')
            
            if [ "$READY" = "$DESIRED" ] && [ "$READY" -gt 0 ]; then
                success "Deployment $deployment is ready ($READY/$DESIRED replicas)"
            else
                error "Deployment $deployment not ready ($READY/$DESIRED replicas)"
            fi
        else
            error "Deployment $deployment not found"
        fi
    done
    
    # Check services
    info "Checking services..."
    kubectl get services -n production
}

# Check database connectivity
check_databases() {
    section "Database Connectivity"
    
    # PostgreSQL
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "SELECT 1" &> /dev/null; then
        success "PostgreSQL connection successful"
        
        # Check databases
        DBS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -t -c "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1');")
        for db in $DBS; do
            success "Database $db exists"
        done
    else
        error "PostgreSQL connection failed"
    fi
    
    # Redis
    if redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD ping &> /dev/null; then
        success "Redis connection successful"
    else
        error "Redis connection failed"
    fi
    
    # Elasticsearch
    if curl -s "$ELASTICSEARCH_URL/_cluster/health" | grep -q '"status":"green"'; then
        success "Elasticsearch cluster is healthy"
    elif curl -s "$ELASTICSEARCH_URL/_cluster/health" | grep -q '"status":"yellow"'; then
        warning "Elasticsearch cluster is yellow"
    else
        error "Elasticsearch cluster is unhealthy"
    fi
}

# Check API endpoints
check_api_endpoints() {
    section "API Endpoints"
    
    BASE_URL=${API_URL:-"http://localhost:9000"}
    
    ENDPOINTS=(
        "/health:Health check"
        "/api/status:API status"
        "/api/auth/health:Auth service"
        "/api/policies/health:Policy service"
        "/api/notifications/health:Notification service"
        "/api/config/health:Config service"
    )
    
    for endpoint_info in "${ENDPOINTS[@]}"; do
        IFS=':' read -r endpoint description <<< "$endpoint_info"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
        if [ "$response" = "200" ]; then
            success "$description endpoint is healthy"
        else
            error "$description endpoint returned $response"
        fi
    done
}

# Check SSL certificates
check_ssl_certificates() {
    section "SSL Certificates"
    
    DOMAINS=(
        "openpolicy.com"
        "api.openpolicy.com"
        "admin.openpolicy.com"
    )
    
    for domain in "${DOMAINS[@]}"; do
        # Skip if domain doesn't resolve
        if ! host $domain &> /dev/null; then
            warning "Domain $domain does not resolve"
            continue
        fi
        
        # Check certificate
        expiry_date=$(echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
        
        if [ -n "$expiry_date" ]; then
            expiry_epoch=$(date -d "$expiry_date" +%s)
            current_epoch=$(date +%s)
            days_left=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [ $days_left -gt 30 ]; then
                success "SSL certificate for $domain valid for $days_left days"
            elif [ $days_left -gt 0 ]; then
                warning "SSL certificate for $domain expires in $days_left days"
            else
                error "SSL certificate for $domain has expired"
            fi
        else
            error "Could not check SSL certificate for $domain"
        fi
    done
}

# Check monitoring stack
check_monitoring() {
    section "Monitoring Stack"
    
    # Prometheus
    if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus is Healthy"; then
        success "Prometheus is healthy"
    else
        error "Prometheus is not healthy"
    fi
    
    # Grafana
    if curl -s http://localhost:3000/api/health | grep -q "ok"; then
        success "Grafana is healthy"
    else
        error "Grafana is not healthy"
    fi
    
    # Elasticsearch (for logging)
    if curl -s http://localhost:9200/_cluster/health | grep -q "status"; then
        success "Elasticsearch (logging) is healthy"
    else
        error "Elasticsearch (logging) is not healthy"
    fi
    
    # Kibana
    if curl -s http://localhost:5601/api/status | grep -q "available"; then
        success "Kibana is healthy"
    else
        error "Kibana is not healthy"
    fi
}

# Check backup system
check_backups() {
    section "Backup System"
    
    # Check backup scripts
    BACKUP_SCRIPTS=(
        "/opt/openpolicy/backup/scripts/backup-postgres.sh"
        "/opt/openpolicy/backup/scripts/backup-redis.sh"
        "/opt/openpolicy/backup/scripts/backup-elasticsearch.sh"
        "/opt/openpolicy/backup/scripts/backup-files.sh"
    )
    
    for script in "${BACKUP_SCRIPTS[@]}"; do
        if [ -f "$script" ] && [ -x "$script" ]; then
            success "Backup script $(basename $script) exists and is executable"
        else
            error "Backup script $(basename $script) not found or not executable"
        fi
    done
    
    # Check backup schedule
    if systemctl is-active --quiet backup-postgres.timer; then
        success "Backup timer is active"
    else
        warning "Backup timer is not active"
    fi
    
    # Check recent backups
    if [ -n "$AZURE_STORAGE_ACCOUNT" ]; then
        LAST_BACKUP=$(az storage blob list \
            --container-name backups \
            --query "[-1].properties.lastModified" \
            -o tsv 2>/dev/null)
        
        if [ -n "$LAST_BACKUP" ]; then
            success "Last backup: $LAST_BACKUP"
        else
            warning "No backups found in Azure storage"
        fi
    fi
}

# Check security configuration
check_security() {
    section "Security Configuration"
    
    # Check security headers
    response=$(curl -sI http://localhost:9000)
    
    SECURITY_HEADERS=(
        "Strict-Transport-Security"
        "X-Content-Type-Options"
        "X-Frame-Options"
        "X-XSS-Protection"
        "Content-Security-Policy"
    )
    
    for header in "${SECURITY_HEADERS[@]}"; do
        if echo "$response" | grep -qi "$header"; then
            success "Security header $header is set"
        else
            warning "Security header $header is missing"
        fi
    done
    
    # Check firewall rules
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        success "Firewall is active"
    else
        warning "Firewall is not active"
    fi
}

# Check performance metrics
check_performance() {
    section "Performance Metrics"
    
    # API response time
    total_time=$(curl -s -o /dev/null -w "%{time_total}" http://localhost:9000/api/health)
    total_time_ms=$(echo "$total_time * 1000" | bc)
    
    if (( $(echo "$total_time_ms < 100" | bc -l) )); then
        success "API response time: ${total_time_ms}ms (excellent)"
    elif (( $(echo "$total_time_ms < 500" | bc -l) )); then
        success "API response time: ${total_time_ms}ms (good)"
    else
        warning "API response time: ${total_time_ms}ms (slow)"
    fi
    
    # Database connection pool
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "SELECT count(*) FROM pg_stat_activity;" &> /dev/null; then
        success "Database connection pool is healthy"
    else
        error "Database connection pool check failed"
    fi
}

# Check CI/CD pipelines
check_cicd() {
    section "CI/CD Pipelines"
    
    # Check GitHub Actions
    for repo in opp-api-gateway opp-auth-service opp-web-frontend; do
        if gh run list -R "openpolicy-platform/$repo" --limit 1 &> /dev/null; then
            LAST_RUN=$(gh run list -R "openpolicy-platform/$repo" --limit 1 --json status,conclusion -q '.[0]')
            if echo "$LAST_RUN" | grep -q "success"; then
                success "Last CI/CD run for $repo succeeded"
            else
                warning "Last CI/CD run for $repo did not succeed"
            fi
        else
            error "No CI/CD runs found for $repo"
        fi
    done
}

# Generate HTML report
generate_report() {
    REPORT_FILE="platform-verification-report-$(date +%Y%m%d-%H%M%S).html"
    
    cat > "$REPORT_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>OpenPolicy Platform V4 - Verification Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .summary {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            text-align: center;
        }
        .summary-item {
            padding: 20px;
            border-radius: 8px;
            min-width: 150px;
        }
        .passed { background-color: #d4edda; color: #155724; }
        .failed { background-color: #f8d7da; color: #721c24; }
        .warnings { background-color: #fff3cd; color: #856404; }
        .results {
            margin: 20px 0;
        }
        .result-item {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 5px solid;
        }
        .result-success { border-color: #28a745; background-color: #f0f9f0; }
        .result-error { border-color: #dc3545; background-color: #fef0f0; }
        .result-warning { border-color: #ffc107; background-color: #fffef0; }
        .timestamp {
            text-align: right;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
        .score {
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
        }
        .recommendation {
            background-color: #e9ecef;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 OpenPolicy Platform V4 - Verification Report</h1>
        
        <div class="summary">
            <div class="summary-item passed">
                <h2>✅ Passed</h2>
                <div class="score">$PASSED</div>
            </div>
            <div class="summary-item warnings">
                <h2>⚠️ Warnings</h2>
                <div class="score">$WARNINGS</div>
            </div>
            <div class="summary-item failed">
                <h2>❌ Failed</h2>
                <div class="score">$FAILED</div>
            </div>
        </div>
        
        <div class="score-section">
            <h2>Overall Score</h2>
            <div class="score">$(( PASSED * 100 / (PASSED + FAILED + WARNINGS) ))%</div>
        </div>
        
        <h2>Detailed Results</h2>
        <div class="results">
EOF

    for result in "${RESULTS[@]}"; do
        if [[ $result == *"✅"* ]]; then
            echo "            <div class='result-item result-success'>$result</div>" >> "$REPORT_FILE"
        elif [[ $result == *"❌"* ]]; then
            echo "            <div class='result-item result-error'>$result</div>" >> "$REPORT_FILE"
        else
            echo "            <div class='result-item result-warning'>$result</div>" >> "$REPORT_FILE"
        fi
    done

    cat >> "$REPORT_FILE" << EOF
        </div>
        
        <div class="recommendation">
            <h2>Recommendations</h2>
EOF

    if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo "            <p><strong>Excellent!</strong> Your platform is fully operational with no issues detected.</p>" >> "$REPORT_FILE"
    elif [ $FAILED -eq 0 ]; then
        echo "            <p><strong>Good!</strong> Your platform is operational but has some warnings that should be addressed.</p>" >> "$REPORT_FILE"
    else
        echo "            <p><strong>Action Required!</strong> There are critical issues that need immediate attention.</p>" >> "$REPORT_FILE"
    fi

    cat >> "$REPORT_FILE" << EOF
            <ul>
                <li>Review and fix all failed checks immediately</li>
                <li>Address warnings to improve platform stability</li>
                <li>Schedule regular verification checks</li>
                <li>Keep all components and dependencies updated</li>
            </ul>
        </div>
        
        <div class="timestamp">
            Generated on: $(date)
        </div>
    </div>
</body>
</html>
EOF

    info "Report generated: $REPORT_FILE"
}

# Main execution
main() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                   OpenPolicy Platform V4 - Final Verification                 ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Run all checks
    check_github_repos
    check_docker_images
    check_kubernetes_deployments
    check_databases
    check_api_endpoints
    check_ssl_certificates
    check_monitoring
    check_backups
    check_security
    check_performance
    check_cicd
    
    # Summary
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                   SUMMARY                                     ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo ""
    
    TOTAL=$((PASSED + WARNINGS + FAILED))
    SCORE=$((PASSED * 100 / TOTAL))
    
    echo -e "  ${CYAN}Overall Score: $SCORE%${NC}"
    echo ""
    
    # Generate report
    generate_report
    
    # Exit code based on failures
    if [ $FAILED -gt 0 ]; then
        echo -e "${RED}Platform verification failed with $FAILED critical issues.${NC}"
        exit 1
    elif [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Platform verification completed with $WARNINGS warnings.${NC}"
        exit 0
    else
        echo -e "${GREEN}Platform verification completed successfully! 🎉${NC}"
        exit 0
    fi
}

# Run main function
main "$@"