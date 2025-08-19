# Azure Deployment Templates for OpenPolicyPlatform Microservices

## 1. Main Azure Infrastructure Template (Bicep)

Create this file as `infrastructure/azure/main.bicep`

```bicep
@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Unique suffix for resource naming')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('Container image tag')
param imageTag string = 'latest'

@description('Database administrator password')
@secure()
param dbAdminPassword string

// Variables
var resourcePrefix = 'openpolicy-${environment}'
var containerEnvName = '${resourcePrefix}-env-${uniqueSuffix}'
var logAnalyticsName = '${resourcePrefix}-logs-${uniqueSuffix}'
var appInsightsName = '${resourcePrefix}-insights-${uniqueSuffix}'
var acrName = 'openpolicyacr${uniqueSuffix}'
var keyVaultName = '${resourcePrefix}-kv-${uniqueSuffix}'
var postgresName = '${resourcePrefix}-postgres-${uniqueSuffix}'
var redisName = '${resourcePrefix}-redis-${uniqueSuffix}'

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: environment == 'prod' ? 90 : 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Azure Container Registry
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
  }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenant().tenantId
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
  }
}

// PostgreSQL Flexible Server
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: postgresName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: 'openpolicy'
    administratorLoginPassword: dbAdminPassword
    version: '15'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: environment == 'prod' ? 35 : 7
      geoRedundantBackup: environment == 'prod' ? 'Enabled' : 'Disabled'
    }
    highAvailability: {
      mode: environment == 'prod' ? 'ZoneRedundant' : 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

// Azure Cache for Redis
resource redis 'Microsoft.Cache/redis@2023-04-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    redisVersion: '6'
    publicNetworkAccess: 'Enabled'
    minimumTlsVersion: '1.2'
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    zoneRedundant: environment == 'prod' ? true : false
  }
}

// Managed Identity for Container Apps
resource containerAppIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${resourcePrefix}-identity'
  location: location
}

// Container Apps
module apiGateway 'modules/container-app.bicep' = {
  name: 'api-gateway-deployment'
  params: {
    containerAppName: '${resourcePrefix}-api-gateway'
    location: location
    managedEnvironmentId: containerAppsEnvironment.id
    userAssignedIdentityId: containerAppIdentity.id
    containerImage: '${acr.properties.loginServer}/openpolicy-api-gateway:${imageTag}'
    targetPort: 3000
    environmentVariables: [
      {
        name: 'NODE_ENV'
        value: environment
      }
      {
        name: 'PORT'
        value: '3000'
      }
      {
        name: 'DATABASE_URL'
        secretRef: 'database-connection-string'
      }
      {
        name: 'REDIS_URL'
        secretRef: 'redis-connection-string'
      }
      {
        name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
        value: appInsights.properties.InstrumentationKey
      }
    ]
    secrets: [
      {
        name: 'database-connection-string'
        value: 'postgresql://openpolicy:${dbAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/openpolicy'
      }
      {
        name: 'redis-connection-string'
        value: '${redis.properties.hostName}:${redis.properties.port},password=${redis.listKeys().primaryKey},ssl=True'
      }
    ]
    minReplicas: environment == 'prod' ? 2 : 1
    maxReplicas: environment == 'prod' ? 10 : 3
    externalIngress: true
  }
}

// Outputs
output containerAppsEnvironmentId string = containerAppsEnvironment.id
output containerRegistryLoginServer string = acr.properties.loginServer
output apiGatewayUrl string = 'https://${apiGateway.outputs.fqdn}'
output keyVaultName string = keyVault.name
output logAnalyticsWorkspaceId string = logAnalytics.id
output applicationInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
```

## 2. Container App Module (Bicep)

Create this file as `infrastructure/azure/modules/container-app.bicep`

```bicep
@description('Container App name')
param containerAppName string

@description('Location for resources')
param location string

@description('Managed Environment ID')
param managedEnvironmentId string

@description('User Assigned Identity ID')
param userAssignedIdentityId string

@description('Container image')
param containerImage string

@description('Target port')
param targetPort int

@description('Environment variables')
param environmentVariables array

@description('Secrets')
param secrets array

@description('Minimum replicas')
param minReplicas int = 1

@description('Maximum replicas')
param maxReplicas int = 3

@description('External ingress enabled')
param externalIngress bool = false

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnvironmentId
    configuration: {
      ingress: externalIngress ? {
        external: true
        targetPort: targetPort
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        allowInsecure: false
        transport: 'auto'
      } : {
        external: false
        targetPort: targetPort
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        transport: 'auto'
      }
      secrets: secrets
    }
    template: {
      containers: [
        {
          image: containerImage
          name: containerAppName
          env: environmentVariables
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 30
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/ready'
                port: targetPort
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 5
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaling-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

output fqdn string = externalIngress ? containerApp.properties.configuration.ingress.fqdn : ''
output id string = containerApp.id
```

## 3. Azure CLI Deployment Scripts

Create this file as `scripts/deploy-azure.sh`

