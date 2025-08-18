#!/usr/bin/env bash
set -euo pipefail

# Architecture Compliance Checker
# This script validates that services follow microservices architecture principles

SERVICE_NAME=${1:-}
if [[ -z "$SERVICE_NAME" ]]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 auth-service"
    exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_DIR="$ROOT_DIR/services/$SERVICE_NAME"
LOG_DIR="$ROOT_DIR/logs/architecture-compliance"

# Create log directory
mkdir -p "$LOG_DIR"

# Initialize compliance tracking using simple arrays
declare -a compliance_checks=(
    "microservices_architecture"
    "health_check_endpoints"
    "centralized_logging"
    "monitoring_endpoints"
    "configuration_standards"
    "dependencies_documented"
    "ports_configured"
    "error_handling"
    "service_isolation"
    "api_gateway_integration"
)

declare -a compliance_status=(
    "false" "false" "false" "false" "false"
    "false" "false" "false" "false" "false"
)

declare -a violations
declare -a warnings
declare -a recommendations

# Function to update compliance status
update_compliance() {
    local check_name="$1"
    local status="$2"
    
    for i in "${!compliance_checks[@]}"; do
        if [[ "${compliance_checks[$i]}" == "$check_name" ]]; then
            compliance_status[$i]="$status"
            break
        fi
    done
}

# Function to get compliance status
get_compliance() {
    local check_name="$1"
    
    for i in "${!compliance_checks[@]}"; do
        if [[ "${compliance_checks[$i]}" == "$check_name" ]]; then
            echo "${compliance_status[$i]}"
            break
        fi
    done
}

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -u +%Y-%m-%dT%H-%M-%SZ)
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_DIR/${SERVICE_NAME}_compliance.log"
}

# Check if service directory exists
if [[ ! -d "$SERVICE_DIR" ]]; then
    log_message "ERROR" "Service directory not found: $SERVICE_DIR"
    exit 1
fi

log_message "INFO" "Starting architecture compliance check for service: $SERVICE_NAME"
log_message "INFO" "Service directory: $SERVICE_DIR"

## 1. Microservices Architecture Validation

log_message "INFO" "Checking microservices architecture compliance..."

# Check if service has its own directory structure
if [[ -d "$SERVICE_DIR/src" ]] && [[ -f "$SERVICE_DIR/Dockerfile" ]]; then
    update_compliance "microservices_architecture" "true"
    log_message "INFO" "✅ Service follows microservices architecture (has src/ and Dockerfile)"
else
    violations+=("Service does not have proper microservices structure (missing src/ or Dockerfile)")
    log_message "ERROR" "❌ Service does not follow microservices architecture"
fi

# Check service isolation
if [[ -f "$SERVICE_DIR/requirements.txt" ]] || [[ -f "$SERVICE_DIR/package.json" ]]; then
    update_compliance "service_isolation" "true"
    log_message "INFO" "✅ Service has isolated dependencies"
else
    warnings+=("Service may not have isolated dependencies")
    log_message "WARN" "⚠️ Service dependency isolation unclear"
fi

## 2. Health Check Endpoints Validation

log_message "INFO" "Checking health check endpoints..."

# Check for health check endpoints in source code
if [[ -d "$SERVICE_DIR/src" ]]; then
    if grep -r "healthz\|readyz\|health" "$SERVICE_DIR/src" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" >/dev/null 2>&1; then
        update_compliance "health_check_endpoints" "true"
        log_message "INFO" "✅ Health check endpoints found in source code"
    else
        violations+=("Missing health check endpoints (/healthz, /readyz)")
        log_message "ERROR" "❌ Health check endpoints not found"
    fi
fi

## 3. Centralized Logging Validation

log_message "INFO" "Checking centralized logging configuration..."

# Check for logging configuration
if grep -r "logging\|logger\|log" "$SERVICE_DIR/src" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" >/dev/null 2>&1; then
    update_compliance "centralized_logging" "true"
    log_message "INFO" "✅ Logging configuration found"
else
    warnings+=("Logging configuration may be missing")
    log_message "WARN" "⚠️ Logging configuration not clearly defined"
fi

## 4. Monitoring Endpoints Validation

log_message "INFO" "Checking monitoring endpoints..."

# Check for metrics endpoints
if grep -r "metrics\|prometheus\|monitoring" "$SERVICE_DIR/src" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" >/dev/null 2>&1; then
    update_compliance "monitoring_endpoints" "true"
    log_message "INFO" "✅ Monitoring endpoints found"
else
    violations+=("Missing monitoring endpoints (/metrics)")
    log_message "ERROR" "❌ Monitoring endpoints not found"
fi

## 5. Configuration Standards Validation

log_message "INFO" "Checking configuration standards..."

# Check for environment variable usage
if grep -r "os\.getenv\|process\.env\|os\.environ" "$SERVICE_DIR/src" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" >/dev/null 2>&1; then
    update_compliance "configuration_standards" "true"
    log_message "INFO" "✅ Environment variable configuration found"
else
    warnings+=("Configuration may not follow environment variable standards")
    log_message "WARN" "⚠️ Environment variable configuration not clearly defined"
fi

## 6. Dependencies Documentation Validation

log_message "INFO" "Checking dependencies documentation..."

# Check for requirements.txt or package.json
if [[ -f "$SERVICE_DIR/requirements.txt" ]] || [[ -f "$SERVICE_DIR/package.json" ]]; then
    update_compliance "dependencies_documented" "true"
    log_message "INFO" "✅ Dependencies are documented"
else
    violations+=("Missing dependencies documentation")
    log_message "ERROR" "❌ Dependencies not documented"
fi

## 7. Port Configuration Validation

log_message "INFO" "Checking port configuration..."

