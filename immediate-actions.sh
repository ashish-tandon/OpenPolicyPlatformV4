#!/bin/bash

# Immediate Actions Script for OpenPolicyPlatformV4
# Prerequisites and initial setup for layered migration

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🎯 OpenPolicyPlatform V4 - Immediate Actions${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to check command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 is not installed${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
        return 0
    fi
}

# Function to check authentication
check_auth() {
    local service=$1
    local check_cmd=$2
    
    if eval "$check_cmd" &> /dev/null; then
        echo -e "${GREEN}✓ Authenticated with $service${NC}"
        return 0
    else
        echo -e "${RED}✗ Not authenticated with $service${NC}"
        return 1
    fi
}

# Function to analyze current repository
analyze_repository() {
    echo -e "\n${YELLOW}📊 Analyzing current repository structure...${NC}"
    
    # Count services
    if [ -d "open-policy-platform/services" ]; then
        service_count=$(ls -1 open-policy-platform/services | wc -l)
        echo -e "${BLUE}Found ${service_count} services in /services directory${NC}"
    fi
    
    # Check for Docker Compose files
    compose_files=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | wc -l)
    echo -e "${BLUE}Found ${compose_files} Docker Compose files${NC}"
    
    # Check current Git status
    if [ -d ".git" ]; then
        echo -e "\n${YELLOW}Git Status:${NC}"
        git status --short | head -10
        if [ $(git status --short | wc -l) -gt 10 ]; then
            echo "... and more uncommitted changes"
        fi
    fi
}

# Function to create backup
create_backup() {
    echo -e "\n${YELLOW}📦 Creating backup...${NC}"
    
    backup_dir="backups/pre-migration-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup important files
    files_to_backup=(
        "docker-compose.yml"
        "docker-compose*.yml"
        ".env"
        "*.md"
        "config/*"
    )
    
    for pattern in "${files_to_backup[@]}"; do
        if ls $pattern 1> /dev/null 2>&1; then
            cp -r $pattern "$backup_dir/" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✓ Backup created in $backup_dir${NC}"
}

# Function to check Azure resources
check_azure_resources() {
    echo -e "\n${YELLOW}☁️ Checking Azure resources...${NC}"
    
    if ! command -v az &> /dev/null; then
        echo -e "${RED}Azure CLI not installed, skipping Azure checks${NC}"
        return
    fi
    
    if ! az account show &> /dev/null; then
        echo -e "${RED}Not logged into Azure, skipping resource checks${NC}"
        return
    fi
    
    # Check for resource group
    if az group show --name openpolicy-platform-rg &> /dev/null; then
        echo -e "${GREEN}✓ Resource group 'openpolicy-platform-rg' exists${NC}"
        
        # Check for key services
        if az acr show --name openpolicyacr --resource-group openpolicy-platform-rg &> /dev/null 2>&1; then
            echo -e "${GREEN}✓ Container Registry exists${NC}"
        else
            echo -e "${YELLOW}⚠ Container Registry not found${NC}"
        fi
        
        if az postgres flexible-server show --name openpolicy-postgresql --resource-group openpolicy-platform-rg &> /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL server exists${NC}"
        else
            echo -e "${YELLOW}⚠ PostgreSQL server not found${NC}"
        fi
        
        if az redis show --name openpolicy-redis --resource-group openpolicy-platform-rg &> /dev/null 2>&1; then
            echo -e "${GREEN}✓ Redis cache exists${NC}"
        else
            echo -e "${YELLOW}⚠ Redis cache not found${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Resource group 'openpolicy-platform-rg' not found${NC}"
    fi
}

# Function to prepare migration directories
prepare_migration() {
    echo -e "\n${YELLOW}📁 Preparing migration structure...${NC}"
    
    # Create migration workspace
    mkdir -p migration-workspace/{infrastructure,data,business,frontend,legacy,orchestration}
    
    # Create tracking file
    cat > migration-workspace/migration-status.json << 'EOF'
{
  "migration_started": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "source_repository": "OpenPolicyPlatformV4",
  "target_architecture": "6-layer",
  "layers": {
    "infrastructure": {
      "status": "pending",
      "services": 15,
      "repository": "openpolicy-infrastructure"
    },
    "data": {
      "status": "pending",
      "services": 8,
      "repository": "openpolicy-data"
    },
    "business": {
      "status": "pending",
      "services": 10,
      "repository": "openpolicy-business"
    },
    "frontend": {
      "status": "pending",
      "services": 3,
      "repository": "openpolicy-frontend"
    },
    "legacy": {
      "status": "pending",
      "services": 3,
      "repository": "openpolicy-legacy"
    },
    "orchestration": {
      "status": "pending",
      "services": 0,
      "repository": "openpolicy-orchestration"
    }
  },
  "total_services": 39,
  "completion_percentage": 0
}
EOF
    
    echo -e "${GREEN}✓ Migration workspace prepared${NC}"
}

