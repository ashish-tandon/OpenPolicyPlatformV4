#!/bin/bash

# Open Policy Platform V4 - Fixed Azure Deployment Script
# This script deploys the platform to Azure with corrected commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration files
COMPOSE_FILE="docker-compose.azure.yml"
ENV_FILE=".env.azure"
AZURE_CONFIG_FILE="azure-config.json"

# Print functions
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Check Azure CLI
check_azure_cli() {
    print_status "Checking Azure CLI..."
    
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install Azure CLI first."
        print_status "Installation guide: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    # Check Azure CLI version
    AZURE_CLI_VERSION=$(az version --query '"azure-cli"' -o tsv)
    print_status "Azure CLI version: $AZURE_CLI_VERSION"
    
    print_success "Azure CLI detected"
}

# Azure login
azure_login() {
    print_status "Logging into Azure..."
    
    if ! az account show &> /dev/null; then
        print_status "Please log in to Azure..."
        az login
    else
        print_success "Already logged into Azure"
    fi
    
    # Set subscription
    if [ -f "$AZURE_CONFIG_FILE" ]; then
        SUBSCRIPTION_ID=$(jq -r '.subscription.id' "$AZURE_CONFIG_FILE")
        print_status "Setting subscription: $SUBSCRIPTION_ID"
        az account set --subscription "$SUBSCRIPTION_ID"
    fi
}

