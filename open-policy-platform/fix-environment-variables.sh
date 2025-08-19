#!/bin/bash

# Fix environment variable warnings for Azure deployment

echo "🔧 Fixing environment variable warnings..."

# Create a complete environment file with all required Azure variables
cat > env.azure.complete <<EOF
# Azure Configuration
AZURE_KEY_VAULT_URL=https://openpolicy-keyvault.vault.azure.net/
AZURE_SEARCH_SERVICE=openpolicy-search
AZURE_CLIENT_ID=your-azure-client-id
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_SUBSCRIPTION_ID=5602b849-384e-4da7-8b75-fd5eb70ea355

# Database Configuration
DATABASE_URL=postgresql://openpolicy:openpolicy123@postgres:5432/openpolicy
DATABASE_URL_TEST=postgresql://openpolicy:openpolicy123@postgres-test:5432/openpolicy_test
POSTGRES_DB=openpolicy
POSTGRES_USER=openpolicy
POSTGRES_PASSWORD=openpolicy123

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Service Configuration
SERVICE_NAME=openpolicy
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
DEBUG=False

# Auth0 Configuration
AUTH0_DOMAIN=dev-openpolicy.ca.auth0.com
AUTH0_CLIENT_ID=zR9zxYpZnRjaMHUfIOTUx9BSMfOekrnG
AUTH0_CLIENT_SECRET=tVfKcn-qUhC9d3v0ihtICtWxgAhMlLeMCwWZBIS2jXTrph72nf4m7kZ1Q4VqO5yo
AUTH0_AUDIENCE=https://api.openpolicy.com

# API Configuration
API_BASE_URL=http://api-gateway:9000
FRONTEND_URL=http://web:3000

# Logging Configuration
LOG_LEVEL=INFO
ELASTICSEARCH_HOST=elasticsearch:9200
FLUENTD_HOST=fluentd
FLUENTD_PORT=24224

# Monitoring Configuration
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF

echo "✅ Created env.azure.complete with all required variables"

# Create a script to export these variables
cat > export-env-vars.sh <<'EOF'
#!/bin/bash
# Export all environment variables from env.azure.complete

set -a
source env.azure.complete
set +a

echo "✅ Environment variables exported successfully"
EOF

chmod +x export-env-vars.sh

# Create docker-compose override to use env_file
cat > docker-compose.override.yml <<EOF
# Override file to fix environment variable warnings

services:
  # Apply env_file to all services
  postgres:
    env_file: ./env.azure.complete
  
  postgres-test:
    env_file: ./env.azure.complete
  
  redis:
    env_file: ./env.azure.complete
  
  elasticsearch:
    env_file: ./env.azure.complete
  
  logstash:
    env_file: ./env.azure.complete
  
  kibana:
    env_file: ./env.azure.complete
  
  prometheus:
    env_file: ./env.azure.complete
  
  grafana:
    env_file: ./env.azure.complete
  
  fluentd:
    env_file: ./env.azure.complete
  
  api-gateway:
    env_file: ./env.azure.complete
  
  config-service:
    env_file: ./env.azure.complete
  
  auth-service:
    env_file: ./env.azure.complete
  
  policy-service:
    env_file: ./env.azure.complete
  
  notification-service:
    env_file: ./env.azure.complete
  
  analytics-service:
    env_file: ./env.azure.complete
  
  monitoring-service:
    env_file: ./env.azure.complete
  
  etl-service:
    env_file: ./env.azure.complete
  
  scraper-service:
    env_file: ./env.azure.complete
  
  search-service:
    env_file: ./env.azure.complete
  
  dashboard-service:
    env_file: ./env.azure.complete
  
  files-service:
    env_file: ./env.azure.complete
  
  reporting-service:
    env_file: ./env.azure.complete
  
  workflow-service:
    env_file: ./env.azure.complete
  
  integration-service:
    env_file: ./env.azure.complete
  
  data-management-service:
    env_file: ./env.azure.complete
  
  representatives-service:
    env_file: ./env.azure.complete
  
  plotly-service:
    env_file: ./env.azure.complete
  
  mobile-api:
    env_file: ./env.azure.complete
  
  legacy-django:
    env_file: ./env.azure.complete
  
  docker-monitor:
    env_file: ./env.azure.complete
  
  web:
    env_file: ./env.azure.complete
EOF

echo "✅ Created docker-compose.override.yml"

# Create a deployment script that sources environment first
cat > deploy-with-env.sh <<'EOF'
#!/bin/bash

# Source environment variables
source ./export-env-vars.sh

# Deploy with both files
docker-compose -f docker-compose.complete.yml -f docker-compose.override.yml up -d

echo "✅ Deployment started with proper environment configuration"
EOF

chmod +x deploy-with-env.sh

echo "
✅ Environment variable fix complete!

To deploy without warnings:
1. Review and update env.azure.complete with your actual Azure credentials
2. Run: ./deploy-with-env.sh

This will:
- Export all required environment variables
- Use docker-compose with override file
- Eliminate all environment variable warnings
"