#!/bin/bash

# Open Policy Platform V4 - Azure Setup Test Script
# This script tests your Azure setup before deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "🧪 Testing Azure Setup for Open Policy Platform V4"
echo "=================================================="
echo ""

# Test 1: Check Azure CLI
print_status "Test 1: Checking Azure CLI..."
if command -v az &> /dev/null; then
    AZURE_CLI_VERSION=$(az version --query '"azure-cli"' -o tsv)
    print_success "Azure CLI detected: version $AZURE_CLI_VERSION"
else
    print_error "Azure CLI not found. Please install Azure CLI first."
    exit 1
fi

# Test 2: Check Azure login
print_status "Test 2: Checking Azure authentication..."
if az account show &> /dev/null; then
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
    print_success "Authenticated to Azure: $SUBSCRIPTION_NAME ($SUBSCRIPTION_ID)"
else
    print_error "Not authenticated to Azure. Please run 'az login' first."
    exit 1
fi

# Test 3: Check configuration file
print_status "Test 3: Checking Azure configuration file..."
if [ -f "azure-config.json" ]; then
    print_success "Azure configuration file found"
    
    # Validate JSON
    if jq empty azure-config.json 2>/dev/null; then
        print_success "Azure configuration file is valid JSON"
        
        # Extract and display key information
        RESOURCE_GROUP=$(jq -r '.resource_group.name' azure-config.json)
        LOCATION=$(jq -r '.resource_group.location' azure-config.json)
        ACR_NAME=$(jq -r '.services.container_registry.name' azure-config.json)
        DB_NAME=$(jq -r '.services.database.name' azure-config.json)
        
        echo "  Resource Group: $RESOURCE_GROUP"
        echo "  Location: $LOCATION"
        echo "  ACR Name: $ACR_NAME"
        echo "  Database Name: $DB_NAME"
    else
        print_error "Azure configuration file contains invalid JSON"
        exit 1
    fi
else
    print_error "Azure configuration file not found: azure-config.json"
    exit 1
fi

# Test 4: Check Docker
print_status "Test 4: Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker detected: $DOCKER_VERSION"
else
    print_error "Docker not found. Please install Docker first."
    exit 1
fi

# Test 5: Check Docker Compose
print_status "Test 5: Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose detected: $COMPOSE_VERSION"
else
    print_error "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Test 6: Check if resources already exist
print_status "Test 6: Checking existing Azure resources..."
RESOURCE_GROUP=$(jq -r '.resource_group.name' azure-config.json)

if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Resource group '$RESOURCE_GROUP' already exists"
    
    # Check what resources exist
    echo "  Checking existing resources in resource group..."
    
    # Check PostgreSQL
    DB_NAME=$(jq -r '.services.database.name' azure-config.json)
    if az postgres flexible-server show --resource-group "$RESOURCE_GROUP" --name "$DB_NAME" &> /dev/null; then
        print_warning "PostgreSQL server '$DB_NAME' already exists"
    else
        print_success "PostgreSQL server '$DB_NAME' does not exist (will be created)"
    fi
    
    # Check ACR
    ACR_NAME=$(jq -r '.services.container_registry.name' azure-config.json)
    if az acr show --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" &> /dev/null; then
        print_warning "Container Registry '$ACR_NAME' already exists"
    else
        print_success "Container Registry '$ACR_NAME' does not exist (will be created)"
    fi
    
    # Check Redis
    REDIS_NAME=$(jq -r '.services.redis.name' azure-config.json)
    if az redis show --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" &> /dev/null; then
        print_warning "Redis Cache '$REDIS_NAME' already exists"
    else
        print_success "Redis Cache '$REDIS_NAME' does not exist (will be created)"
    fi
    
else
    print_success "Resource group '$RESOURCE_GROUP' does not exist (will be created)"
fi

# Test 7: Check Docker Compose file
print_status "Test 7: Checking Docker Compose file..."
if [ -f "docker-compose.azure.yml" ]; then
    print_success "Docker Compose file found: docker-compose.azure.yml"
else
    print_warning "Docker Compose file not found: docker-compose.azure.yml"
    print_status "You may need to create this file or use a different compose file"
fi

echo ""
echo "🎯 Test Summary:"
echo "================="

if [ $? -eq 0 ]; then
    print_success "All basic tests passed! Your Azure setup is ready for deployment."
    echo ""
    print_status "Next steps:"
    echo "  1. Run: ./deploy-azure-fixed.sh"
    echo "  2. Or follow the manual steps in: AZURE_DEPLOYMENT_STEP_BY_STEP.md"
    echo ""
    print_success "🚀 Ready to deploy to Azure!"
else
    print_error "Some tests failed. Please fix the issues before proceeding."
    exit 1
fi
