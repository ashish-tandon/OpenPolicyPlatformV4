#!/bin/bash

# Azure AKS Setup Script for OpenPolicyPlatform V4
# This script creates and configures an AKS cluster with Key Vault integration

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
CLUSTER_NAME="openpolicy-aks"
NODE_COUNT=3
NODE_SIZE="Standard_D4s_v3"
KEY_VAULT_NAME="openpolicy-kv-$(date +%s)"
ACR_NAME="openpolicyacr$(date +%s)"
STORAGE_ACCOUNT="openpolicysa$(date +%s)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        error "Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        warning "kubectl not found. Installing..."
        az aks install-cli
    fi
    
    # Check Helm
    if ! command -v helm &> /dev/null; then
        warning "Helm not found. Installing..."
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    fi
    
    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        error "Not logged in to Azure. Please run: az login"
    fi
    
    log "✅ Prerequisites check passed"
}

# Create resource group
create_resource_group() {
    log "Creating resource group: $RESOURCE_GROUP..."
    
    if az group exists --name $RESOURCE_GROUP | grep -q "true"; then
        warning "Resource group $RESOURCE_GROUP already exists"
    else
        az group create --name $RESOURCE_GROUP --location $LOCATION
        log "✅ Resource group created"
    fi
}

# Create Azure Container Registry
create_acr() {
    log "Creating Azure Container Registry: $ACR_NAME..."
    
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Standard \
        --admin-enabled true
    
    log "✅ ACR created"
}

# Create Key Vault
create_key_vault() {
    log "Creating Azure Key Vault: $KEY_VAULT_NAME..."
    
    az keyvault create \
        --name $KEY_VAULT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --enable-rbac-authorization false
    
    log "✅ Key Vault created"
}

# Add secrets to Key Vault
add_secrets() {
    log "Adding secrets to Key Vault..."
    
    # Database password
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "postgres-password" \
        --value "$(openssl rand -base64 32)"
    
    # Redis password
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "redis-password" \
        --value "$(openssl rand -base64 32)"
    
    # JWT secret
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "jwt-secret" \
        --value "$(openssl rand -base64 64)"
    
    # Admin password
    az keyvault secret set \
        --vault-name $KEY_VAULT_NAME \
        --name "admin-password" \
        --value "$(openssl rand -base64 16)"
    
    log "✅ Secrets added to Key Vault"
}

# Create AKS cluster
create_aks_cluster() {
    log "Creating AKS cluster: $CLUSTER_NAME..."
    
    az aks create \
        --resource-group $RESOURCE_GROUP \
        --name $CLUSTER_NAME \
        --node-count $NODE_COUNT \
        --node-vm-size $NODE_SIZE \
        --enable-managed-identity \
        --enable-addons monitoring,azure-keyvault-secrets-provider \
        --enable-cluster-autoscaler \
        --min-count 3 \
        --max-count 10 \
        --network-plugin azure \
        --network-policy calico \
        --generate-ssh-keys \
        --attach-acr $ACR_NAME
    
    log "✅ AKS cluster created"
}

# Configure kubectl
configure_kubectl() {
    log "Configuring kubectl..."
    
    az aks get-credentials \
        --resource-group $RESOURCE_GROUP \
        --name $CLUSTER_NAME \
        --overwrite-existing
    
    # Verify connection
    kubectl get nodes
    
    log "✅ kubectl configured"
}

# Install ingress controller
install_ingress() {
    log "Installing NGINX Ingress Controller..."
    
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    
    helm install ingress-nginx ingress-nginx/ingress-nginx \
        --create-namespace \
        --namespace ingress-nginx \
        --set controller.service.externalTrafficPolicy=Local \
        --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path"=/healthz
    
    log "✅ Ingress controller installed"
}

# Install cert-manager
install_cert_manager() {
    log "Installing cert-manager..."
    
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    helm install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.13.0 \
        --set installCRDs=true
    
    # Wait for cert-manager to be ready
    kubectl wait --namespace cert-manager \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/instance=cert-manager \
        --timeout=300s
    
    log "✅ cert-manager installed"
}

# Create cluster issuer
create_cluster_issuer() {
    log "Creating Let's Encrypt cluster issuer..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@openpolicyplatform.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    
    log "✅ Cluster issuer created"
}

