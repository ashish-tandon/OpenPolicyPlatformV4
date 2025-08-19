#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Repository Secrets Setup

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
echo -e "${BLUE}🔐 Setting up Repository Secrets for V5${NC}"
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

echo -e "${YELLOW}⚠️  IMPORTANT: You need to create these secrets manually in each repository${NC}"
echo -e "${YELLOW}   This script will show you exactly what to do${NC}"
echo
echo -e "${CYAN}Required secrets for each repository:${NC}"
echo

# Define required secrets
declare -A SECRETS
SECRETS["REPO_SYNC_TOKEN"]="GitHub token for cross-repository synchronization"
SECRETS["DOCKER_REGISTRY_TOKEN"]="Token for GitHub Container Registry access"
SECRETS["KUBERNETES_CONFIG"]="Base64 encoded kubeconfig for deployment"
SECRETS["AZURE_CREDENTIALS"]="Azure service principal credentials (JSON)"
SECRETS["AUTH0_SECRETS"]="Auth0 client ID, secret, and domain"
SECRETS["DATABASE_URL"]="Production database connection string"
SECRETS["REDIS_URL"]="Production Redis connection string"

echo -e "${YELLOW}📋 Required Secrets for Each Repository:${NC}"
echo "=================================================="

for secret in "${!SECRETS[@]}"; do
    echo -e "${CYAN}🔐 $secret${NC}"
    echo -e "   ${SECRETS[$secret]}"
    echo
done

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}📝 SETUP INSTRUCTIONS${NC}"
echo -e "${GREEN}==================================================${NC}"
echo

for repo in "${REPOS[@]}"; do
    echo -e "${YELLOW}🔧 Setting up secrets for: $repo${NC}"
    echo -e "${CYAN}Repository URL: https://github.com/$ORG/$repo${NC}"
    echo
    echo -e "${GREEN}Steps to add secrets:${NC}"
    echo "1. Go to: https://github.com/$ORG/$repo/settings/secrets/actions"
    echo "2. Click 'New repository secret'"
    echo "3. Add each secret from the list above"
    echo "4. Repeat for all repositories"
    echo
    echo -e "${PURPLE}Quick Links:${NC}"
    echo "  - Settings: https://github.com/$ORG/$repo/settings"
    echo "  - Actions: https://github.com/$ORG/$repo/actions"
    echo "  - Security: https://github.com/$ORG/$repo/security"
    echo
    echo "----------------------------------------"
done

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ SECRETS SETUP GUIDE COMPLETE!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 Next Actions:${NC}"
echo -e "  1. Add secrets to each repository manually"
echo -e "  2. Test CI/CD workflows with sample commits"
echo -e "  3. Set up monitoring and alerting"
echo -e "  4. Deploy to staging environment"
echo
echo -e "${CYAN}⏱️  Estimated time to complete: 15-30 minutes${NC}"
echo
echo -e "${PURPLE}🎉 Once secrets are configured, your V5 CI/CD will be fully operational!${NC}"