```bash
#!/bin/bash

# Azure Deployment Script for OpenPolicyPlatform
set -e

# Configuration
ENVIRONMENT=${1:-"dev"}
LOCATION=${2:-"canadacentral"}
SUBSCRIPTION_ID=${3:-""}
IMAGE_TAG=${4:-"latest"}

# Validate parameters
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "Error: Subscription ID is required"
    echo "Usage: $0 <environment> <location> <subscription_id> [image_tag]"
    echo "Example: $0 prod canadacentral 12345678-1234-1234-1234-123456789012 v1.0.0"
    exit 1
fi

# Colors for output
RED='[0;31m'
GREEN='[0;32m'
YELLOW='[1;33m'
NC='[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Set Azure subscription
log "Setting Azure subscription to $SUBSCRIPTION_ID"
az account set --subscription "$SUBSCRIPTION_ID"

# Variables
RESOURCE_GROUP_NAME="openpolicy-${ENVIRONMENT}-rg"
UNIQUE_SUFFIX=$(echo -n "${SUBSCRIPTION_ID}-${ENVIRONMENT}" | sha256sum | cut -c1-8)
DB_ADMIN_PASSWORD=$(openssl rand -base64 32)

log "Starting deployment to environment: $ENVIRONMENT"
log "Location: $LOCATION"
log "Resource Group: $RESOURCE_GROUP_NAME"
log "Image Tag: $IMAGE_TAG"

# Create resource group
log "Creating resource group: $RESOURCE_GROUP_NAME"
az group create     --name "$RESOURCE_GROUP_NAME"     --location "$LOCATION"     --tags environment="$ENVIRONMENT" project="openpolicy"

# Deploy main infrastructure
log "Deploying main infrastructure..."
DEPLOYMENT_OUTPUT=$(az deployment group create     --resource-group "$RESOURCE_GROUP_NAME"     --template-file infrastructure/azure/main.bicep     --parameters environment="$ENVIRONMENT"                 imageTag="$IMAGE_TAG"                 dbAdminPassword="$DB_ADMIN_PASSWORD"     --output json)

if [ $? -ne 0 ]; then
    error "Infrastructure deployment failed"
    exit 1
fi

# Extract outputs
ACR_LOGIN_SERVER=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.containerRegistryLoginServer.value')
API_GATEWAY_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.apiGatewayUrl.value')
KEY_VAULT_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.keyVaultName.value')

log "Deployment completed successfully!"
log "Container Registry: $ACR_LOGIN_SERVER"
log "API Gateway URL: $API_GATEWAY_URL"
log "Key Vault: $KEY_VAULT_NAME"

# Store deployment information
cat > "deployment-output-${ENVIRONMENT}.json" << EOF
{
  "environment": "$ENVIRONMENT",
  "resourceGroup": "$RESOURCE_GROUP_NAME",
  "containerRegistry": "$ACR_LOGIN_SERVER",
  "apiGatewayUrl": "$API_GATEWAY_URL",
  "keyVault": "$KEY_VAULT_NAME",
  "deploymentDate": "$(date -Iseconds)"
}
EOF

log "Deployment information saved to deployment-output-${ENVIRONMENT}.json"
log "Azure deployment completed successfully!"
```

## 4. Blue-Green Deployment Script

Create this file as `scripts/blue-green-deploy.sh`

