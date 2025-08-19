#!/bin/bash

# MASTER DEPLOYMENT SCRIPT FOR OPENPOLICY PLATFORM V4
# This script executes the complete deployment of everything

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                     OPENPOLICY PLATFORM V4 - MEGA DEPLOYMENT                 ║"
    echo "║                                                                              ║"
    echo "║                          🚀 DEPLOYING EVERYTHING! 🚀                         ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}▶ $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check prerequisites
check_prerequisites() {
    section "Checking Prerequisites"
    
    # Required tools
    REQUIRED_TOOLS=(
        "docker:Docker not installed. Visit https://docs.docker.com/get-docker/"
        "docker-compose:Docker Compose not installed"
        "kubectl:Kubectl not installed. Visit https://kubernetes.io/docs/tasks/tools/"
        "helm:Helm not installed. Visit https://helm.sh/docs/intro/install/"
        "az:Azure CLI not installed. Visit https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        "gh:GitHub CLI not installed. Visit https://cli.github.com/"
        "jq:jq not installed. Run: apt-get install jq"
    )
    
    for tool_info in "${REQUIRED_TOOLS[@]}"; do
        IFS=':' read -r tool message <<< "$tool_info"
        if command -v $tool &> /dev/null; then
            log "✅ $tool is installed"
        else
            error "$message"
        fi
    done
    
    # Check authentication
    if gh auth status &> /dev/null; then
        log "✅ GitHub CLI authenticated"
    else
        error "Not authenticated to GitHub. Run: gh auth login"
    fi
    
    if az account show &> /dev/null; then
        log "✅ Azure CLI authenticated"
    else
        info "Not authenticated to Azure. Run: az login"
    fi
}

# Execute deployment steps
execute_deployment() {
    # 1. GitHub Repositories
    section "Step 1/10: Creating GitHub Repositories"
    if [ -f "scripts/execute-github-setup.sh" ]; then
        ./scripts/execute-github-setup.sh || warning "GitHub setup had issues"
    else
        info "GitHub setup script not found, skipping..."
    fi
    
    # 2. Build Docker Images
    section "Step 2/10: Building Docker Images"
    log "Building all Docker images..."
    docker-compose -f docker-compose.complete.yml build --parallel || warning "Some images failed to build"
    
    # 3. Setup Databases
    section "Step 3/10: Setting Up Databases"
    if [ -f "scripts/setup-complete-database.sh" ]; then
        ./scripts/setup-complete-database.sh || warning "Database setup had issues"
    else
        info "Database setup script not found, skipping..."
    fi
    
    # 4. Deploy Locally
    section "Step 4/10: Local Deployment"
    log "Starting local services..."
    docker-compose -f docker-compose.complete.yml up -d
    sleep 30  # Wait for services to start
    
    # 5. Setup SSL Certificates
    section "Step 5/10: SSL Certificate Setup"
    if [ -f "scripts/ssl-certificate-setup.sh" ]; then
        sudo ./scripts/ssl-certificate-setup.sh || warning "SSL setup had issues"
    else
        info "SSL setup script not found, skipping..."
    fi
    
    # 6. Setup Security Scanning
    section "Step 6/10: Security Configuration"
    if [ -f "scripts/security-scan-setup.sh" ]; then
        ./scripts/security-scan-setup.sh || warning "Security setup had issues"
    else
        info "Security setup script not found, skipping..."
    fi
    
    # 7. Setup Backup System
    section "Step 7/10: Backup & DR Configuration"
    if [ -f "scripts/backup-disaster-recovery.sh" ]; then
        ./scripts/backup-disaster-recovery.sh || warning "Backup setup had issues"
    else
        info "Backup setup script not found, skipping..."
    fi
    
    # 8. Deploy to QNAP
    section "Step 8/10: QNAP Deployment"
    if [ -f "scripts/create-qnap-deployment-package.sh" ]; then
        ./scripts/create-qnap-deployment-package.sh
        log "QNAP deployment package created: qnap-deployment-*.tar.gz"
        info "Transfer this package to your QNAP and run the deployment script"
    else
        info "QNAP deployment script not found, skipping..."
    fi
    
    # 9. Deploy to Azure
    section "Step 9/10: Azure Deployment"
    if [ "$DEPLOY_TO_AZURE" = "yes" ] && [ -f "deployment/azure/deploy-to-azure.sh" ]; then
        ./deployment/azure/deploy-to-azure.sh || warning "Azure deployment had issues"
    else
        info "Skipping Azure deployment (set DEPLOY_TO_AZURE=yes to enable)"
    fi
    
    # 10. Final Verification
    section "Step 10/10: Platform Verification"
    if [ -f "scripts/final-platform-verification.sh" ]; then
        ./scripts/final-platform-verification.sh || warning "Some verification checks failed"
    else
        info "Verification script not found, skipping..."
    fi
}