# Check Dockerfile for port exposure
if [[ -f "$SERVICE_DIR/Dockerfile" ]]; then
    if grep -q "EXPOSE" "$SERVICE_DIR/Dockerfile"; then
        update_compliance "ports_configured" "true"
        log_message "INFO" "✅ Port configuration found in Dockerfile"
    else
        violations+=("Missing port configuration in Dockerfile")
        log_message "ERROR" "❌ Port not configured in Dockerfile"
    fi
fi

## 8. Error Handling Validation

log_message "INFO" "Checking error handling..."

# Check for error handling patterns
if grep -r "try\|catch\|except\|error" "$SERVICE_DIR/src" --include="*.py" --include="*.js" --include="*.ts" --include="*.go" >/dev/null 2>&1; then
    update_compliance "error_handling" "true"
    log_message "INFO" "✅ Error handling patterns found"
else
    warnings+=("Error handling may be insufficient")
    log_message "WARN" "⚠️ Error handling patterns not clearly defined"
fi

## 9. API Gateway Integration Validation

log_message "INFO" "Checking API Gateway integration..."

# Check if service is configured in API Gateway
if [[ -f "$ROOT_DIR/services/api-gateway/main.go" ]]; then
    if grep -q "$SERVICE_NAME" "$ROOT_DIR/services/api-gateway/main.go"; then
        update_compliance "api_gateway_integration" "true"
        log_message "INFO" "✅ Service is integrated with API Gateway"
    else
        warnings+=("Service may not be integrated with API Gateway")
        log_message "WARN" "⚠️ API Gateway integration not found"
    fi
fi

## 10. Generate Compliance Report

log_message "INFO" "Generating compliance report..."

# Calculate compliance score
total_checks=${#compliance_checks[@]}
passed_checks=0
for i in "${!compliance_checks[@]}"; do
    if [[ "${compliance_status[$i]}" == "true" ]]; then
        ((passed_checks++))
    fi
done

compliance_score=$((passed_checks * 100 / total_checks))

# Generate detailed report
REPORT_FILE="$LOG_DIR/${SERVICE_NAME}_compliance_report_$(date -u +%Y-%m-%dT%H-%M-%SZ).md"

{
    echo "# Architecture Compliance Report"
    echo "- **Service**: $SERVICE_NAME"
    echo "- **Timestamp**: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- **Compliance Score**: $compliance_score% ($passed_checks/$total_checks)"
    echo ""
    echo "## Compliance Status"
    echo ""
    
    for i in "${!compliance_checks[@]}"; do
        status="❌"
        if [[ "${compliance_status[$i]}" == "true" ]]; then
            status="✅"
        fi
        echo "- $status **${compliance_checks[$i]//_/ }**: ${compliance_status[$i]}"
    done
    
    if [[ ${#violations[@]} -gt 0 ]]; then
        echo ""
        echo "## Critical Violations"
        echo ""
        for violation in "${violations[@]}"; do
            echo "- ❌ $violation"
        done
    fi
    
    if [[ ${#warnings[@]} -gt 0 ]]; then
        echo ""
        echo "## Warnings"
        echo ""
        for warning in "${warnings[@]}"; do
            echo "- ⚠️ $warning"
        done
    fi
    
    if [[ ${#recommendations[@]} -gt 0 ]]; then
        echo ""
        echo "## Recommendations"
        echo ""
        for recommendation in "${recommendations[@]}"; do
            echo "- 💡 $recommendation"
        done
    fi
    
    echo ""
    echo "## Next Steps"
    echo ""
    if [[ $compliance_score -eq 100 ]]; then
        echo "🎉 **Service is fully compliant with microservices architecture!**"
        echo "- Ready for deployment"
        echo "- No immediate action required"
    elif [[ $compliance_score -ge 80 ]]; then
        echo "✅ **Service is mostly compliant with minor issues**"
        echo "- Review warnings and recommendations"
        echo "- Fix violations before deployment"
        echo "- Consider improvements for better architecture alignment"
    elif [[ $compliance_score -ge 60 ]]; then
        echo "⚠️ **Service has significant compliance issues**"
        echo "- Fix all violations before deployment"
        echo "- Address warnings and recommendations"
        echo "- Consider architecture review"
    else
        echo "❌ **Service has major compliance issues**"
        echo "- **DO NOT DEPLOY** until issues are resolved"
        echo "- Fix all violations and warnings"
        echo "- Consider complete architecture redesign"
    fi
    
    echo ""
    echo "## Detailed Check Results"
    echo ""
    echo "| Check | Status | Details |"
    echo "|------|--------|---------|"
    
    for i in "${!compliance_checks[@]}"; do
        status="❌"
        if [[ "${compliance_status[$i]}" == "true" ]]; then
            status="✅"
        fi
        check_name="${compliance_checks[$i]//_/ }"
        echo "| $check_name | $status | ${compliance_status[$i]} |"
    done
    
} > "$REPORT_FILE"

# Display summary
echo ""
echo "=== ARCHITECTURE COMPLIANCE CHECK COMPLETE ==="
echo "Service: $SERVICE_NAME"
echo "Compliance Score: $compliance_score% ($passed_checks/$total_checks)"
echo "Report saved to: $REPORT_FILE"
echo ""

if [[ $compliance_score -eq 100 ]]; then
    echo "🎉 ALL CHECKS PASSED - Service is ready for deployment!"
    exit 0
elif [[ $compliance_score -ge 80 ]]; then
    echo "✅ Service is mostly compliant - Review warnings before deployment"
    exit 0
elif [[ $compliance_score -ge 60 ]]; then
    echo "⚠️ Service has compliance issues - Fix violations before deployment"
    exit 1
else
    echo "❌ Service has major compliance issues - DO NOT DEPLOY"
    exit 1
fi