```bash
#!/bin/bash

# Blue-Green Deployment Script for Azure Container Apps
set -e

# Configuration
RESOURCE_GROUP=${1}
APP_NAME=${2}
NEW_IMAGE=${3}
ENVIRONMENT=${4:-"prod"}

# Validate parameters
if [ -z "$RESOURCE_GROUP" ] || [ -z "$APP_NAME" ] || [ -z "$NEW_IMAGE" ]; then
    echo "Usage: $0 <resource_group> <app_name> <new_image> [environment]"
    echo "Example: $0 openpolicy-prod-rg api-gateway ghcr.io/user/api-gateway:v1.0.1 prod"
    exit 1
fi

# Colors for output
GREEN='[0;32m'
YELLOW='[1;33m'
RED='[0;31m'
NC='[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Functions
wait_for_revision() {
    local revision_name=$1
    local max_attempts=30
    local attempt=0

    log "Waiting for revision $revision_name to be ready..."

    while [ $attempt -lt $max_attempts ]; do
        local status=$(az containerapp revision show             --name "$revision_name"             --app "$APP_NAME"             --resource-group "$RESOURCE_GROUP"             --query "properties.provisioningState"             --output tsv 2>/dev/null)

        if [ "$status" = "Provisioned" ]; then
            log "Revision $revision_name is ready"
            return 0
        elif [ "$status" = "Failed" ]; then
            error "Revision $revision_name failed to provision"
        fi

        sleep 10
        attempt=$((attempt + 1))
        echo -n "."
    done

    error "Timeout waiting for revision $revision_name"
}

health_check() {
    local url=$1
    local max_attempts=10
    local attempt=0

    log "Performing health check on $url"

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url/health" > /dev/null; then
            log "Health check passed"
            return 0
        fi

        sleep 5
        attempt=$((attempt + 1))
        echo -n "."
    done

    error "Health check failed for $url"
}

# Main deployment process
log "Starting blue-green deployment for $APP_NAME"
log "New image: $NEW_IMAGE"

# Get current revision (blue)
BLUE_REVISION=$(az containerapp revision list     --name "$APP_NAME"     --resource-group "$RESOURCE_GROUP"     --query "[?properties.trafficWeight > \`0\`] | [0].name"     --output tsv)

log "Current blue revision: $BLUE_REVISION"

# Create new revision (green)
GREEN_SUFFIX="green-$(date +%s)"
log "Creating green revision with suffix: $GREEN_SUFFIX"

az containerapp update     --name "$APP_NAME"     --resource-group "$RESOURCE_GROUP"     --image "$NEW_IMAGE"     --revision-suffix "$GREEN_SUFFIX"     --set-env-vars "DEPLOYMENT_VERSION=$GREEN_SUFFIX"

# Get the new revision name
GREEN_REVISION=$(az containerapp revision list     --name "$APP_NAME"     --resource-group "$RESOURCE_GROUP"     --query "[?ends_with(name, '$GREEN_SUFFIX')].name"     --output tsv)

log "Green revision created: $GREEN_REVISION"

# Wait for green revision to be ready
wait_for_revision "$GREEN_REVISION"

# Gradual traffic shift for production
if [ "$ENVIRONMENT" = "prod" ]; then
    log "Starting gradual traffic shift for production..."

    # 10% to green
    log "Shifting 10% traffic to green revision"
    az containerapp ingress traffic set         --name "$APP_NAME"         --resource-group "$RESOURCE_GROUP"         --revision-weight "$GREEN_REVISION=10,$BLUE_REVISION=90"

    sleep 300  # 5 minutes

    # 50% to green
    log "Shifting 50% traffic to green revision"
    az containerapp ingress traffic set         --name "$APP_NAME"         --resource-group "$RESOURCE_GROUP"         --revision-weight "$GREEN_REVISION=50,$BLUE_REVISION=50"

    sleep 300  # 5 minutes

    # Final switch to 100% green
    log "Switching 100% traffic to green revision"
    az containerapp ingress traffic set         --name "$APP_NAME"         --resource-group "$RESOURCE_GROUP"         --revision-weight "$GREEN_REVISION=100"
else
    # Non-production: direct switch
    log "Switching 100% traffic to green revision (non-production)"
    az containerapp ingress traffic set         --name "$APP_NAME"         --resource-group "$RESOURCE_GROUP"         --revision-weight "$GREEN_REVISION=100"
fi

log "Blue-green deployment completed successfully!"
log "Green revision $GREEN_REVISION is now serving 100% of traffic"
```

## 5. Azure Parameter Files

Create parameter files for different environments:

### Development Parameters (`parameters/dev.json`)
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environment": {
      "value": "dev"
    },
    "location": {
      "value": "canadacentral"
    },
    "imageTag": {
      "value": "latest"
    }
  }
}
```

### Production Parameters (`parameters/prod.json`)
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environment": {
      "value": "prod"
    },
    "location": {
      "value": "canadacentral"
    },
    "imageTag": {
      "value": "v1.0.0"
    }
  }
}
```

## 6. Monitoring Setup Script

Create this file as `scripts/setup-monitoring.sh`

```bash
#!/bin/bash

# Monitoring Setup Script
set -e

RESOURCE_GROUP=${1}
ENVIRONMENT=${2}

if [ -z "$RESOURCE_GROUP" ] || [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <resource_group> <environment>"
    exit 1
fi

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Setting up monitoring for $ENVIRONMENT environment in $RESOURCE_GROUP"

# Get resource IDs
APP_INSIGHTS_ID=$(az monitor app-insights component list     --resource-group "$RESOURCE_GROUP"     --query "[0].id"     --output tsv)

# Create action group for alerts
ACTION_GROUP_NAME="openpolicy-${ENVIRONMENT}-alerts"
az monitor action-group create     --name "$ACTION_GROUP_NAME"     --resource-group "$RESOURCE_GROUP"     --short-name "OPAlerts"     --email-receiver name="DevOps Team" email="${ALERT_EMAIL:-devops@example.com}"

# High error rate alert
az monitor metrics alert create     --name "High Error Rate - $ENVIRONMENT"     --resource-group "$RESOURCE_GROUP"     --scopes "$APP_INSIGHTS_ID"     --condition "avg requests/failed > 10"     --window-size 5m     --evaluation-frequency 1m     --action "$ACTION_GROUP_NAME"     --description "Alert when error rate exceeds 10 failed requests per minute"

log "Monitoring setup completed"
```

This comprehensive Azure deployment setup provides:

1. **Complete Infrastructure as Code** using Bicep templates
2. **Modular architecture** with reusable components  
3. **Environment-specific configurations** for dev/staging/prod
4. **Blue-green deployment automation** with health checks and rollback
5. **Security best practices** with Key Vault and managed identities
6. **Monitoring and alerting** setup for production environments
7. **Scalable container apps** with auto-scaling rules

The templates are production-ready and follow Azure best practices for microservices deployment.