# Configure Key Vault integration
configure_key_vault_integration() {
    log "Configuring Key Vault integration..."
    
    # Get cluster identity
    IDENTITY_CLIENT_ID=$(az aks show -g $RESOURCE_GROUP -n $CLUSTER_NAME --query identityProfile.kubeletidentity.clientId -o tsv)
    
    # Grant Key Vault access
    az keyvault set-policy \
        --name $KEY_VAULT_NAME \
        --secret-permissions get list \
        --spn $IDENTITY_CLIENT_ID
    
    # Create SecretProviderClass
    cat <<EOF | kubectl apply -f -
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-kvname-system-msi
  namespace: open-policy-platform
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "$IDENTITY_CLIENT_ID"
    keyvaultName: "$KEY_VAULT_NAME"
    objects: |
      array:
        - |
          objectName: postgres-password
          objectType: secret
        - |
          objectName: redis-password
          objectType: secret
        - |
          objectName: jwt-secret
          objectType: secret
        - |
          objectName: admin-password
          objectType: secret
    tenantId: "$(az account show --query tenantId -o tsv)"
  secretObjects:
  - secretName: platform-secrets
    type: Opaque
    data:
    - objectName: postgres-password
      key: postgres-password
    - objectName: redis-password
      key: redis-password
    - objectName: jwt-secret
      key: jwt-secret
    - objectName: admin-password
      key: admin-password
EOF
    
    log "✅ Key Vault integration configured"
}

# Create storage account for persistent volumes
create_storage_account() {
    log "Creating storage account: $STORAGE_ACCOUNT..."
    
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2
    
    # Get connection string
    STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --query connectionString -o tsv)
    
    # Create file shares
    az storage share create \
        --name postgres-data \
        --quota 100 \
        --connection-string "$STORAGE_CONNECTION_STRING"
    
    az storage share create \
        --name redis-data \
        --quota 20 \
        --connection-string "$STORAGE_CONNECTION_STRING"
    
    log "✅ Storage account created"
}

# Deploy monitoring stack
deploy_monitoring() {
    log "Deploying monitoring stack..."
    
    # Add Prometheus community repo
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Install kube-prometheus-stack
    helm install monitoring prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.retention=30d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
        --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=10Gi
    
    log "✅ Monitoring stack deployed"
}

# Create deployment summary
create_summary() {
    log "Creating deployment summary..."
    
    cat > azure-aks-deployment-summary.txt << EOF
Azure AKS Deployment Summary
============================
Date: $(date)

Resource Group: $RESOURCE_GROUP
Location: $LOCATION
Cluster Name: $CLUSTER_NAME
ACR Name: $ACR_NAME
Key Vault Name: $KEY_VAULT_NAME
Storage Account: $STORAGE_ACCOUNT

Cluster Details:
- Node Count: $NODE_COUNT (autoscaling 3-10)
- Node Size: $NODE_SIZE
- Network Plugin: Azure CNI
- Network Policy: Calico

Installed Components:
- NGINX Ingress Controller
- cert-manager with Let's Encrypt
- Azure Key Vault CSI Driver
- Prometheus & Grafana monitoring

Next Steps:
1. Build and push Docker images to ACR:
   az acr build --registry $ACR_NAME --image openpolicy/api-gateway:latest ./services/api-gateway

2. Deploy OpenPolicyPlatform:
   helm install open-policy-platform ./charts/open-policy-platform \
     --namespace open-policy-platform \
     --create-namespace \
     --values ./charts/open-policy-platform/values-azure.yaml

3. Get ingress IP:
   kubectl get service -n ingress-nginx ingress-nginx-controller

4. Configure DNS to point to the ingress IP

5. Access monitoring:
   kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

Default Grafana credentials:
- Username: admin
- Password: prom-operator

Key Vault secrets are automatically available in the cluster.
EOF
    
    log "✅ Summary saved to: azure-aks-deployment-summary.txt"
}

# Main execution
main() {
    echo "🚀 Azure AKS Setup for OpenPolicyPlatform V4"
    echo "==========================================="
    echo ""
    echo "This script will create:"
    echo "- Resource Group: $RESOURCE_GROUP"
    echo "- AKS Cluster: $CLUSTER_NAME"
    echo "- Container Registry: $ACR_NAME"
    echo "- Key Vault: $KEY_VAULT_NAME"
    echo "- Storage Account: $STORAGE_ACCOUNT"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    check_prerequisites
    create_resource_group
    create_acr
    create_key_vault
    add_secrets
    create_aks_cluster
    configure_kubectl
    install_ingress
    install_cert_manager
    create_cluster_issuer
    configure_key_vault_integration
    create_storage_account
    deploy_monitoring
    create_summary
    
    echo ""
    echo "✅ Azure AKS setup complete!"
    echo ""
    echo "📄 See azure-aks-deployment-summary.txt for details and next steps"
}

# Run main function
main "$@"