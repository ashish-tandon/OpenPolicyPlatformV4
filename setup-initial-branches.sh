#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Initial Branch Setup

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
echo -e "${BLUE}🌿 Setting up Initial Branches for V5 Repositories${NC}"
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

echo -e "${CYAN}Setting up initial branches for ${#REPOS[@]} repositories...${NC}"
echo

for repo in "${REPOS[@]}"; do
    echo -e "${YELLOW}🌿 Setting up branches for $repo...${NC}"
    
    # Create develop branch
    echo -e "${CYAN}Creating develop branch...${NC}"
    gh api repos/$ORG/$repo/branches \
        --method POST \
        --field name=develop \
        --field source=main \
        --silent
    
    echo -e "${GREEN}✅ Develop branch created${NC}"
    
    # Create feature branch
    echo -e "${CYAN}Creating feature branch...${NC}"
    gh api repos/$ORG/$repo/branches \
        --method POST \
        --field name=feature/initial-setup \
        --field source=main \
        --silent
    
    echo -e "${GREEN}✅ Feature branch created${NC}"
    
    # Create hotfix branch
    echo -e "${CYAN}Creating hotfix branch...${NC}"
    gh api repos/$ORG/$repo/branches \
        --method POST \
        --field name=hotfix/initial-setup \
        --field source=main \
        --silent
    
    echo -e "${GREEN}✅ Hotfix branch created${NC}"
    
    echo -e "${GREEN}✅ $repo branches setup complete${NC}"
    echo "----------------------------------------"
done

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ INITIAL BRANCH SETUP COMPLETE!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 What was created:${NC}"
echo -e "  ✅ develop branch - for staging deployments"
echo -e "  ✅ feature/initial-setup - for development work"
echo -e "  ✅ hotfix/initial-setup - for emergency fixes"
echo
echo -e "${CYAN}🚀 Next steps:${NC}"
echo -e "  1. Set up branch protection rules"
echo -e "  2. Configure repository secrets"
echo -e "  3. Test CI/CD workflows"
echo
echo -e "${PURPLE}🎉 Your V5 repositories now have proper branch structure!${NC}"