# Create Azure resources
create_azure_resources() {
    print_status "Creating Azure resources..."
    
    if [ ! -f "$AZURE_CONFIG_FILE" ]; then
        print_error "Azure configuration file not found: $AZURE_CONFIG_FILE"
        print_status "Please create the configuration file with your Azure settings"
        exit 1
    fi
    
    # Extract values from JSON config
    AZURE_RESOURCE_GROUP=$(jq -r '.resource_group.name' "$AZURE_CONFIG_FILE")
    AZURE_LOCATION=$(jq -r '.resource_group.location' "$AZURE_CONFIG_FILE")
    AZURE_ACR_NAME=$(jq -r '.services.container_registry.name' "$AZURE_CONFIG_FILE")
    AZURE_POSTGRES_SERVER=$(jq -r '.services.database.name' "$AZURE_CONFIG_FILE")
    AZURE_POSTGRES_USER="openpolicy"
    AZURE_POSTGRES_PASSWORD=$(openssl rand -base64 32)
    AZURE_REDIS_NAME=$(jq -r '.services.redis.name' "$AZURE_CONFIG_FILE")
    AZURE_STORAGE_ACCOUNT=$(jq -r '.services.storage.name' "$AZURE_CONFIG_FILE")
    AZURE_APP_INSIGHTS_NAME=$(jq -r '.services.app_insights.name' "$AZURE_CONFIG_FILE")
    AZURE_KEY_VAULT_NAME=$(jq -r '.services.key_vault.name' "$AZURE_CONFIG_FILE")
    AZURE_JWT_SECRET=$(openssl rand -base64 64)
    
    print_status "Creating resource group: $AZURE_RESOURCE_GROUP"
    az group create --name "$AZURE_RESOURCE_GROUP" --location "$AZURE_LOCATION"
    
    # Create Azure Container Registry
    print_status "Creating Azure Container Registry: $AZURE_ACR_NAME"
    az acr create --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_ACR_NAME" \
        --sku Basic \
        --admin-enabled true
    
    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name "$AZURE_ACR_NAME" --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name "$AZURE_ACR_NAME" --query passwords[0].value -o tsv)
    
    # Create Azure Database for PostgreSQL - FIXED COMMAND
    print_status "Creating Azure Database for PostgreSQL: $AZURE_POSTGRES_SERVER"
    az postgres flexible-server create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_POSTGRES_SERVER" \
        --location "$AZURE_LOCATION" \
        --admin-user "$AZURE_POSTGRES_USER" \
        --admin-password "$AZURE_POSTGRES_PASSWORD" \
        --sku-name Standard_B1ms \
        --tier Burstable \
        --storage-size 32 \
        --version 15 \
        --yes
    
    # Create database
    print_status "Creating database: openpolicy"
    az postgres flexible-server db create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --server-name "$AZURE_POSTGRES_SERVER" \
        --database-name "openpolicy"
    
    # Create test database
    print_status "Creating test database: openpolicy_test"
    az postgres flexible-server db create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --server-name "$AZURE_POSTGRES_SERVER" \
        --database-name "openpolicy_test"
    
    # Configure firewall rules
    print_status "Configuring PostgreSQL firewall rules..."
    az postgres flexible-server firewall-rule create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_POSTGRES_SERVER" \
        --rule-name "AllowAllAzureServices" \
        --start-ip-address "0.0.0.0" \
        --end-ip-address "255.255.255.255"
    
    # Get PostgreSQL connection details
    POSTGRES_HOST=$(az postgres flexible-server show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_POSTGRES_SERVER" \
        --query fullyQualifiedDomainName -o tsv)
    
    # Create Azure Cache for Redis
    print_status "Creating Azure Cache for Redis: $AZURE_REDIS_NAME"
    az redis create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_REDIS_NAME" \
        --location "$AZURE_LOCATION" \
        --sku Basic \
        --vm-size C0 \
        --enable-non-ssl-port
    
    # Get Redis access key
    AZURE_REDIS_PASSWORD=$(az redis list-keys --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_REDIS_NAME" --query primaryKey -o tsv)
    
    # Create Azure Storage Account
    print_status "Creating Azure Storage Account: $AZURE_STORAGE_ACCOUNT"
    az storage account create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_STORAGE_ACCOUNT" \
        --location "$AZURE_LOCATION" \
        --sku Standard_LRS \
        --encryption-services blob
    
    # Get storage account key
    AZURE_STORAGE_KEY=$(az storage account keys list --resource-group "$AZURE_RESOURCE_GROUP" --account-name "$AZURE_STORAGE_ACCOUNT" --query '[0].value' -o tsv)
    
    # Create Application Insights
    print_status "Creating Application Insights: $AZURE_APP_INSIGHTS_NAME"
    az monitor app-insights component create \
        --app "$AZURE_APP_INSIGHTS_NAME" \
        --location "$AZURE_LOCATION" \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --kind web
    
    # Get Application Insights connection string
    AZURE_APP_INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show --app "$AZURE_APP_INSIGHTS_NAME" --resource-group "$AZURE_RESOURCE_GROUP" --query connectionString -o tsv)
    
    # Create Azure Key Vault
    print_status "Creating Azure Key Vault: $AZURE_KEY_VAULT_NAME"
    az keyvault create \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_KEY_VAULT_NAME" \
        --location "$AZURE_LOCATION" \
        --sku standard
    
    # Store secrets in Key Vault
    print_status "Storing secrets in Key Vault..."
    az keyvault secret set --vault-name "$AZURE_KEY_VAULT_NAME" --name "JWT-SECRET" --value "$AZURE_JWT_SECRET"
    az keyvault secret set --vault-name "$AZURE_KEY_VAULT_NAME" --name "POSTGRES-PASSWORD" --value "$AZURE_POSTGRES_PASSWORD"
    az keyvault secret set --vault-name "$AZURE_KEY_VAULT_NAME" --name "REDIS-PASSWORD" --value "$AZURE_REDIS_PASSWORD"
    
    print_success "Azure resources created successfully"
    
    # Display connection information
    print_status "PostgreSQL Connection Details:"
    echo "  Host: $POSTGRES_HOST"
    echo "  Username: $AZURE_POSTGRES_USER"
    echo "  Password: $AZURE_POSTGRES_PASSWORD"
    echo "  Database: openpolicy"
    echo "  Test Database: openpolicy_test"
    
    print_status "Redis Connection Details:"
    echo "  Host: $AZURE_REDIS_NAME.redis.cache.windows.net"
    echo "  Port: 6379"
    echo "  Password: $AZURE_REDIS_PASSWORD"
}