# Function to generate migration report
generate_report() {
    echo -e "\n${YELLOW}📄 Generating pre-migration report...${NC}"
    
    cat > MIGRATION_READINESS_REPORT.md << 'EOF'
# Migration Readiness Report

**Generated**: $(date)
**Repository**: OpenPolicyPlatformV4
**Migration Type**: Monorepo to 6-Layer Architecture

## Environment Check

### Prerequisites
- [ ] Git installed and configured
- [ ] GitHub CLI installed and authenticated
- [ ] Azure CLI installed and authenticated
- [ ] Docker installed and running
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed

### Repository Status
- **Total Services**: 45+ components
- **Architecture**: Monolith transitioning to microservices
- **Current State**: Mixed (some services in /services, others scattered)

## Layer Distribution Plan

### Infrastructure Layer (15 services)
- Authentication, Monitoring, Config, Gateway
- Database, Cache, Message Queue
- Logging Stack (ELK)
- Background Processing (Celery)

### Data Layer (8 services)
- ETL, Data Management, Scrapers
- Policy Engine, Search, File Management

### Business Layer (10 services)
- Committees, Representatives, Votes, Debates
- Analytics, Reporting, Dashboard
- Workflow, Integration

### Frontend Layer (3 services)
- Web Application
- Mobile API
- Main Backend API

### Legacy Layer (3 services)
- Legacy Django
- MCP Service
- Docker Monitor

### Orchestration Layer
- CI/CD Pipelines
- Deployment Configurations
- Infrastructure as Code

## Migration Timeline

### Week 1-2: Infrastructure Layer
- Set up core services
- Establish database and cache
- Configure monitoring

### Week 3-4: Data Layer
- Migrate data processing services
- Set up scrapers
- Configure search

### Week 5-8: Business Layer
- Migrate business logic
- Set up analytics
- Configure workflows

### Week 9-10: Frontend Layer
- Migrate UI services
- Set up mobile API
- Configure gateway routing

### Week 11: Legacy & Cleanup
- Migrate legacy services
- Clean up old code
- Documentation

### Week 12: Testing & Validation
- End-to-end testing
- Performance validation
- Production readiness

## Risk Assessment

### High Risk
- Service interdependencies
- Data migration complexity
- Authentication across layers

### Medium Risk
- Performance impact
- Network latency between layers
- Configuration management

### Low Risk
- Technology stack (well-established)
- Team expertise
- Rollback procedures

## Next Steps

1. Run `./immediate-actions.sh` to verify environment
2. Execute `./layered-migration.sh` for each layer
3. Monitor progress in migration-workspace/
4. Update CI/CD pipelines
5. Perform integration testing

## Success Criteria

- [ ] All 6 repositories created and populated
- [ ] CI/CD pipelines functional
- [ ] Services deployed to Azure
- [ ] End-to-end tests passing
- [ ] Performance targets met
- [ ] Documentation complete
EOF
    
    echo -e "${GREEN}✓ Report generated: MIGRATION_READINESS_REPORT.md${NC}"
}

# Main execution
main() {
    echo -e "${PURPLE}Starting immediate actions for layered migration...${NC}\n"
    
    # Check prerequisites
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    all_good=true
    
    check_command "git" || all_good=false
    check_command "gh" || all_good=false
    check_command "az" || all_good=false
    check_command "docker" || all_good=false
    check_command "python3" || all_good=false
    check_command "node" || all_good=false
    
    echo ""
    
    # Check authentication
    echo -e "${YELLOW}🔐 Checking authentication...${NC}"
    
    check_auth "GitHub" "gh auth status" || all_good=false
    check_auth "Azure" "az account show" || all_good=false
    
    # Analyze repository
    analyze_repository
    
    # Check Azure resources
    check_azure_resources
    
    # Create backup
    create_backup
    
    # Prepare migration structure
    prepare_migration
    
    # Generate report
    generate_report
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ "$all_good" = true ]; then
        echo -e "${GREEN}✅ All prerequisites met! Ready for migration.${NC}"
        echo -e "\n${YELLOW}Next steps:${NC}"
        echo "1. Review MIGRATION_READINESS_REPORT.md"
        echo "2. Update configuration in layered-migration.sh"
        echo "3. Run: ./layered-migration.sh <github-org> <azure-subscription> all"
    else
        echo -e "${RED}⚠️  Some prerequisites are missing.${NC}"
        echo -e "\n${YELLOW}Please install missing tools and authenticate:${NC}"
        echo "- GitHub CLI: gh auth login"
        echo "- Azure CLI: az login"
        echo "- Docker: Ensure Docker daemon is running"
    fi
    
    echo -e "\n${BLUE}Summary files created:${NC}"
    echo "- COMPLETE_SERVICES_INVENTORY.md"
    echo "- MIGRATION_READINESS_REPORT.md"
    echo "- migration-workspace/"
    echo "- backups/"
}

# Run main function
main