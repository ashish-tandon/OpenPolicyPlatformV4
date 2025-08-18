#!/bin/bash

# Open Policy Platform V4 - Local Azure Deployment Preparation
# This script prepares the platform for deployment to Azure

set -e

echo "🚀 Open Policy Platform V4 - Azure Deployment Preparation"
echo "========================================================="

# Configuration
COMPOSE_FILE="docker-compose.azure.yml"
ENV_FILE=".env.azure"
CONFIG_FILE="azure-config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Azure CLI
check_azure_cli() {
    print_status "Checking Azure CLI installation..."
    
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI not found"
        print_status "Please install Azure CLI:"
        echo "  macOS: brew install azure-cli"
        echo "  Ubuntu: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
        echo "  Windows: Download from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    print_success "Azure CLI found: $(az version --query '\"azure-cli\"' -o tsv)"
}

# Check Azure login
check_azure_login() {
    print_status "Checking Azure login status..."
    
    if ! az account show &> /dev/null; then
        print_warning "Not logged into Azure"
        print_status "Please login with: az login"
        print_warning "You will need to authenticate in your browser"
    else
        print_success "Azure login verified"
        print_status "Current subscription: $(az account show --query name -o tsv)"
    fi
}

# Create Azure environment file
create_azure_env() {
    print_status "Creating Azure environment file..."
    
    cat > "$ENV_FILE" << EOF
# Open Policy Platform V4 - Azure Environment Configuration
# Update these values with your Azure resource details

# Database Configuration (Azure Database for PostgreSQL)
DATABASE_URL=postgresql://openpolicy:your_password@your-server.postgres.database.azure.com:5432/openpolicy?sslmode=require
REDIS_URL=redis://your-redis-host:6380?ssl=true&password=your_redis_password

# Security Configuration
JWT_SECRET=openpolicy_production_jwt_secret_2024_secure_32_chars
JWT_EXPIRY_MINUTES=30
JWT_REFRESH_EXPIRY_DAYS=7
SECRET_KEY=openpolicy_production_secret_key_2024_secure_32_chars

# Auth0 Configuration
AUTH0_DOMAIN=dev-openpolicy.ca.auth0.com
AUTH0_CLIENT_ID=zR9zxYpZnRjaMHUfIOTUx9BSMfOekrnG
AUTH0_CLIENT_SECRET=tVfKcn-qUhC9d3v0ihtICtWxgAhMlLeMCwWZBIS2jXTrph72nf4m7kZ1Q4VqO5yo
AUTH0_AUDIENCE=https://api.openpolicy.com

# System Configuration
SYSTEM_ADMIN_EMAIL=ashish.tandon@openpolicy.me
LOG_LEVEL=INFO
ENVIRONMENT=production

# CORS Configuration
ALLOWED_HOSTS=["your-azure-domain.com","localhost","127.0.0.1"]
ALLOWED_ORIGINS=["https://your-azure-domain.com","http://localhost:3000"]

# Umami Analytics Configuration
UMAMI_WEBSITE_ID=your_umami_website_id
UMAMI_API_URL=https://your-umami-instance.com/api
UMAMI_USERNAME=ashish.tandon@openpolicy.me
UMAMI_PASSWORD=nrt2rfv!mwc1NUH8fra

# Azure Specific Configuration
AZURE_SUBSCRIPTION_ID=5602b849-384e-4da7-8b75-fd5eb70ea355
AZURE_RESOURCE_GROUP=openpolicy-platform-rg
AZURE_LOCATION=canadacentral
AZURE_ACR_NAME=openpolicyacr
AZURE_APP_SERVICE_PLAN=openpolicy-asp
AZURE_WEB_APP_NAME=openpolicy-platform
EOF

    print_success "Azure environment file created: $ENV_FILE"
}

