#!/bin/bash

# Azure Deployment Script for OpenPolicyPlatform V4
# This script handles the complete deployment to Azure AKS

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
CLUSTER_NAME="openpolicy-aks"
ACR_NAME="openpolicyacr"
KEY_VAULT_NAME="openpolicy-kv"
NAMESPACE="production"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if Azure CLI is installed and logged in
check_azure_cli() {
    log "Checking Azure CLI..."
    
    if ! command -v az &> /dev/null; then
        error "Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    fi
    
    if ! az account show &> /dev/null; then
        error "Not logged in to Azure. Please run: az login"
    fi
    
    log "✅ Azure CLI is ready"
}

# Build and push Docker images to ACR
build_and_push_images() {
    log "Building and pushing Docker images to ACR..."
    
    # Get ACR login credentials
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
    az acr login --name $ACR_NAME
    
    # List of services to build
    local services=(
        "api-gateway"
        "auth-service"
        "policy-service"
        "notification-service"
        "config-service"
        "search-service"
        "dashboard-service"
        "web"
        "admin-dashboard"
    )
    
    for service in "${services[@]}"; do
        log "Building $service..."
        
        if [ "$service" == "web" ] || [ "$service" == "admin-dashboard" ]; then
            docker build -t $ACR_LOGIN_SERVER/opp-$service:latest -t $ACR_LOGIN_SERVER/opp-$service:v4.0.0 ./apps/web/
        else
            docker build -t $ACR_LOGIN_SERVER/opp-$service:latest -t $ACR_LOGIN_SERVER/opp-$service:v4.0.0 ./services/$service/
        fi
        
        log "Pushing $service to ACR..."
        docker push $ACR_LOGIN_SERVER/opp-$service:latest
        docker push $ACR_LOGIN_SERVER/opp-$service:v4.0.0
    done
    
    log "✅ All images built and pushed successfully"
}

# Create Kubernetes namespace
create_namespace() {
    log "Creating namespace: $NAMESPACE"
    
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    kubectl label namespace $NAMESPACE environment=production --overwrite
    
    log "✅ Namespace created"
}

# Deploy secrets from Key Vault
deploy_secrets() {
    log "Deploying secrets from Key Vault..."
    
    # Create secret provider class
    cat <<EOF | kubectl apply -f -
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-keyvault-secrets
  namespace: $NAMESPACE
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
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
    
    log "✅ Secrets deployed"
}

# Deploy platform using Helm
deploy_platform() {
    log "Deploying OpenPolicyPlatform using Helm..."
    
    # Update Helm values with ACR registry
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
    
    # Create temporary values file with ACR registry
    cat > /tmp/azure-values-override.yaml <<EOF
global:
  imageRegistry: "$ACR_LOGIN_SERVER/"
  imagePullSecrets:
    - name: acr-secret

ingress:
  enabled: true
  hosts:
    - host: openpolicy.azure.com
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: web
              port: 3000
        - path: /api
          pathType: Prefix
          backend:
            service:
              name: api-gateway
              port: 9000
    - host: admin.openpolicy.azure.com
      paths:
        - path: /
          pathType: Prefix
          backend:
            service:
              name: admin-dashboard
              port: 3001
  tls:
    - secretName: openpolicy-tls
      hosts:
        - openpolicy.azure.com
        - admin.openpolicy.azure.com
EOF
    
    # Deploy using Helm
    helm upgrade --install open-policy-platform \
        ./charts/open-policy-platform \
        --namespace $NAMESPACE \
        --values ./charts/open-policy-platform/values-azure.yaml \
        --values /tmp/azure-values-override.yaml \
        --timeout 10m \
        --wait
    
    log "✅ Platform deployed successfully"
}

# Check deployment status
check_deployment_status() {
    log "Checking deployment status..."
    
    # Wait for all pods to be ready
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/instance=open-policy-platform \
        -n $NAMESPACE \
        --timeout=300s
    
    # Get pod status
    echo ""
    info "Pod Status:"
    kubectl get pods -n $NAMESPACE
    
    # Get service status
    echo ""
    info "Service Status:"
    kubectl get svc -n $NAMESPACE
    
    # Get ingress status
    echo ""
    info "Ingress Status:"
    kubectl get ingress -n $NAMESPACE
    
    log "✅ All services are running"
}

