#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Branch Protection Setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}🔒 Setting up Branch Protection for V5 Repositories${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# GitHub organization/user
ORG="ashish-tandon"

# Repository names
REPOS=(
    "openpolicy-platform-v5-core"
    "openpolicy-platform-v5-services"
    "openpolicy-platform-v5-web"
    "openpolicy-platform-v5-monitoring"
    "openpolicy-platform-v5-deployment"
    "openpolicy-platform-v5-docs"
)

echo -e "${CYAN}Setting up branch protection for ${#REPOS[@]} repositories...${NC}"
echo

for repo in "${REPOS[@]}"; do
    echo -e "${YELLOW}🔒 Setting up branch protection for $repo...${NC}"
    
    # Set up main branch protection
    gh api repos/$ORG/$repo/branches/main/protection \
        --method PUT \
        --field required_status_checks='{"strict":true,"contexts":["code-quality","security-scan"]}' \
        --field enforce_admins=true \
        --field required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
        --field restrictions='{"users":[],"teams":[]}' \
        --silent
    
    echo -e "${GREEN}✅ Main branch protection configured${NC}"
    
    # Set up develop branch protection
    gh api repos/$ORG/$repo/branches/develop/protection \
        --method PUT \
        --field required_status_checks='{"strict":false,"contexts":["code-quality"]}' \
        --field enforce_admins=false \
        --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
        --field restrictions='{"users":[],"teams":[]}' \
        --silent
    
    echo -e "${GREEN}✅ Develop branch protection configured${NC}"
    
    # Enable security features
    echo -e "${CYAN}🔒 Enabling security features...${NC}"
    
    # Enable secret scanning
    gh api repos/$ORG/$repo/security-and-analysis \
        --method PUT \
        --field secret_scanning='{"status":"enabled"}' \
        --field secret_scanning_push_protection='{"status":"enabled"}' \
        --silent
    
    echo -e "${GREEN}✅ Secret scanning enabled${NC}"
    
    # Enable Dependabot
    gh api repos/$ORG/$repo/vulnerability-alerts \
        --method PUT \
        --silent
    
    echo -e "${GREEN}✅ Vulnerability alerts enabled${NC}"
    
    echo -e "${GREEN}✅ $repo setup complete${NC}"
    echo "----------------------------------------"
done

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ BRANCH PROTECTION SETUP COMPLETE!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 What was configured:${NC}"
echo -e "  ✅ Main branch: 2 reviews required, strict checks"
echo -e "  ✅ Develop branch: 1 review required, quality checks"
echo -e "  ✅ Secret scanning enabled for all repos"
echo -e "  ✅ Vulnerability alerts enabled"
echo -e "  ✅ Admin enforcement on main branch"
echo
echo -e "${CYAN}🚀 Next steps:${NC}"
echo -e "  1. Set up repository secrets"
echo -e "  2. Configure CI/CD workflows"
echo -e "  3. Set up monitoring and alerting"
echo -e "  4. Deploy to staging environment"
echo
echo -e "${PURPLE}🎉 Your V5 repositories are now secure and protected!${NC}"