# Create deployment instructions
create_deployment_instructions() {
    print_status "Creating Azure deployment instructions..."
    
    cat > "AZURE_DEPLOYMENT_INSTRUCTIONS.md" << EOF
# 🚀 Open Policy Platform V4 - Azure Deployment Instructions

## 📋 Prerequisites
1. Azure subscription (ID: 5602b849-384e-4da7-8b75-fd5eb70ea355)
2. Azure CLI installed and configured
3. Docker installed locally
4. PostgreSQL client tools (for database import)

## 🔐 Azure Authentication
\`\`\`bash
# Login to Azure
az login

# Set subscription
az account set --subscription 5602b849-384e-4da7-8b75-fd5eb70ea355
\`\`\`

## 🏗️ Azure Resource Creation

### 1. Create Resource Group
\`\`\`bash
az group create --name openpolicy-platform-rg --location canadacentral
\`\`\`

### 2. Create Azure Container Registry (ACR)
\`\`\`bash
az acr create --resource-group openpolicy-platform-rg \
  --name openpolicyacr --sku Basic

# Login to ACR
az acr login --name openpolicyacr
\`\`\`

### 3. Create Azure Database for PostgreSQL
\`\`\`bash
az postgres flexible-server create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgres \
  --location canadacentral \
  --admin-user openpolicy \
  --admin-password "your_secure_password" \
  --sku-name Standard_B1ms \
  --version 14 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group openpolicy-platform-rg \
  --server-name openpolicy-postgres \
  --database-name openpolicy
\`\`\`

### 4. Create Azure Cache for Redis
\`\`\`bash
az redis create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-redis \
  --location canadacentral \
  --sku Basic --vm-size c0
\`\`\`

### 5. Create App Service Plan
\`\`\`bash
az appservice plan create \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-asp \
  --location canadacentral \
  --sku B1 --is-linux
\`\`\`

## 🐳 Docker Image Building & Pushing

### 1. Build Images
\`\`\`bash
# Build API image
docker build -t openpolicyacr.azurecr.io/openpolicy-api:latest ./backend

# Build Web image
docker build -t openpolicyacr.azurecr.io/openpolicy-web:latest ./web
\`\`\`

### 2. Push to ACR
\`\`\`bash
# Push API image
docker push openpolicyacr.azurecr.io/openpolicy-api:latest

# Push Web image
docker push openpolicyacr.azurecr.io/openpolicy-web:latest
\`\`\`

## 🚀 Platform Deployment

### 1. Update Environment Variables
Update \`.env.azure\` with your actual Azure resource details:
- Database connection string
- Redis connection string
- Azure resource names

### 2. Deploy with Docker Compose
\`\`\`bash
docker-compose -f docker-compose.azure.yml up -d
\`\`\`

### 3. Import Database
\`\`\`bash
# Get database connection details
az postgres flexible-server show \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgres

# Import database
./scripts/import-database-azure.sh \
  database-exports/full_database_*.sql \
  your-server.postgres.database.azure.com \
  your_password
\`\`\`

## 🌐 Access URLs
- **Web Interface**: https://your-azure-domain.com
- **API**: https://your-azure-domain.com:8000
- **Grafana**: https://your-azure-domain.com:3001
- **Prometheus**: https://your-azure-domain.com:9090

## 🔍 Verification
\`\`\`bash
# Check service status
docker-compose -f docker-compose.azure.yml ps

# Check logs
docker-compose -f docker-compose.azure.yml logs -f

# Test database connection
az postgres flexible-server execute \
  --resource-group openpolicy-platform-rg \
  --name openpolicy-postgres \
  --database-name openpolicy \
  --querytext "SELECT version();"
\`\`\`

## 🆘 Troubleshooting
- Check Azure resource status in Azure Portal
- Verify firewall rules allow your IP
- Check ACR authentication
- Monitor resource usage and limits
- Review Azure Monitor logs

## 💰 Cost Optimization
- Use Basic SKUs for development
- Consider reserved instances for production
- Monitor and set up spending limits
- Use Azure Advisor for recommendations
EOF

    print_success "Azure deployment instructions created: AZURE_DEPLOYMENT_INSTRUCTIONS.md"
}

# Main execution
main() {
    echo ""
    print_status "Starting Azure deployment preparation..."
    
    check_azure_cli
    check_azure_login
    create_azure_env
    create_deployment_instructions
    
    echo ""
    print_success "Azure deployment preparation completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Login to Azure: az login"
    echo "2. Create Azure resources (see AZURE_DEPLOYMENT_INSTRUCTIONS.md)"
    echo "3. Update .env.azure with your resource details"
    echo "4. Build and push Docker images to ACR"
    echo "5. Deploy the platform"
    echo ""
    print_warning "IMPORTANT: Update .env.azure with your actual Azure resource details"
}

# Run main function
main "$@"