# Get public IP and URLs
get_access_urls() {
    log "Getting access URLs..."
    
    # Get ingress IP
    INGRESS_IP=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$INGRESS_IP" ]; then
        warning "Ingress IP not yet assigned. Waiting..."
        sleep 30
        INGRESS_IP=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
    fi
    
    echo ""
    info "Access URLs:"
    echo "  Main Platform: http://$INGRESS_IP (configure DNS: openpolicy.azure.com → $INGRESS_IP)"
    echo "  Admin Dashboard: http://$INGRESS_IP (configure DNS: admin.openpolicy.azure.com → $INGRESS_IP)"
    echo ""
    info "To access with custom domains, update your DNS records or /etc/hosts:"
    echo "  $INGRESS_IP openpolicy.azure.com"
    echo "  $INGRESS_IP admin.openpolicy.azure.com"
}

# Run smoke tests
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Get ingress IP
    INGRESS_IP=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')
    
    # Test API Gateway health
    if curl -f -s "http://$INGRESS_IP/api/health" | grep -q "healthy"; then
        log "✅ API Gateway is healthy"
    else
        error "API Gateway health check failed"
    fi
    
    # Test web frontend
    if curl -f -s "http://$INGRESS_IP" | grep -q "OpenPolicy"; then
        log "✅ Web frontend is accessible"
    else
        warning "Web frontend might not be fully loaded yet"
    fi
}

# Create monitoring dashboard
setup_monitoring() {
    log "Setting up monitoring dashboard..."
    
    # Create port-forward for Grafana
    kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &
    GRAFANA_PID=$!
    
    sleep 5
    
    info "Grafana is accessible at: http://localhost:3000"
    info "Default credentials: admin / prom-operator"
    info "To stop port-forward: kill $GRAFANA_PID"
}

# Main deployment flow
main() {
    echo "🚀 Azure Deployment for OpenPolicyPlatform V4"
    echo "============================================"
    echo ""
    echo "This will deploy to:"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  AKS Cluster: $CLUSTER_NAME"
    echo "  ACR: $ACR_NAME"
    echo "  Namespace: $NAMESPACE"
    echo ""
    
    # Check prerequisites
    check_azure_cli
    
    # Get AKS credentials
    log "Getting AKS credentials..."
    az aks get-credentials --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME --overwrite-existing
    
    # Create namespace
    create_namespace
    
    # Deploy secrets
    deploy_secrets
    
    # Build and push images
    info "Building Docker images (this may take 10-15 minutes)..."
    build_and_push_images
    
    # Deploy platform
    deploy_platform
    
    # Check status
    check_deployment_status
    
    # Get URLs
    get_access_urls
    
    # Run tests
    run_smoke_tests
    
    # Setup monitoring
    setup_monitoring
    
    # Create summary
    cat > azure-deployment-summary-$(date +%Y%m%d-%H%M%S).txt << EOF
Azure Deployment Summary
========================
Date: $(date)
Resource Group: $RESOURCE_GROUP
AKS Cluster: $CLUSTER_NAME
ACR: $ACR_NAME
Namespace: $NAMESPACE

Deployment Status: SUCCESS

Access URLs:
- Platform: http://$INGRESS_IP (openpolicy.azure.com)
- Admin: http://$INGRESS_IP (admin.openpolicy.azure.com)
- API Gateway: http://$INGRESS_IP/api
- Grafana: http://localhost:3000

Next Steps:
1. Configure DNS records to point to $INGRESS_IP
2. Enable SSL/TLS certificates
3. Configure backup procedures
4. Set up monitoring alerts
5. Review security settings

Commands:
- View pods: kubectl get pods -n $NAMESPACE
- View logs: kubectl logs -n $NAMESPACE [pod-name]
- Scale deployment: kubectl scale deployment [name] --replicas=3 -n $NAMESPACE
- Update image: kubectl set image deployment/[name] [container]=[image] -n $NAMESPACE
EOF
    
    echo ""
    echo "✅ Deployment completed successfully!"
    echo "📄 Summary saved to: azure-deployment-summary-*.txt"
}

# Handle script interruption
trap 'echo "Deployment interrupted. Cleaning up..."; exit 1' INT TERM

# Run main function
main "$@"