#!/bin/bash

# Open Policy Platform V4 - Azure Deployment Script
# This script deploys the platform to Azure

set -e

echo "🚀 Starting Open Policy Platform V4 deployment to Azure..."

# Configuration
COMPOSE_FILE="docker-compose.azure.yml"
ENV_FILE=".env.azure"
AZURE_CONFIG_FILE="azure-config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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
    print_status "Checking Azure CLI..."
    
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install Azure CLI first."
        print_status "Installation guide: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    print_success "Azure CLI detected"
}

# Check Docker and Docker Compose
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Dependencies check passed"
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
    
    # Get current subscription
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    print_success "Using subscription: $SUBSCRIPTION_ID"
}

# Create Azure resources
create_azure_resources() {
    print_status "Creating Azure resources..."
    
    # Read configuration
    if [ ! -f "$AZURE_CONFIG_FILE" ]; then
        print_error "Azure configuration file not found: $AZURE_CONFIG_FILE"
        print_status "Please create the configuration file with your Azure settings"
        exit 1
    fi
    
    # Load configuration
    source "$AZURE_CONFIG_FILE"
    
    # Create resource group
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
    
    # Create Azure Database for PostgreSQL
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
        --version 15
    
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
}

# Create environment file
create_env_file() {
    print_status "Creating Azure environment configuration file..."
    
    # Load configuration
    source "$AZURE_CONFIG_FILE"
    
    cat > "$ENV_FILE" << EOF
# Open Policy Platform V4 - Azure Environment Configuration

# Azure Configuration
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP=$AZURE_RESOURCE_GROUP
AZURE_LOCATION=$AZURE_LOCATION
AZURE_DOMAIN=$AZURE_DOMAIN

# Azure Container Registry
AZURE_ACR_NAME=$AZURE_ACR_NAME
AZURE_ACR_USERNAME=$ACR_USERNAME
AZURE_ACR_PASSWORD=$ACR_PASSWORD

# Database Configuration
AZURE_POSTGRES_USER=$AZURE_POSTGRES_USER
AZURE_POSTGRES_PASSWORD=$AZURE_POSTGRES_PASSWORD
AZURE_POSTGRES_SERVER=$AZURE_POSTGRES_SERVER

# Redis Configuration
AZURE_REDIS_PASSWORD=$AZURE_REDIS_PASSWORD
AZURE_REDIS_NAME=$AZURE_REDIS_NAME

# Storage Configuration
AZURE_STORAGE_ACCOUNT=$AZURE_STORAGE_ACCOUNT
AZURE_STORAGE_KEY=$AZURE_STORAGE_KEY
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=$AZURE_STORAGE_ACCOUNT;AccountKey=$AZURE_STORAGE_KEY;EndpointSuffix=core.windows.net

# Application Insights
AZURE_APP_INSIGHTS_NAME=$AZURE_APP_INSIGHTS_NAME
AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING=$AZURE_APP_INSIGHTS_CONNECTION_STRING
AZURE_APPLICATION_INSIGHTS_KEY=$AZURE_APP_INSIGHTS_NAME

# Key Vault
AZURE_KEY_VAULT_NAME=$AZURE_KEY_VAULT_NAME

# JWT Configuration
AZURE_JWT_SECRET=$AZURE_JWT_SECRET

# Grafana Configuration
AZURE_GRAFANA_PASSWORD=$AZURE_GRAFANA_PASSWORD

# Platform Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO

# Network Configuration
PLATFORM_DOMAIN=$AZURE_DOMAIN
PLATFORM_PORT=8000
WEB_PORT=3000
GATEWAY_PORT=80
GATEWAY_SSL_PORT=443

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
ALERTMANAGER_PORT=9093

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *
EOF
    
    print_success "Azure environment file created: $ENV_FILE"
}

# Build and push Docker images to Azure Container Registry
build_and_push_images() {
    print_status "Building and pushing Docker images to Azure Container Registry..."
    
    # Load configuration
    source "$AZURE_CONFIG_FILE"
    
    # Login to ACR
    az acr login --name "$AZURE_ACR_NAME"
    
    # Build and push API image
    print_status "Building and pushing API image..."
    docker build -t "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:latest" ./backend
    docker push "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:latest"
    
    # Build and push Web image
    print_status "Building and pushing Web image..."
    docker build -t "$AZURE_ACR_NAME.azurecr.io/openpolicy-web:latest" ./frontend
    docker push "$AZURE_ACR_NAME.azurecr.io/openpolicy-web:latest"
    
    print_success "Docker images built and pushed successfully"
}