# Create environment file
create_env_file() {
    print_status "Creating Azure environment configuration file..."
    
    # Extract values from JSON config
    AZURE_RESOURCE_GROUP=$(jq -r '.resource_group.name' "$AZURE_CONFIG_FILE")
    AZURE_LOCATION=$(jq -r '.resource_group.location' "$AZURE_CONFIG_FILE")
    AZURE_ACR_NAME=$(jq -r '.services.container_registry.name' "$AZURE_CONFIG_FILE")
    AZURE_POSTGRES_SERVER=$(jq -r '.services.database.name' "$AZURE_CONFIG_FILE")
    AZURE_POSTGRES_USER="openpolicy"
    AZURE_POSTGRES_PASSWORD=$(openssl rand -base64 32)
    AZURE_REDIS_NAME=$(jq -r '.services.redis.name' "$AZURE_CONFIG_FILE")
    AZURE_STORAGE_ACCOUNT=$(jq -r '.services.storage.name' "$AZURE_CONFIG_FILE")
    
    # Get actual values from Azure
    POSTGRES_HOST=$(az postgres flexible-server show \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_POSTGRES_SERVER" \
        --query fullyQualifiedDomainName -o tsv)
    
    ACR_USERNAME=$(az acr credential show --name "$AZURE_ACR_NAME" --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name "$AZURE_ACR_NAME" --query passwords[0].value -o tsv)
    
    AZURE_REDIS_PASSWORD=$(az redis list-keys --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_REDIS_NAME" --query primaryKey -o tsv)
    AZURE_STORAGE_KEY=$(az storage account keys list --resource-group "$AZURE_RESOURCE_GROUP" --account-name "$AZURE_STORAGE_ACCOUNT" --query '[0].value' -o tsv)
    
    cat > "$ENV_FILE" << EOF
# Open Policy Platform V4 - Azure Environment Configuration

# Azure Configuration
AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP
AZURE_LOCATION=$AZURE_LOCATION

# Azure Container Registry
AZURE_ACR_NAME=$AZURE_ACR_NAME
AZURE_ACR_USERNAME=$ACR_USERNAME
AZURE_ACR_PASSWORD=$ACR_PASSWORD

# Database Configuration
AZURE_POSTGRES_USER=$AZURE_POSTGRES_USER
AZURE_POSTGRES_PASSWORD=$AZURE_POSTGRES_PASSWORD
AZURE_POSTGRES_SERVER=$POSTGRES_HOST
AZURE_POSTGRES_DATABASE=openpolicy
AZURE_POSTGRES_TEST_DATABASE=openpolicy_test

# Redis Configuration
AZURE_REDIS_PASSWORD=$AZURE_REDIS_PASSWORD
AZURE_REDIS_NAME=$AZURE_REDIS_NAME.redis.cache.windows.net
AZURE_REDIS_PORT=6379

# Storage Configuration
AZURE_STORAGE_ACCOUNT=$AZURE_STORAGE_ACCOUNT
AZURE_STORAGE_KEY=$AZURE_STORAGE_KEY

# Application Configuration
NODE_ENV=production
DATABASE_URL=postgresql://$AZURE_POSTGRES_USER:$AZURE_POSTGRES_PASSWORD@$POSTGRES_HOST:5432/openpolicy
REDIS_URL=redis://:$AZURE_REDIS_PASSWORD@$AZURE_REDIS_NAME.redis.cache.windows.net:6379
EOF
    
    print_success "Environment file created: $ENV_FILE"
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    AZURE_ACR_NAME=$(jq -r '.services.container_registry.name' "$AZURE_CONFIG_FILE")
    
    # Login to ACR
    print_status "Logging into Azure Container Registry..."
    az acr login --name "$AZURE_ACR_NAME"
    
    # Build images
    print_status "Building Docker images..."
    
    # Build backend image
    if [ -d "backend" ]; then
        print_status "Building backend image..."
        docker build -t "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:latest" ./backend
        docker push "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:latest"
    fi
    
    # Build web image
    if [ -d "web" ]; then
        print_status "Building web image..."
        docker build -t "$AZURE_ACR_NAME.azurecr.io/openpolicy-web:latest" ./web
        docker push "$AZURE_ACR_NAME.azurecr.io/openpolicy-web:latest"
    fi
    
    print_success "Docker images built and pushed successfully"
}

# Deploy platform
deploy_platform() {
    print_status "Deploying Open Policy Platform..."
    
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_status "Please run the resource creation first"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Load environment variables
    source "$ENV_FILE"
    
    # Deploy with Docker Compose
    print_status "Starting services with Docker Compose..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    print_success "Platform deployed successfully"
}

# Main deployment function
main() {
    echo "🚀 Starting Open Policy Platform V4 deployment to Azure..."
    echo ""
    
    check_prerequisites
    check_azure_cli
    azure_login
    create_azure_resources
    create_env_file
    build_and_push_images
    deploy_platform
    
    echo ""
    print_success "🎉 Open Policy Platform V4 has been successfully deployed to Azure!"
    echo ""
    print_status "Next steps:"
    echo "  1. Check service status: docker-compose -f $COMPOSE_FILE ps"
    echo "  2. View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  3. Access the platform at your configured domain"
    echo "  4. Import your database data if needed"
}

# Run main function
main "$@"