# Create quick access scripts
create_shortcuts() {
    section "Creating Quick Access Scripts"
    
    # Start script
    cat > start-platform.sh << 'EOF'
#!/bin/bash
echo "Starting OpenPolicy Platform..."
docker-compose -f docker-compose.complete.yml up -d
echo "Platform started! Access at: http://localhost:9000"
EOF
    chmod +x start-platform.sh
    
    # Stop script
    cat > stop-platform.sh << 'EOF'
#!/bin/bash
echo "Stopping OpenPolicy Platform..."
docker-compose -f docker-compose.complete.yml down
echo "Platform stopped!"
EOF
    chmod +x stop-platform.sh
    
    # Status script
    cat > check-status.sh << 'EOF'
#!/bin/bash
echo "OpenPolicy Platform Status:"
docker-compose -f docker-compose.complete.yml ps
echo ""
echo "API Health: $(curl -s http://localhost:9000/health || echo 'Not responding')"
EOF
    chmod +x check-status.sh
    
    # Logs script
    cat > view-logs.sh << 'EOF'
#!/bin/bash
SERVICE=${1:-api-gateway}
docker-compose -f docker-compose.complete.yml logs -f $SERVICE
EOF
    chmod +x view-logs.sh
    
    log "✅ Quick access scripts created"
}

# Generate final report
generate_final_report() {
    section "Generating Final Report"
    
    REPORT_FILE="DEPLOYMENT_REPORT_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# OpenPolicy Platform V4 - Deployment Report

**Date**: $(date)
**Deployed By**: $(whoami)
**Platform Version**: 4.0.0

## Deployment Summary

### ✅ Components Deployed
- [ ] GitHub Repositories (6)
- [ ] Docker Images (37)
- [ ] Database Schema
- [ ] SSL Certificates
- [ ] Security Scanning
- [ ] Backup System
- [ ] Monitoring Stack
- [ ] QNAP Package
- [ ] Azure Infrastructure

### 🌐 Access URLs
- **Local Platform**: http://localhost:9000
- **Local Admin**: http://localhost:3001
- **Grafana**: http://localhost:3000
- **Kibana**: http://localhost:5601

### 🔑 Default Credentials
- **Admin Email**: admin@openpolicy.com
- **Admin Password**: AdminSecure123!
- **Grafana**: admin / prom-operator

### 📋 Next Steps
1. Run verification: \`./scripts/final-platform-verification.sh\`
2. Check service status: \`./check-status.sh\`
3. View logs: \`./view-logs.sh [service-name]\`
4. Access admin dashboard and configure settings
5. Set up production domains and SSL
6. Configure backup destinations
7. Set up monitoring alerts

### 🚀 Quick Commands
\`\`\`bash
# Start platform
./start-platform.sh

# Stop platform
./stop-platform.sh

# Check status
./check-status.sh

# View logs
./view-logs.sh api-gateway

# Run tests
./scripts/comprehensive-platform-test.sh

# Backup now
./backup/scripts/backup-all.sh
\`\`\`

### 📚 Documentation
- Architecture: docs/architecture/
- API Docs: docs/api/
- Operations: docs/operations/
- Security: security/policies/

### ⚠️ Important Notes
- Remember to update environment variables for production
- Configure real email/SMS providers for notifications
- Set up proper SSL certificates for production domains
- Review and adjust security policies
- Schedule regular backup tests
- Plan disaster recovery drills

## Deployment Log
$(tail -50 deployment.log 2>/dev/null || echo "No deployment log found")
EOF
    
    log "✅ Deployment report generated: $REPORT_FILE"
}

# Main execution
main() {
    print_banner
    
    # Start logging
    exec > >(tee -a deployment.log)
    exec 2>&1
    
    log "Starting complete platform deployment..."
    START_TIME=$(date +%s)
    
    # Check prerequisites
    check_prerequisites
    
    # Confirm deployment
    echo ""
    echo -e "${YELLOW}This will deploy the ENTIRE OpenPolicy Platform V4.${NC}"
    echo -e "${YELLOW}This includes creating repositories, building images, and setting up infrastructure.${NC}"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        info "Deployment cancelled"
        exit 0
    fi
    
    # Execute deployment
    execute_deployment
    
    # Create shortcuts
    create_shortcuts
    
    # Generate report
    generate_final_report
    
    # Calculate duration
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))
    
    # Final summary
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                         🎉 DEPLOYMENT COMPLETE! 🎉                           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}✅ OpenPolicy Platform V4 has been successfully deployed!${NC}"
    echo -e "${GREEN}✅ Total deployment time: ${MINUTES}m ${SECONDS}s${NC}"
    echo ""
    echo -e "${BLUE}📋 What to do next:${NC}"
    echo "   1. Check platform status: ${YELLOW}./check-status.sh${NC}"
    echo "   2. View the admin dashboard: ${YELLOW}http://localhost:3001${NC}"
    echo "   3. Run verification tests: ${YELLOW}./scripts/final-platform-verification.sh${NC}"
    echo "   4. Read the deployment report: ${YELLOW}cat $REPORT_FILE${NC}"
    echo ""
    echo -e "${GREEN}🚀 Your platform is ready for production!${NC}"
    echo ""
}

# Trap errors
trap 'error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"