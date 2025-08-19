#!/bin/bash

# Setup Azure resources for OpenPolicy Platform

RESOURCE_GROUP="openpolicy-platform-rg"
LOCATION="canadacentral"
ACR_NAME="openpolicyacr"

echo "Creating Azure resources..."

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name openpolicy-postgresql \
  --location $LOCATION \
  --admin-user openpolicy \
  --admin-password "SecurePassword123!" \
  --sku-name Standard_B2s \
  --storage-size 32 \
  --version 15

# Create Redis Cache
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

# Create Application Insights
az monitor app-insights component create \
  --app openpolicy-appinsights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web

# Create Container Apps Environment
az containerapp env create \
  --name openpolicy-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

echo "✅ Azure resources created successfully!"
echo ""
echo "Next steps:"
echo "1. Get ACR credentials: az acr credential show --name $ACR_NAME"
echo "2. Update GitHub secrets with the credentials"
echo "3. Deploy services using CI/CD pipelines"
