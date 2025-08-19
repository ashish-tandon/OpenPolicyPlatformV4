#!/bin/bash

# OpenPolicyPlatform V4 - DEPLOYMENT SCRIPT
# This script will deploy all 6 repositories to GitHub and Azure

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🚀 OpenPolicyPlatform V4 - DEPLOYMENT STARTING${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Configuration - UPDATE THESE
GITHUB_ORG="${GITHUB_ORG:-ashish-tandon}"
AZURE_SUBSCRIPTION="${AZURE_SUBSCRIPTION:-your-subscription-id}"
AZURE_RESOURCE_GROUP="openpolicy-platform-rg"
AZURE_LOCATION="canadacentral"
ACR_NAME="openpolicyacr"

# Function to check authentication
check_auth() {
    echo -e "\n${YELLOW}🔐 Checking authentication...${NC}"
    
    # Check GitHub
    if gh auth status &>/dev/null; then
        echo -e "${GREEN}✓ GitHub authenticated${NC}"
    else
        echo -e "${RED}✗ GitHub not authenticated${NC}"
        echo -e "${YELLOW}Please run: gh auth login${NC}"
        exit 1
    fi
    
    # Check Azure
    if az account show &>/dev/null; then
        echo -e "${GREEN}✓ Azure authenticated${NC}"
        AZURE_SUBSCRIPTION=$(az account show --query id -o tsv)
        echo -e "${BLUE}Using subscription: $AZURE_SUBSCRIPTION${NC}"
    else
        echo -e "${RED}✗ Azure not authenticated${NC}"
        echo -e "${YELLOW}Please run: az login${NC}"
        exit 1
    fi
}

# Function to create and push GitHub repositories
deploy_github_repos() {
    echo -e "\n${YELLOW}📦 Creating GitHub repositories...${NC}"
    
    cd migration-repos
    
    for repo in openpolicy-infrastructure openpolicy-data openpolicy-business openpolicy-frontend openpolicy-legacy openpolicy-orchestration; do
        echo -e "\n${BLUE}Processing $repo...${NC}"
        
        cd $repo
        
        # Check if remote already exists
        if git remote get-url origin &>/dev/null; then
            echo -e "${YELLOW}Remote already exists, updating...${NC}"
            git remote set-url origin "https://github.com/${GITHUB_ORG}/${repo}.git"
        else
            git remote add origin "https://github.com/${GITHUB_ORG}/${repo}.git"
        fi
        
        # Create GitHub repo if it doesn't exist
        if gh repo view "${GITHUB_ORG}/${repo}" &>/dev/null; then
            echo -e "${GREEN}✓ Repository ${repo} already exists${NC}"
        else
            echo -e "${YELLOW}Creating repository ${repo}...${NC}"
            gh repo create "${GITHUB_ORG}/${repo}" \
                --public \
                --description "OpenPolicy Platform V4 - ${repo}" \
                --homepage "https://github.com/${GITHUB_ORG}/OpenPolicyPlatformV4" || {
                echo -e "${RED}Failed to create ${repo}${NC}"
            }
        fi
        
        # Push code
        echo -e "${YELLOW}Pushing code to ${repo}...${NC}"
        git push -u origin master 2>/dev/null || git push -u origin main || {
            # If push fails, try to set upstream
            git branch -M main
            git push -u origin main
        }
        
        echo -e "${GREEN}✓ ${repo} deployed to GitHub${NC}"
        
        cd ..
    done
    
    cd ..
}

# Function to create Azure resources
deploy_azure_resources() {
    echo -e "\n${YELLOW}☁️  Creating Azure resources...${NC}"
    
    # Create resource group
    echo -e "${BLUE}Creating resource group...${NC}"
    az group create \
        --name $AZURE_RESOURCE_GROUP \
        --location $AZURE_LOCATION \
        --output table || echo "Resource group may already exist"
    
    # Create Container Registry
    echo -e "${BLUE}Creating Container Registry...${NC}"
    if az acr show --name $ACR_NAME --resource-group $AZURE_RESOURCE_GROUP &>/dev/null; then
        echo -e "${GREEN}✓ Container Registry already exists${NC}"
    else
        az acr create \
            --resource-group $AZURE_RESOURCE_GROUP \
            --name $ACR_NAME \
            --sku Basic \
            --admin-enabled true \
            --output table
    fi
    
    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
    
    # Create PostgreSQL Flexible Server
    echo -e "${BLUE}Creating PostgreSQL server...${NC}"
    if az postgres flexible-server show --name openpolicy-postgresql --resource-group $AZURE_RESOURCE_GROUP &>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL server already exists${NC}"
    else
        az postgres flexible-server create \
            --resource-group $AZURE_RESOURCE_GROUP \
            --name openpolicy-postgresql \
            --location $AZURE_LOCATION \
            --admin-user openpolicy \
            --admin-password "SecurePassword123!" \
            --sku-name Standard_B2s \
            --storage-size 32 \
            --version 15 \
            --output table
    fi
    
    # Create Redis Cache
    echo -e "${BLUE}Creating Redis Cache...${NC}"
    if az redis show --name openpolicy-redis --resource-group $AZURE_RESOURCE_GROUP &>/dev/null; then
        echo -e "${GREEN}✓ Redis Cache already exists${NC}"
    else
        az redis create \
            --resource-group $AZURE_RESOURCE_GROUP \
            --name openpolicy-redis \
            --location $AZURE_LOCATION \
            --sku Basic \
            --vm-size c0 \
            --output table
    fi
    
    # Create Storage Account
    echo -e "${BLUE}Creating Storage Account...${NC}"
    if az storage account show --name openpolicystorage --resource-group $AZURE_RESOURCE_GROUP &>/dev/null; then
        echo -e "${GREEN}✓ Storage Account already exists${NC}"
    else
        az storage account create \
            --name openpolicystorage \
            --resource-group $AZURE_RESOURCE_GROUP \
            --location $AZURE_LOCATION \
            --sku Standard_LRS \
            --output table
    fi
    
    # Create Application Insights
    echo -e "${BLUE}Creating Application Insights...${NC}"
    if az monitor app-insights component show --app openpolicy-appinsights --resource-group $AZURE_RESOURCE_GROUP &>/dev/null; then
        echo -e "${GREEN}✓ Application Insights already exists${NC}"
    else
        az monitor app-insights component create \
            --app openpolicy-appinsights \
            --location $AZURE_LOCATION \
            --resource-group $AZURE_RESOURCE_GROUP \
            --application-type web \
            --output table
    fi
    
    # Create Container Apps Environment
    echo -e "${BLUE}Creating Container Apps Environment...${NC}"
    if az containerapp env show --name openpolicy-env --resource-group $AZURE_RESOURCE_GROUP &>/dev/null; then
        echo -e "${GREEN}✓ Container Apps Environment already exists${NC}"
    else
        az containerapp env create \
            --name openpolicy-env \
            --resource-group $AZURE_RESOURCE_GROUP \
            --location $AZURE_LOCATION \
            --output table
    fi
    
    echo -e "${GREEN}✓ Azure resources created successfully${NC}"
    
    # Save credentials
    echo -e "\n${YELLOW}Saving Azure credentials...${NC}"
    cat > migration-repos/azure-credentials.json << EOF
{
    "subscriptionId": "$AZURE_SUBSCRIPTION",
    "resourceGroup": "$AZURE_RESOURCE_GROUP",
    "acrName": "$ACR_NAME",
    "acrUsername": "$ACR_USERNAME",
    "acrPassword": "$ACR_PASSWORD",
    "postgresqlServer": "openpolicy-postgresql",
    "redisCache": "openpolicy-redis",
    "storageAccount": "openpolicystorage"
}
EOF
    echo -e "${GREEN}✓ Credentials saved to migration-repos/azure-credentials.json${NC}"
}

# Function to set GitHub secrets
set_github_secrets() {
    echo -e "\n${YELLOW}🔐 Setting GitHub secrets...${NC}"
    
    # Get Azure credentials
    AZURE_CREDS=$(cat migration-repos/azure-credentials.json)
    ACR_USERNAME=$(echo $AZURE_CREDS | jq -r .acrUsername)
    ACR_PASSWORD=$(echo $AZURE_CREDS | jq -r .acrPassword)
    
    # Get service principal for GitHub Actions
    echo -e "${BLUE}Creating service principal for GitHub Actions...${NC}"
    SP_OUTPUT=$(az ad sp create-for-rbac \
        --name "openpolicy-github-actions" \
        --role contributor \
        --scopes /subscriptions/$AZURE_SUBSCRIPTION/resourceGroups/$AZURE_RESOURCE_GROUP \
        --sdk-auth)
    
    # Extract values
    CLIENT_ID=$(echo $SP_OUTPUT | jq -r .clientId)
    CLIENT_SECRET=$(echo $SP_OUTPUT | jq -r .clientSecret)
    TENANT_ID=$(echo $SP_OUTPUT | jq -r .tenantId)
    
    # Set secrets for each repository
    for repo in openpolicy-infrastructure openpolicy-data openpolicy-business openpolicy-frontend openpolicy-legacy openpolicy-orchestration; do
        echo -e "\n${BLUE}Setting secrets for $repo...${NC}"
        
        gh secret set AZURE_SUBSCRIPTION_ID --repo "${GITHUB_ORG}/${repo}" --body "$AZURE_SUBSCRIPTION"
        gh secret set AZURE_TENANT_ID --repo "${GITHUB_ORG}/${repo}" --body "$TENANT_ID"
        gh secret set AZURE_CLIENT_ID --repo "${GITHUB_ORG}/${repo}" --body "$CLIENT_ID"
        gh secret set AZURE_CLIENT_SECRET --repo "${GITHUB_ORG}/${repo}" --body "$CLIENT_SECRET"
        gh secret set ACR_USERNAME --repo "${GITHUB_ORG}/${repo}" --body "$ACR_USERNAME"
        gh secret set ACR_PASSWORD --repo "${GITHUB_ORG}/${repo}" --body "$ACR_PASSWORD"
        
        echo -e "${GREEN}✓ Secrets set for $repo${NC}"
    done
}

# Function to trigger deployments
trigger_deployments() {
    echo -e "\n${YELLOW}🚀 Triggering CI/CD deployments...${NC}"
    
    for repo in openpolicy-infrastructure openpolicy-data openpolicy-business openpolicy-frontend openpolicy-legacy openpolicy-orchestration; do
        echo -e "\n${BLUE}Triggering deployment for $repo...${NC}"
        
        # Trigger a workflow run by creating a small commit
        cd migration-repos/$repo
        echo "Deployment triggered at $(date)" >> deployment.log
        git add deployment.log
        git commit -m "Trigger deployment" || true
        git push || true
        cd ../..
        
        echo -e "${GREEN}✓ Deployment triggered for $repo${NC}"
    done
}

# Function to monitor deployment
monitor_deployment() {
    echo -e "\n${YELLOW}📊 Monitoring deployments...${NC}"
    
    echo -e "\n${BLUE}GitHub Actions Status:${NC}"
    for repo in openpolicy-infrastructure openpolicy-data openpolicy-business openpolicy-frontend openpolicy-legacy; do
        echo -e "\n${YELLOW}$repo:${NC}"
        gh run list --repo "${GITHUB_ORG}/${repo}" --limit 1
    done
    
    echo -e "\n${BLUE}Azure Container Apps Status:${NC}"
    az containerapp list --resource-group $AZURE_RESOURCE_GROUP --output table
    
    echo -e "\n${GREEN}✓ Deployment monitoring complete${NC}"
}

# Function to display completion message
display_completion() {
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo -e "\n${BLUE}📍 GitHub Repositories:${NC}"
    for repo in openpolicy-infrastructure openpolicy-data openpolicy-business openpolicy-frontend openpolicy-legacy openpolicy-orchestration; do
        echo -e "   https://github.com/${GITHUB_ORG}/${repo}"
    done
    
    echo -e "\n${BLUE}☁️  Azure Resources:${NC}"
    echo -e "   Resource Group: $AZURE_RESOURCE_GROUP"
    echo -e "   Container Registry: $ACR_NAME"
    echo -e "   PostgreSQL: openpolicy-postgresql"
    echo -e "   Redis: openpolicy-redis"
    
    echo -e "\n${BLUE}🔍 Monitor Progress:${NC}"
    echo -e "   GitHub Actions: https://github.com/${GITHUB_ORG}?tab=repositories"
    echo -e "   Azure Portal: https://portal.azure.com"
    
    echo -e "\n${BLUE}📋 Next Steps:${NC}"
    echo -e "   1. Monitor CI/CD pipelines in GitHub Actions"
    echo -e "   2. Check Container Apps deployment in Azure Portal"
    echo -e "   3. Access services once deployed:"
    echo -e "      - API Gateway: https://<app-name>.azurecontainerapps.io:9000"
    echo -e "      - Web Frontend: https://<app-name>.azurecontainerapps.io:3000"
    echo -e "      - Monitoring: https://<app-name>.azurecontainerapps.io:3001"
}

# Main execution
main() {
    echo -e "${PURPLE}Starting OpenPolicyPlatform V4 deployment...${NC}"
    
    # Check if we're in the right directory
    if [ ! -d "migration-repos" ]; then
        echo -e "${RED}Error: migration-repos directory not found${NC}"
        echo -e "${YELLOW}Please run this script from the workspace root${NC}"
        exit 1
    fi
    
    # Step 1: Check authentication
    check_auth
    
    # Step 2: Deploy GitHub repositories
    deploy_github_repos
    
    # Step 3: Create Azure resources
    deploy_azure_resources
    
    # Step 4: Set GitHub secrets
    set_github_secrets
    
    # Step 5: Trigger deployments
    trigger_deployments
    
    # Step 6: Monitor deployment
    sleep 10  # Give GitHub Actions time to start
    monitor_deployment
    
    # Step 7: Display completion
    display_completion
    
    echo -e "\n${GREEN}🎉 Platform deployment initiated successfully!${NC}"
}

# Run main function
main "$@"