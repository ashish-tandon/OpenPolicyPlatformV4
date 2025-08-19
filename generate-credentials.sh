#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Credentials Generation

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
echo -e "${BLUE}🔑 Generating Credentials for V5 CI/CD Setup${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Create credentials directory
mkdir -p credentials
cd credentials

echo -e "${CYAN}🔐 Step 1: Generating SSH Keys${NC}"
echo "=================================================="

# Generate SSH key for laptop (if doesn't exist)
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo -e "${YELLOW}Generating SSH key for laptop...${NC}"
    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N "" -C "ashishtandon@laptop"
    echo -e "${GREEN}✅ Laptop SSH key generated${NC}"
else
    echo -e "${GREEN}✅ Laptop SSH key already exists${NC}"
fi

# Generate SSH key for QNAP
echo -e "${YELLOW}Generating SSH key for QNAP...${NC}"
ssh-keygen -t ed25519 -f ~/.ssh/qnap_key -N "" -C "admin@qnap-staging"
echo -e "${GREEN}✅ QNAP SSH key generated${NC}"

# Copy public keys to credentials directory
echo -e "${CYAN}Copying public keys...${NC}"
cp ~/.ssh/id_ed25519.pub credentials/laptop_public_key.pem
cp ~/.ssh/qnap_key.pub credentials/qnap_public_key.pem

echo -e "${GREEN}✅ SSH keys setup complete${NC}"
echo

echo -e "${CYAN}🔐 Step 2: Azure Credentials Setup${NC}"
echo "=================================================="

echo -e "${YELLOW}⚠️  Note: Azure CLI must be installed and logged in${NC}"
echo -e "${YELLOW}   Run: az login (if not already logged in)${NC}"
echo

# Check if Azure CLI is available
if command -v az &> /dev/null; then
    echo -e "${GREEN}✅ Azure CLI found${NC}"
    
    # Check if logged in
    if az account show &> /dev/null; then
        echo -e "${GREEN}✅ Azure CLI logged in${NC}"
        
        echo -e "${CYAN}Creating Azure service principal...${NC}"
        echo -e "${YELLOW}This will create a service principal for CI/CD access${NC}"
        
        # Create service principal
        az ad sp create-for-rbac \
            --name "openpolicy-platform-v5" \
            --role contributor \
            --scopes /subscriptions/$(az account show --query id -o tsv) \
            --sdk-auth > azure_credentials.json
        
        echo -e "${GREEN}✅ Azure service principal created${NC}"
        echo -e "${CYAN}Credentials saved to: azure_credentials.json${NC}"
        
        # Extract resource group and cluster names
        echo -e "${CYAN}Suggested Azure resource names:${NC}"
        echo "Resource Group: openpolicy-platform-v5-prod"
        echo "AKS Cluster: aks-openpolicy-platform-v5"
        echo "Key Vault: openpolicy-platform-v5-kv"
        
    else
        echo -e "${RED}❌ Azure CLI not logged in${NC}"
        echo -e "${YELLOW}Please run: az login${NC}"
    fi
else
    echo -e "${RED}❌ Azure CLI not found${NC}"
    echo -e "${YELLOW}Please install Azure CLI first${NC}"
    echo -e "${CYAN}Installation: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${NC}"
fi

echo

echo -e "${CYAN}🔐 Step 3: GitHub Token Setup${NC}"
echo "=================================================="

echo -e "${YELLOW}⚠️  You need to create a GitHub Personal Access Token manually${NC}"
echo -e "${CYAN}Steps:${NC}"
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Give it a name: 'OpenPolicyPlatform V5 CI/CD'"
echo "4. Set expiration: 90 days (or as needed)"
echo "5. Select scopes:"
echo "   - repo (Full control of private repositories)"
echo "   - workflow (Update GitHub Action workflows)"
echo "   - write:packages (Upload packages to GitHub Package Registry)"
echo "6. Click 'Generate token'"
echo "7. Copy the token (you won't see it again!)"
echo

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ CREDENTIALS GENERATION COMPLETE!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 Generated Files:${NC}"
echo -e "  ✅ ~/.ssh/id_ed25519 (Laptop SSH private key)"
echo -e "  ✅ ~/.ssh/id_ed25519.pub (Laptop SSH public key)"
echo -e "  ✅ ~/.ssh/qnap_key (QNAP SSH private key)"
echo -e "  ✅ ~/.ssh/qnap_key.pub (QNAP SSH public key)"
echo -e "  ✅ credentials/laptop_public_key.pem"
echo -e "  ✅ credentials/qnap_public_key.pem"
echo -e "  ✅ credentials/azure_credentials.json (if Azure CLI available)"
echo
echo -e "${CYAN}🚀 Next Steps:${NC}"
echo -e "  1. Copy the GitHub token when you create it"
echo -e "  2. Add all credentials to repository secrets"
echo -e "  3. Set up branch protection"
echo -e "  4. Test CI/CD workflows"
echo
echo -e "${PURPLE}🎉 Your credentials are ready for V5 CI/CD setup!${NC}"
echo
echo -e "${YELLOW}📝 Important Notes:${NC}"
echo -e "  • Keep your SSH private keys secure"
echo -e "  • Add the public keys to your laptop and QNAP"
echo -e "  • The GitHub token will be used for all repositories"
echo -e "  • Azure credentials are in JSON format for easy copying"
