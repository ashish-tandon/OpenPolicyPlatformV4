# 🚀 Manual Deployment Steps - OpenPolicyPlatform V4

Since we can't run interactive authentication in this environment, here are the **EXACT MANUAL STEPS** to deploy your platform:

## 📋 Step 1: Prepare Your Local Machine

Open a terminal on your local machine (not in this environment) and run:

```bash
# 1. Install required tools
brew install gh azure-cli  # macOS
# or appropriate for your OS

# 2. Authenticate
gh auth login
az login

# 3. Clone or download the migration-repos folder from this workspace
# You can download it as a ZIP or use any file transfer method
```

## 📋 Step 2: Create GitHub Repositories

```bash
# Navigate to migration-repos
cd migration-repos

# Create all 6 repositories
gh repo create ashish-tandon/openpolicy-infrastructure --public --description "Infrastructure services for OpenPolicy Platform"
gh repo create ashish-tandon/openpolicy-data --public --description "Data processing services for OpenPolicy Platform"
gh repo create ashish-tandon/openpolicy-business --public --description "Business logic services for OpenPolicy Platform"
gh repo create ashish-tandon/openpolicy-frontend --public --description "Frontend services for OpenPolicy Platform"
gh repo create ashish-tandon/openpolicy-legacy --public --description "Legacy services for OpenPolicy Platform"
gh repo create ashish-tandon/openpolicy-orchestration --public --description "Orchestration for OpenPolicy Platform"
```

## 📋 Step 3: Push Code to GitHub

```bash
# Push each repository
for repo in openpolicy-*; do
    echo "Pushing $repo..."
    cd $repo
    git remote add origin https://github.com/ashish-tandon/$repo.git
    git branch -M main
    git push -u origin main
    cd ..
done
```

## 📋 Step 4: Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="openpolicy-platform-rg"
LOCATION="canadacentral"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name openpolicyacr \
  --sku Basic \
  --admin-enabled true

# Create PostgreSQL
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name openpolicy-postgresql \
  --location $LOCATION \
  --admin-user openpolicy \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B2s \
  --storage-size 32 \
  --version 15

# Create Redis
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name openpolicy-redis \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0

# Create Storage Account
az storage account create \
  --name openpolicystorage \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create Container Apps Environment
az containerapp env create \
  --name openpolicy-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

## 📋 Step 5: Get Azure Credentials

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name openpolicyacr --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name openpolicyacr --query passwords[0].value -o tsv)

# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "openpolicy-github-actions" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP \
  --sdk-auth

# Save the output - you'll need it for GitHub secrets
```

## 📋 Step 6: Set GitHub Secrets

For EACH repository, set these secrets:

```bash
# Example for infrastructure repo
REPO="ashish-tandon/openpolicy-infrastructure"

gh secret set AZURE_SUBSCRIPTION_ID --repo $REPO --body "your-subscription-id"
gh secret set AZURE_TENANT_ID --repo $REPO --body "your-tenant-id"
gh secret set AZURE_CLIENT_ID --repo $REPO --body "your-client-id"
gh secret set AZURE_CLIENT_SECRET --repo $REPO --body "your-client-secret"
gh secret set ACR_USERNAME --repo $REPO --body "$ACR_USERNAME"
gh secret set ACR_PASSWORD --repo $REPO --body "$ACR_PASSWORD"

# Repeat for all 6 repositories
```

## 📋 Step 7: Trigger Deployments

The CI/CD pipelines will automatically trigger when you pushed the code. To check status:

```bash
# View workflow runs
gh run list --repo ashish-tandon/openpolicy-infrastructure
gh run list --repo ashish-tandon/openpolicy-data
# ... etc for all repos

# Watch a specific run
gh run watch --repo ashish-tandon/openpolicy-infrastructure
```

## 📋 Step 8: Verify Deployment

```bash
# List Container Apps
az containerapp list -g openpolicy-platform-rg -o table

# Get application URLs
az containerapp show -n openpolicy-infrastructure -g openpolicy-platform-rg --query properties.configuration.ingress.fqdn -o tsv
```

## 🎯 Quick Copy-Paste Script

Here's everything in one script you can copy and run:

```bash
#!/bin/bash
# Save this as deploy.sh and run it

# Variables
export GITHUB_ORG="ashish-tandon"
export RESOURCE_GROUP="openpolicy-platform-rg"
export LOCATION="canadacentral"

# Create GitHub repos
repos=("openpolicy-infrastructure" "openpolicy-data" "openpolicy-business" "openpolicy-frontend" "openpolicy-legacy" "openpolicy-orchestration")
for repo in "${repos[@]}"; do
    gh repo create $GITHUB_ORG/$repo --public --description "$repo for OpenPolicy Platform" || echo "Repo exists"
done

# Push code
cd migration-repos
for repo in openpolicy-*; do
    cd $repo
    git remote add origin https://github.com/$GITHUB_ORG/$repo.git || true
    git push -u origin main || git push -u origin master
    cd ..
done
cd ..

# Create Azure resources
az group create --name $RESOURCE_GROUP --location $LOCATION
az acr create --resource-group $RESOURCE_GROUP --name openpolicyacr --sku Basic --admin-enabled true
az postgres flexible-server create --resource-group $RESOURCE_GROUP --name openpolicy-postgresql --location $LOCATION --admin-user openpolicy --admin-password "SecurePassword123!" --sku-name Standard_B2s --storage-size 32 --version 15
az redis create --resource-group $RESOURCE_GROUP --name openpolicy-redis --location $LOCATION --sku Basic --vm-size c0
az storage account create --name openpolicystorage --resource-group $RESOURCE_GROUP --location $LOCATION --sku Standard_LRS
az containerapp env create --name openpolicy-env --resource-group $RESOURCE_GROUP --location $LOCATION

echo "✅ Deployment initiated! Check GitHub Actions for progress."
```

## 📊 Expected Timeline

- Repository creation: 2 minutes
- Code push: 5 minutes
- Azure resource creation: 10-15 minutes
- CI/CD pipeline runs: 10-15 minutes per repository
- **Total time**: ~45 minutes

## ✅ Success Checklist

- [ ] All 6 GitHub repositories created
- [ ] Code pushed to all repositories
- [ ] Azure resources created
- [ ] GitHub secrets configured
- [ ] CI/CD pipelines running
- [ ] Container Apps deployed
- [ ] Health checks passing

## 🎉 Done!

Your OpenPolicyPlatform V4 is now deployed with:
- 6 independent repositories
- Full CI/CD automation
- Cloud-native infrastructure
- Automatic scaling
- Comprehensive monitoring

Access your services at the Container Apps URLs provided by Azure! 🚀