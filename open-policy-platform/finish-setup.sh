#!/bin/bash

# Open Policy Platform V4 - Finish Setup (Azure Environment)
# This script finishes the setup for Azure deployment with Key Vault

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

echo "🔧 Finishing Azure Setup for Open Policy Platform V4..."
echo ""

# Extract values from JSON config
AZURE_RESOURCE_GROUP=$(jq -r '.resource_group.name' "$AZURE_CONFIG_FILE")
AZURE_KEY_VAULT_NAME=$(jq -r '.services.key_vault.name' "$AZURE_CONFIG_FILE")
AZURE_POSTGRES_SERVER=$(jq -r '.services.database.name' "$AZURE_CONFIG_FILE")
AZURE_REDIS_NAME=$(jq -r '.services.redis.name' "$AZURE_CONFIG_FILE")

print_status "Resource Group: $AZURE_RESOURCE_GROUP"
print_status "Key Vault: $AZURE_KEY_VAULT_NAME"
print_status "PostgreSQL Server: $AZURE_POSTGRES_SERVER"
print_status "Redis Cache: $AZURE_REDIS_NAME"

# Get the passwords from existing resources
print_status "Retrieving existing resource passwords..."

# Get PostgreSQL password (we'll need to reset it since it was auto-generated)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
print_status "Setting new PostgreSQL password: $POSTGRES_PASSWORD"

# Update PostgreSQL password
az postgres flexible-server update \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$AZURE_POSTGRES_SERVER" \
    --admin-password "$POSTGRES_PASSWORD"

# Get Redis password
REDIS_PASSWORD=$(az redis list-keys --resource-group "$AZURE_RESOURCE_GROUP" --name "$AZURE_REDIS_NAME" --query primaryKey -o tsv)
print_status "Redis password retrieved: ${REDIS_PASSWORD:0:10}..."

# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 64)

# Store secrets in Azure Key Vault
print_status "Storing secrets in Azure Key Vault..."
az keyvault secret set --vault-name "$AZURE_KEY_VAULT_NAME" --name "JWT-SECRET" --value "$JWT_SECRET"
az keyvault secret set --vault-name "$AZURE_KEY_VAULT_NAME" --name "POSTGRES-PASSWORD" --value "$POSTGRES_PASSWORD"
az keyvault secret set --vault-name "$AZURE_KEY_VAULT_NAME" --name "REDIS-PASSWORD" --value "$REDIS_PASSWORD"

print_success "Secrets stored in Azure Key Vault successfully!"

# Get PostgreSQL connection details
POSTGRES_HOST=$(az postgres flexible-server show \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --name "$AZURE_POSTGRES_SERVER" \
    --query fullyQualifiedDomainName -o tsv)

# Get ACR credentials
AZURE_ACR_NAME=$(jq -r '.services.container_registry.name' "$AZURE_CONFIG_FILE")
ACR_USERNAME=$(az acr credential show --name "$AZURE_ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$AZURE_ACR_NAME" --query passwords[0].value -o tsv)

# Get storage account key
AZURE_STORAGE_ACCOUNT=$(jq -r '.services.storage.name' "$AZURE_CONFIG_FILE")
AZURE_STORAGE_KEY=$(az storage account keys list --resource-group "$AZURE_RESOURCE_GROUP" --account-name "$AZURE_STORAGE_ACCOUNT" --query '[0].value' -o tsv)

# Create environment file
print_status "Creating Azure environment configuration file..."

cat > "$ENV_FILE" << EOF
# Open Policy Platform V4 - Azure Environment Configuration

# Azure Configuration
AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP
AZURE_LOCATION=canadacentral

# Azure Container Registry
AZURE_ACR_NAME=$AZURE_ACR_NAME
AZURE_ACR_USERNAME=$ACR_USERNAME
AZURE_ACR_PASSWORD=$ACR_PASSWORD

# Database Configuration
AZURE_POSTGRES_USER=openpolicy
AZURE_POSTGRES_PASSWORD=$POSTGRES_PASSWORD
AZURE_POSTGRES_SERVER=$POSTGRES_HOST
AZURE_POSTGRES_DATABASE=openpolicy
AZURE_POSTGRES_TEST_DATABASE=openpolicy_test

# Redis Configuration
AZURE_REDIS_PASSWORD=$REDIS_PASSWORD
AZURE_REDIS_NAME=$AZURE_REDIS_NAME.redis.cache.windows.net
AZURE_REDIS_PORT=6379

# Storage Configuration
AZURE_STORAGE_ACCOUNT=$AZURE_STORAGE_ACCOUNT
AZURE_STORAGE_KEY=$AZURE_STORAGE_KEY

# Application Configuration
NODE_ENV=production
DATABASE_URL=postgresql://openpolicy:$POSTGRES_PASSWORD@$POSTGRES_HOST:5432/openpolicy
REDIS_URL=redis://:$REDIS_PASSWORD@$AZURE_REDIS_NAME.redis.cache.windows.net:6379

# Security Configuration
AZURE_JWT_SECRET=$JWT_SECRET
EOF

print_success "Environment file created: $ENV_FILE"

# Build and push Docker images
print_status "Building and pushing Docker images..."

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

# Deploy platform
print_status "Deploying Open Policy Platform..."

if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Docker Compose file not found: $COMPOSE_FILE"
    print_status "Available compose files:"
    ls -la docker-compose*.yml
    exit 1
fi

# Deploy with Docker Compose
print_status "Starting services with Docker Compose..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

print_success "Platform deployed successfully"

echo ""
print_success "🎉 Open Policy Platform V4 has been successfully deployed to Azure!"
echo ""
print_status "Connection Details:"
echo "  PostgreSQL: $POSTGRES_HOST"
echo "  Redis: $AZURE_REDIS_NAME.redis.cache.windows.net:6379"
echo "  Storage: $AZURE_STORAGE_ACCOUNT"
echo "  Key Vault: $AZURE_KEY_VAULT_NAME"
echo "  Container Registry: $AZURE_ACR_NAME.azurecr.io"
echo ""
print_status "Next steps:"
echo "  1. Check service status: docker-compose -f $COMPOSE_FILE ps"
echo "  2. View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  3. Test database connection"
echo "  4. Import your database data if needed"
echo ""
print_status "Database credentials:"
echo "  Username: openpolicy"
echo "  Password: $POSTGRES_PASSWORD"
echo "  Database: openpolicy"
echo "  Test Database: openpolicy_test"
echo ""
print_status "Test database connection:"
echo "  az postgres flexible-server execute --resource-group $AZURE_RESOURCE_GROUP --name $AZURE_POSTGRES_SERVER --database-name openpolicy --querytext \"SELECT version();\""
