#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Repository Secrets Setup Guide

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
echo -e "${BLUE}🔐 Repository Secrets Setup Guide${NC}"
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

echo -e "${YELLOW}⚠️  IMPORTANT: You need to add these secrets to each repository manually${NC}"
echo -e "${YELLOW}   This script will show you exactly what to do${NC}"
echo

echo -e "${CYAN}📋 Required Secrets for Each Repository:${NC}"
echo "=================================================="

# Core secrets needed
# Core secrets needed
SECRETS_REPO_SYNC_TOKEN="GitHub token for cross-repository synchronization"
SECRETS_DOCKER_REGISTRY_TOKEN="Token for GitHub Container Registry access"
SECRETS_DEV_SSH_PRIVATE_KEY="SSH private key for laptop deployment"
SECRETS_DEV_SSH_USER="SSH username for laptop (usually your username)"
SECRETS_DEV_SSH_HOST="SSH hostname for laptop (localhost or 127.0.0.1)"
SECRETS_QNAP_SSH_PRIVATE_KEY="SSH private key for QNAP staging server"
SECRETS_QNAP_SSH_USER="SSH username for QNAP (usually admin)"
SECRETS_QNAP_SSH_HOST="QNAP server IP address (e.g., 192.168.1.100)"
SECRETS_AZURE_CREDENTIALS="Azure service principal credentials (JSON)"
SECRETS_AZURE_RESOURCE_GROUP="Azure resource group name for production"
SECRETS_AZURE_AKS_CLUSTER="Azure Kubernetes cluster name"

echo -e "${YELLOW}📋 Required Secrets for Each Repository:${NC}"
echo "=================================================="

echo -e "${CYAN}🔐 REPO_SYNC_TOKEN${NC}"
echo -e "   ${SECRETS_REPO_SYNC_TOKEN}"
echo
echo -e "${CYAN}🔐 DOCKER_REGISTRY_TOKEN${NC}"
echo -e "   ${SECRETS_DOCKER_REGISTRY_TOKEN}"
echo
echo -e "${CYAN}🔐 DEV_SSH_PRIVATE_KEY${NC}"
echo -e "   ${SECRETS_DEV_SSH_PRIVATE_KEY}"
echo
echo -e "${CYAN}🔐 DEV_SSH_USER${NC}"
echo -e "   ${SECRETS_DEV_SSH_USER}"
echo
echo -e "${CYAN}🔐 DEV_SSH_HOST${NC}"
echo -e "   ${SECRETS_DEV_SSH_HOST}"
echo
echo -e "${CYAN}🔐 QNAP_SSH_PRIVATE_KEY${NC}"
echo -e "   ${SECRETS_QNAP_SSH_PRIVATE_KEY}"
echo
echo -e "${CYAN}🔐 QNAP_SSH_USER${NC}"
echo -e "   ${SECRETS_QNAP_SSH_USER}"
echo
echo -e "${CYAN}🔐 QNAP_SSH_HOST${NC}"
echo -e "   ${SECRETS_QNAP_SSH_HOST}"
echo
echo -e "${CYAN}🔐 AZURE_CREDENTIALS${NC}"
echo -e "   ${SECRETS_AZURE_CREDENTIALS}"
echo
echo -e "${CYAN}🔐 AZURE_RESOURCE_GROUP${NC}"
echo -e "   ${SECRETS_AZURE_RESOURCE_GROUP}"
echo
echo -e "${CYAN}🔐 AZURE_AKS_CLUSTER${NC}"
echo -e "   ${SECRETS_AZURE_AKS_CLUSTER}"
echo

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
echo -e "${GREEN}🔐 SECRET VALUES TO SET${NC}"
echo -e "${GREEN}==================================================${NC}"
echo

echo -e "${CYAN}1. REPO_SYNC_TOKEN${NC}"
echo "   Generate a GitHub Personal Access Token with 'repo' scope"
echo "   Go to: https://github.com/settings/tokens"
echo "   Copy the token and use it for all repositories"
echo

echo -e "${CYAN}2. DOCKER_REGISTRY_TOKEN${NC}"
echo "   Use the same GitHub token as REPO_SYNC_TOKEN"
echo "   This allows access to GitHub Container Registry"
echo

echo -e "${CYAN}3. DEV_SSH_PRIVATE_KEY${NC}"
echo "   Your SSH private key for laptop access"
echo "   Usually located at: ~/.ssh/id_rsa or ~/.ssh/id_ed25519"
echo "   Copy the entire key including BEGIN and END lines"
echo

echo -e "${CYAN}4. DEV_SSH_USER${NC}"
echo "   Your laptop username: ashishtandon"
echo

echo -e "${CYAN}5. DEV_SSH_HOST${NC}"
echo "   Your laptop hostname: localhost or 127.0.0.1"
echo

echo -e "${CYAN}6. QNAP_SSH_PRIVATE_KEY${NC}"
echo "   SSH private key for QNAP NAS access"
echo "   Generate a new key pair for QNAP access"
echo "   ssh-keygen -t ed25519 -f ~/.ssh/qnap_key"
echo

echo -e "${CYAN}7. QNAP_SSH_USER${NC}"
echo "   QNAP admin username: admin"
echo

echo -e "${CYAN}8. QNAP_SSH_HOST${NC}"
echo "   QNAP server IP address (e.g., 192.168.1.100)"
echo "   Find this in your router admin panel or QNAP interface"
echo

echo -e "${CYAN}9. AZURE_CREDENTIALS${NC}"
echo "   Azure service principal JSON credentials"
echo "   Create with: az ad sp create-for-rbac --name openpolicy-platform"
echo "   Copy the entire JSON output"
echo

echo -e "${CYAN}10. AZURE_RESOURCE_GROUP${NC}"
echo "    Azure resource group name: openpolicy-platform-prod"
echo

echo -e "${CYAN}11. AZURE_AKS_CLUSTER${NC}"
echo "    Azure Kubernetes cluster name: aks-openpolicy-platform"
echo

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
echo -e "${CYAN}⏱️  Estimated time to complete: 30-60 minutes${NC}"
echo
echo -e "${PURPLE}🎉 Once secrets are configured, your V5 CI/CD will be fully operational!${NC}"