# Deploy the platform
deploy_platform() {
    print_status "Deploying Open Policy Platform V4 to Azure..."
    
    # Stop existing containers
    if docker-compose -f "$COMPOSE_FILE" down 2>/dev/null; then
        print_success "Existing containers stopped"
    fi
    
    # Build and start services
    docker-compose -f "$COMPOSE_FILE" up -d --build
    
    print_success "Platform deployment initiated"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        print_status "Checking service health (attempt $attempt/$max_attempts)..."
        
        if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            print_success "API service is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            print_error "Services failed to become ready after $max_attempts attempts"
            exit 1
        fi
        
        attempt=$((attempt + 1))
        sleep 10
    done
    
    print_success "All services are ready"
}

# Display deployment information
show_deployment_info() {
    print_success "Open Policy Platform V4 deployed successfully to Azure!"
    
    # Load configuration
    source "$AZURE_CONFIG_FILE"
    
    echo ""
    echo "🌐 Platform Access Information:"
    echo "   API: https://$AZURE_DOMAIN:8000"
    echo "   Web: https://$AZURE_DOMAIN:3000"
    echo "   Gateway: https://$AZURE_DOMAIN"
    echo ""
    echo "📊 Monitoring:"
    echo "   Prometheus: https://$AZURE_DOMAIN:9090"
    echo "   Grafana: https://$AZURE_DOMAIN:3001 (admin/$AZURE_GRAFANA_PASSWORD)"
    echo "   AlertManager: https://$AZURE_DOMAIN:9093"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   Admin: admin@openpolicy.com / admin123"
    echo "   Moderator: moderator@openpolicy.com / mod123"
    echo "   MP Office: mp_office@openpolicy.com / mp123"
    echo ""
    echo "☁️  Azure Resources:"
    echo "   Resource Group: $AZURE_RESOURCE_GROUP"
    echo "   Container Registry: $AZURE_ACR_NAME.azurecr.io"
    echo "   PostgreSQL Server: $AZURE_POSTGRES_SERVER"
    echo "   Redis Cache: $AZURE_REDIS_NAME"
    echo "   Storage Account: $AZURE_STORAGE_ACCOUNT"
    echo "   Application Insights: $AZURE_APP_INSIGHTS_NAME"
    echo "   Key Vault: $AZURE_KEY_VAULT_NAME"
    echo ""
    echo "🛠️  Management Commands:"
    echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "   Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "   Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "   Update platform: docker-compose -f $COMPOSE_FILE up -d --build"
    echo ""
    echo "📋 Azure CLI Commands:"
    echo "   View resources: az resource list --resource-group $AZURE_RESOURCE_GROUP"
    echo "   View logs: az monitor activity-log list --resource-group $AZURE_RESOURCE_GROUP"
    echo "   Scale database: az postgres flexible-server update --name $AZURE_POSTGRES_SERVER --resource-group $AZURE_RESOURCE_GROUP --sku-name Standard_B2ms"
}

# Create Azure configuration template
create_azure_config_template() {
    if [ ! -f "$AZURE_CONFIG_FILE" ]; then
        print_status "Creating Azure configuration template..."
        
        cat > "$AZURE_CONFIG_FILE" << 'EOF'
# Azure Configuration Template
# Please update these values with your Azure settings

# Azure Subscription and Resource Group
AZURE_SUBSCRIPTION_ID="your_subscription_id"
AZURE_RESOURCE_GROUP="openpolicy-platform-rg"
AZURE_LOCATION="eastus"

# Domain Configuration
AZURE_DOMAIN="your-domain.com"

# Azure Container Registry
AZURE_ACR_NAME="openpolicyacr"

# Database Configuration
AZURE_POSTGRES_USER="openpolicy"
AZURE_POSTGRES_PASSWORD="your_secure_password_here"
AZURE_POSTGRES_SERVER="openpolicy-postgres"

# Redis Configuration
AZURE_REDIS_NAME="openpolicy-redis"

# Storage Configuration
AZURE_STORAGE_ACCOUNT="openpolicystorage"

# Application Insights
AZURE_APP_INSIGHTS_NAME="openpolicy-insights"

# Key Vault
AZURE_KEY_VAULT_NAME="openpolicy-keyvault"

# JWT Configuration
AZURE_JWT_SECRET="your_jwt_secret_key_here_change_in_production"

# Grafana Configuration
AZURE_GRAFANA_PASSWORD="admin123"
EOF
        
        print_success "Azure configuration template created: $AZURE_CONFIG_FILE"
        print_warning "Please update the configuration file with your Azure settings before running the deployment"
        exit 0
    fi
}

# Main deployment process
main() {
    echo "=========================================="
    echo "Open Policy Platform V4 - Azure Deployment"
    echo "=========================================="
    echo ""
    
    # Check if configuration exists
    if [ ! -f "$AZURE_CONFIG_FILE" ]; then
        create_azure_config_template
    fi
    
    check_azure_cli
    check_dependencies
    azure_login
    create_azure_resources
    create_env_file
    build_and_push_images
    deploy_platform
    wait_for_services
    show_deployment_info
    
    echo ""
    print_success "Azure deployment completed successfully! 🎉"
}

# Run main function
main "$@"
