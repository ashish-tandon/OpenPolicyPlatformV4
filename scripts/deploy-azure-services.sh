#!/bin/bash

# ========================================
# Azure Service Deployment Script
# OpenPolicyPlatform V4 - Deploy all services to Azure
# ========================================

set -e  # Exit on any error

# ========================================
# CONFIGURATION
# ========================================
RESOURCE_GROUP="openpolicy-platform-rg"
LOCATION="canadacentral"
ENVIRONMENT_NAME="openpolicy-env"
ACR_NAME="openpolicyacr"

# Service configurations
SERVICES=(
    "api-gateway:80:external:1:3"
    "api:8000:internal:2:5"
    "web:3000:internal:2:3"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ========================================
# FUNCTIONS
# ========================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged into Azure
    if ! az account show &> /dev/null; then
        error "Not logged into Azure. Please run 'az login' first."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

check_resource_group() {
    log "Checking resource group..."
    
    if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        error "Resource group '$RESOURCE_GROUP' does not exist."
        exit 1
    fi
    
    success "Resource group '$RESOURCE_GROUP' exists"
}

check_acr() {
    log "Checking Azure Container Registry..."
    
    if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        error "Container Registry '$ACR_NAME' does not exist."
        exit 1
    fi
    
    success "Container Registry '$ACR_NAME' exists"
}

login_to_acr() {
    log "Logging into Azure Container Registry..."
    
    if az acr login --name "$ACR_NAME"; then
        success "Successfully logged into ACR"
    else
        error "Failed to log into ACR"
        exit 1
    fi
}

build_and_push_images() {
    log "Building and pushing container images..."
    
    # Build API Gateway image
    log "Building API Gateway image..."
    docker build -t "${ACR_NAME}.azurecr.io/openpolicy-gateway:latest" ./infrastructure/gateway
    docker push "${ACR_NAME}.azurecr.io/openpolicy-gateway:latest"
    success "API Gateway image built and pushed"
    
    # Build Backend API image
    log "Building Backend API image..."
    docker build -t "${ACR_NAME}.azurecr.io/openpolicy-api:latest" ./backend
    docker push "${ACR_NAME}.azurecr.io/openpolicy-api:latest"
    success "Backend API image built and pushed"
    
    # Build Web Frontend image
    log "Building Web Frontend image..."
    docker build -t "${ACR_NAME}.azurecr.io/openpolicy-web:latest" ./web
    docker push "${ACR_NAME}.azurecr.io/openpolicy-web:latest"
    success "Web Frontend image built and pushed"
}

create_container_apps_environment() {
    log "Creating Container Apps Environment..."
    
    # Check if environment already exists
    if az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Container Apps Environment '$ENVIRONMENT_NAME' already exists"
        return 0
    fi
    
    # Get Log Analytics workspace ID
    WORKSPACE_ID=$(az monitor log-analytics workspace list --resource-group "$RESOURCE_GROUP" --query "[0].id" -o tsv)
    
    if [ -z "$WORKSPACE_ID" ]; then
        error "No Log Analytics workspace found. Creating one..."
        WORKSPACE_NAME="openpolicy-logs-$(date +%s)"
        az monitor log-analytics workspace create \
            --resource-group "$RESOURCE_GROUP" \
            --workspace-name "$WORKSPACE_NAME" \
            --location "$LOCATION"
        WORKSPACE_ID=$(az monitor log-analytics workspace show --resource-group "$RESOURCE_GROUP" --workspace-name "$WORKSPACE_NAME" --query "id" -o tsv)
    fi
    
    # Create Container Apps Environment
    if az containerapp env create \
        --name "$ENVIRONMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --logs-workspace-id "$WORKSPACE_ID"; then
        success "Container Apps Environment created"
    else
        error "Failed to create Container Apps Environment"
        exit 1
    fi
}

deploy_service() {
    local service_name=$1
    local target_port=$2
    local ingress_type=$3
    local min_replicas=$4
    local max_replicas=$5
    
    log "Deploying $service_name service..."
    
    # Check if service already exists
    if az containerapp show --name "$service_name" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Service '$service_name' already exists, updating..."
        
        # Update existing service
        if az containerapp update \
            --name "$service_name" \
            --resource-group "$RESOURCE_GROUP" \
            --image "${ACR_NAME}.azurecr.io/openpolicy-${service_name#openpolicy-}:latest" \
            --min-replicas "$min_replicas" \
            --max-replicas "$max_replicas"; then
            success "Service '$service_name' updated"
        else
            error "Failed to update service '$service_name'"
            return 1
        fi
    else
        # Create new service
        if az containerapp create \
            --name "$service_name" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "$ENVIRONMENT_NAME" \
            --image "${ACR_NAME}.azurecr.io/openpolicy-${service_name#openpolicy-}:latest" \
            --target-port "$target_port" \
            --ingress "$ingress_type" \
            --min-replicas "$min_replicas" \
            --max-replicas "$max_replicas"; then
            success "Service '$service_name' created"
        else
            error "Failed to create service '$service_name'"
            return 1
        fi
    fi
}

deploy_all_services() {
    log "Deploying all services..."
    
    for service_config in "${SERVICES[@]}"; do
        IFS=':' read -r service_name target_port ingress_type min_replicas max_replicas <<< "$service_config"
        full_service_name="openpolicy-${service_name}"
        
        if deploy_service "$full_service_name" "$target_port" "$ingress_type" "$min_replicas" "$max_replicas"; then
            success "Service '$full_service_name' deployed successfully"
        else
            error "Failed to deploy service '$full_service_name'"
            return 1
        fi
    done
    
    success "All services deployed successfully"
}

configure_environment_variables() {
    log "Configuring environment variables..."
    
    # Get Redis password
    REDIS_PASSWORD=$(az redis list-keys --name openpolicy-redis --resource-group "$RESOURCE_GROUP" --query "primaryKey" -o tsv)
    
    # Get PostgreSQL password (you'll need to set this manually)
    warning "Please set the PostgreSQL password manually in the Azure portal or use Key Vault"
    
    # Configure API service environment variables
    log "Configuring API service environment variables..."
    
    if az containerapp update \
        --name "openpolicy-api" \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "REDIS_MIGRATION_MODE=dual" \
            "AZURE_REDIS_URL=rediss://:${REDIS_PASSWORD}@openpolicy-redis.redis.cache.windows.net:6380" \
            "AZURE_POSTGRES_URL=postgresql://openpolicy:<POSTGRES_PASSWORD>@openpolicy-postgresql.postgres.database.azure.com:5432/openpolicy" \
            "ENVIRONMENT=production" \
            "LOG_LEVEL=info"; then
        success "API service environment variables configured"
    else
        warning "Failed to configure API service environment variables"
    fi
    
    # Configure Web service environment variables
    log "Configuring Web service environment variables..."
    
    if az containerapp update \
        --name "openpolicy-web" \
        --resource-group "$RESOURCE_GROUP" \
        --set-env-vars \
            "VITE_API_URL=https://openpolicy-api.${ENVIRONMENT_NAME}.canadacentral.azurecontainerapps.io" \
            "NODE_ENV=production"; then
        success "Web service environment variables configured"
    else
        warning "Failed to configure Web service environment variables"
    fi
}

check_service_health() {
    log "Checking service health..."
    
    local healthy_services=0
    local total_services=${#SERVICES[@]}
    
    for service_config in "${SERVICES[@]}"; do
        IFS=':' read -r service_name target_port ingress_type min_replicas max_replicas <<< "$service_config"
        full_service_name="openpolicy-${service_name}"
        
        if az containerapp show --name "$full_service_name" --resource-group "$RESOURCE_GROUP" --query "properties.runningStatus" -o tsv | grep -q "Running"; then
            success "Service '$full_service_name' is running"
            ((healthy_services++))
        else
            error "Service '$full_service_name' is not running"
        fi
    done
    
    if [ $healthy_services -eq $total_services ]; then
        success "All services are healthy and running"
        return 0
    else
        warning "$healthy_services out of $total_services services are running"
        return 1
    fi
}

get_service_urls() {
    log "Getting service URLs..."
    
    echo -e "\n${BLUE}Service URLs:${NC}"
    echo "========================================"
    
    for service_config in "${SERVICES[@]}"; do
        IFS=':' read -r service_name target_port ingress_type min_replicas max_replicas <<< "$service_config"
        full_service_name="openpolicy-${service_name}"
        
        if [ "$ingress_type" = "external" ]; then
            url=$(az containerapp show --name "$full_service_name" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv)
            echo -e "${GREEN}${service_name}:${NC} https://${url}"
        else
            echo -e "${YELLOW}${service_name}:${NC} Internal service (no external URL)"
        fi
    done
    
    echo "========================================"
}

# ========================================
# MAIN EXECUTION
# ========================================

main() {
    log "Starting Azure service deployment for OpenPolicyPlatform V4..."
    
    # Check prerequisites
    check_prerequisites
    
    # Check resource group
    check_resource_group
    
    # Check ACR
    check_acr
    
    # Login to ACR
    login_to_acr
    
    # Build and push images
    build_and_push_images
    
    # Create Container Apps Environment
    create_container_apps_environment
    
    # Deploy all services
    deploy_all_services
    
    # Configure environment variables
    configure_environment_variables
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if check_service_health; then
        success "All services deployed and running successfully!"
        
        # Get service URLs
        get_service_urls
        
        log "Deployment completed successfully!"
        log "Next steps:"
        log "1. Set PostgreSQL password in Azure portal"
        log "2. Test Redis connectivity"
        log "3. Validate all service endpoints"
        log "4. Monitor application performance"
        
    else
        error "Some services failed to deploy or are not running"
        log "Please check the Azure portal for more details"
        exit 1
    fi
}

# ========================================
# SCRIPT EXECUTION
# ========================================

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed
    main "$@"
else
    # Script is being sourced
    log "Script sourced. Use main() function to execute deployment."
fi
