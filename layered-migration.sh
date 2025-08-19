#!/bin/bash

# Layered Migration Script for OpenPolicyPlatformV4
# This script implements the 6-layer architecture consolidation

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_ORG="${1:-ashish-tandon}"
AZURE_SUBSCRIPTION="${2:-your-subscription-id}"
LAYER="${3:-all}"

# Repository names
INFRA_REPO="openpolicy-infrastructure"
DATA_REPO="openpolicy-data"
BUSINESS_REPO="openpolicy-business"
FRONTEND_REPO="openpolicy-frontend"
LEGACY_REPO="openpolicy-legacy"
ORCHESTRATION_REPO="openpolicy-orchestration"

echo -e "${BLUE}🚀 OpenPolicyPlatform V4 - Layered Migration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to create repository
create_repository() {
    local repo_name=$1
    local description=$2
    
    echo -e "${YELLOW}Creating repository: ${repo_name}...${NC}"
    
    # Check if repo exists
    if gh repo view "${GITHUB_ORG}/${repo_name}" &>/dev/null; then
        echo -e "${GREEN}✓ Repository ${repo_name} already exists${NC}"
    else
        gh repo create "${GITHUB_ORG}/${repo_name}" \
            --public \
            --description "${description}" \
            --clone=false || {
            echo -e "${RED}✗ Failed to create ${repo_name}${NC}"
            return 1
        }
        echo -e "${GREEN}✓ Created repository ${repo_name}${NC}"
    fi
}

# Function to setup repository structure
setup_repository_structure() {
    local repo_name=$1
    local repo_path="${repo_name}"
    
    # Clone or create directory
    if [ ! -d "${repo_path}" ]; then
        git clone "https://github.com/${GITHUB_ORG}/${repo_name}.git" "${repo_path}" 2>/dev/null || {
            mkdir -p "${repo_path}"
            cd "${repo_path}"
            git init
            git remote add origin "https://github.com/${GITHUB_ORG}/${repo_name}.git"
            cd ..
        }
    fi
    
    cd "${repo_path}"
    
    # Create standard directory structure
    mkdir -p .github/workflows
    mkdir -p src/services
    mkdir -p tests
    mkdir -p scripts
    mkdir -p config
    mkdir -p docs
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
*.log
.docker/

# Testing
.coverage
.pytest_cache/
htmlcov/

# Build
dist/
build/
*.egg-info/
EOF

    cd ..
}

# Function to create CI/CD workflow
create_cicd_workflow() {
    local repo_name=$1
    local repo_path="${repo_name}"
    local workflow_file="${repo_path}/.github/workflows/ci-cd.yml"
    
    mkdir -p "$(dirname "${workflow_file}")"
    
    cat > "${workflow_file}" << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov flake8
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Test with pytest
      run: |
        pytest --cov=./src --cov-report=xml --cov-report=html

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy to Azure Container Apps
      uses: azure/container-apps-deploy-action@v1
      with:
        appSourcePath: ${{ github.workspace }}
        registryUrl: ${{ env.REGISTRY }}
        registryUsername: ${{ github.actor }}
        registryPassword: ${{ secrets.GITHUB_TOKEN }}
        containerAppName: ${{ github.event.repository.name }}
        resourceGroup: openpolicy-platform-rg
EOF
}

# Function to migrate infrastructure layer
migrate_infrastructure_layer() {
    echo -e "${BLUE}🔧 Migrating Infrastructure Layer...${NC}"
    
    create_repository "${INFRA_REPO}" "Infrastructure services for OpenPolicy Platform"
    setup_repository_structure "${INFRA_REPO}"
    
    cd "${INFRA_REPO}"
    
    # Copy infrastructure services
    cp -r ../open-policy-platform/services/auth-service ./src/services/
    cp -r ../open-policy-platform/services/monitoring-service ./src/services/
    cp -r ../open-policy-platform/services/config-service ./src/services/
    cp -r ../open-policy-platform/services/api-gateway ./src/services/
    
    # Copy infrastructure configs
    cp -r ../open-policy-platform/infrastructure/gateway ./config/
    cp -r ../open-policy-platform/backend/monitoring ./config/monitoring/
    
    # Create docker-compose for infrastructure
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: openpolicy
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  auth-service:
    build: ./src/services/auth-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis

  monitoring-service:
    build: ./src/services/monitoring-service
    environment:
      - PROMETHEUS_URL=http://prometheus:9090
      - GRAFANA_URL=http://grafana:3000
    depends_on:
      - prometheus
      - grafana

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./config/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana

  api-gateway:
    build: ./src/services/api-gateway
    ports:
      - "9000:9000"
    environment:
      - AUTH_SERVICE_URL=http://auth-service:9001
      - MONITORING_SERVICE_URL=http://monitoring-service:9006
    depends_on:
      - auth-service
      - monitoring-service

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
EOF

    # Create README
    cat > README.md << 'EOF'
# OpenPolicy Infrastructure Layer

This repository contains the infrastructure services for the OpenPolicy Platform.

## Services Included

1. **Authentication Service** - JWT-based authentication
2. **Monitoring Service** - System health monitoring
3. **Configuration Service** - Centralized configuration
4. **API Gateway** - Central entry point for all APIs
5. **PostgreSQL** - Primary database
6. **Redis** - Cache and message broker
7. **Prometheus** - Metrics collection
8. **Grafana** - Monitoring dashboards
9. **Elasticsearch** - Log storage
10. **Logstash** - Log processing
11. **Kibana** - Log visualization

## Quick Start

```bash
# Set up environment
cp .env.example .env
# Edit .env with your values

# Start services
docker-compose up -d

# Check health
docker-compose ps
```

## Deployment

This layer is deployed first as it provides core services for all other layers.
EOF

    create_cicd_workflow "${INFRA_REPO}"
    
    git add .
    git commit -m "Initial infrastructure layer setup" || true
    git push origin main || true
    
    cd ..
    echo -e "${GREEN}✓ Infrastructure layer migration complete${NC}"
}

# Function to migrate data layer
migrate_data_layer() {
    echo -e "${BLUE}📊 Migrating Data Layer...${NC}"
    
    create_repository "${DATA_REPO}" "Data processing services for OpenPolicy Platform"
    setup_repository_structure "${DATA_REPO}"
    
    cd "${DATA_REPO}"
    
    # Copy data services
    cp -r ../open-policy-platform/services/etl-service ./src/services/
    cp -r ../open-policy-platform/services/data-management-service ./src/services/
    cp -r ../open-policy-platform/services/scraper-service ./src/services/
    cp -r ../open-policy-platform/services/policy-service ./src/services/
    cp -r ../open-policy-platform/services/search-service ./src/services/
    cp -r ../open-policy-platform/services/files-service ./src/services/
    
    # Copy scrapers
    cp -r ../open-policy-platform/scrapers ./
    
    # Create docker-compose for data layer
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  etl-service:
    build: ./src/services/etl-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis

  data-management-service:
    build: ./src/services/data-management-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  scraper-service:
    build: ./src/services/scraper-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SCRAPERS_DATA_DIR=/app/scrapers-data
    volumes:
      - ./scrapers:/scrapers:ro
      - scrapers_data:/app/scrapers-data

  policy-service:
    build: ./src/services/policy-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  search-service:
    build: ./src/services/search-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ELASTICSEARCH_URL=${ELASTICSEARCH_URL}

  files-service:
    build: ./src/services/files-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - STORAGE_PATH=/app/storage
    volumes:
      - files_storage:/app/storage

volumes:
  scrapers_data:
  files_storage:
EOF

    create_cicd_workflow "${DATA_REPO}"
    
    git add .
    git commit -m "Initial data layer setup" || true
    git push origin main || true
    
    cd ..
    echo -e "${GREEN}✓ Data layer migration complete${NC}"
}

# Function to migrate business layer
migrate_business_layer() {
    echo -e "${BLUE}💼 Migrating Business Layer...${NC}"
    
    create_repository "${BUSINESS_REPO}" "Business logic services for OpenPolicy Platform"
    setup_repository_structure "${BUSINESS_REPO}"
    
    cd "${BUSINESS_REPO}"
    
    # Copy business services
    cp -r ../open-policy-platform/services/committees-service ./src/services/
    cp -r ../open-policy-platform/services/representatives-service ./src/services/
    cp -r ../open-policy-platform/services/votes-service ./src/services/
    cp -r ../open-policy-platform/services/debates-service ./src/services/
    cp -r ../open-policy-platform/services/analytics-service ./src/services/
    cp -r ../open-policy-platform/services/reporting-service ./src/services/
    cp -r ../open-policy-platform/services/dashboard-service ./src/services/
    cp -r ../open-policy-platform/services/plotly-service ./src/services/
    cp -r ../open-policy-platform/services/workflow-service ./src/services/
    cp -r ../open-policy-platform/services/integration-service ./src/services/
    
    create_cicd_workflow "${BUSINESS_REPO}"
    
    git add .
    git commit -m "Initial business layer setup" || true
    git push origin main || true
    
    cd ..
    echo -e "${GREEN}✓ Business layer migration complete${NC}"
}

# Function to migrate frontend layer
migrate_frontend_layer() {
    echo -e "${BLUE}🎨 Migrating Frontend Layer...${NC}"
    
    create_repository "${FRONTEND_REPO}" "Frontend services for OpenPolicy Platform"
    setup_repository_structure "${FRONTEND_REPO}"
    
    cd "${FRONTEND_REPO}"
    
    # Copy frontend services
    cp -r ../open-policy-platform/web ./src/web/
    cp -r ../open-policy-platform/services/mobile-api ./src/services/
    cp -r ../open-policy-platform/backend/api ./src/api/
    
    # Copy mobile apps
    cp -r ../open-policy-platform/mobile ./
    
    create_cicd_workflow "${FRONTEND_REPO}"
    
    git add .
    git commit -m "Initial frontend layer setup" || true
    git push origin main || true
    
    cd ..
    echo -e "${GREEN}✓ Frontend layer migration complete${NC}"
}

# Function to migrate legacy layer
migrate_legacy_layer() {
    echo -e "${BLUE}🏛️ Migrating Legacy Layer...${NC}"
    
    create_repository "${LEGACY_REPO}" "Legacy services for OpenPolicy Platform"
    setup_repository_structure "${LEGACY_REPO}"
    
    cd "${LEGACY_REPO}"
    
    # Copy legacy services
    cp -r ../open-policy-platform/services/legacy-django ./src/services/
    cp -r ../open-policy-platform/services/mcp-service ./src/services/
    cp -r ../open-policy-platform/services/docker-monitor ./src/services/
    
    create_cicd_workflow "${LEGACY_REPO}"
    
    git add .
    git commit -m "Initial legacy layer setup" || true
    git push origin main || true
    
    cd ..
    echo -e "${GREEN}✓ Legacy layer migration complete${NC}"
}

# Function to create orchestration repository
create_orchestration_layer() {
    echo -e "${BLUE}🎭 Creating Orchestration Layer...${NC}"
    
    create_repository "${ORCHESTRATION_REPO}" "Orchestration and deployment for OpenPolicy Platform"
    setup_repository_structure "${ORCHESTRATION_REPO}"
    
    cd "${ORCHESTRATION_REPO}"
    
    # Create orchestration files
    cat > docker-compose.platform.yml << 'EOF'
version: '3.8'

# This file orchestrates all layers of the platform
# Use with: docker-compose -f docker-compose.platform.yml up

services:
  # Infrastructure Layer
  infrastructure:
    image: ghcr.io/ashish-tandon/openpolicy-infrastructure:latest
    networks:
      - openpolicy-network

  # Data Layer
  data:
    image: ghcr.io/ashish-tandon/openpolicy-data:latest
    depends_on:
      - infrastructure
    networks:
      - openpolicy-network

  # Business Layer
  business:
    image: ghcr.io/ashish-tandon/openpolicy-business:latest
    depends_on:
      - data
    networks:
      - openpolicy-network

  # Frontend Layer
  frontend:
    image: ghcr.io/ashish-tandon/openpolicy-frontend:latest
    depends_on:
      - business
    ports:
      - "80:80"
      - "3000:3000"
    networks:
      - openpolicy-network

  # Legacy Layer (optional)
  legacy:
    image: ghcr.io/ashish-tandon/openpolicy-legacy:latest
    profiles:
      - legacy
    networks:
      - openpolicy-network

networks:
  openpolicy-network:
    driver: bridge
EOF

    # Create deployment script
    cat > deploy-platform.sh << 'EOF'
#!/bin/bash

# Deploy all layers of OpenPolicy Platform

echo "🚀 Deploying OpenPolicy Platform..."

# Deploy Infrastructure Layer
echo "📦 Deploying Infrastructure Layer..."
kubectl apply -f k8s/infrastructure/

# Wait for infrastructure
kubectl wait --for=condition=ready pod -l layer=infrastructure --timeout=300s

# Deploy Data Layer
echo "📦 Deploying Data Layer..."
kubectl apply -f k8s/data/

# Wait for data services
kubectl wait --for=condition=ready pod -l layer=data --timeout=300s

# Deploy Business Layer
echo "📦 Deploying Business Layer..."
kubectl apply -f k8s/business/

# Wait for business services
kubectl wait --for=condition=ready pod -l layer=business --timeout=300s

# Deploy Frontend Layer
echo "📦 Deploying Frontend Layer..."
kubectl apply -f k8s/frontend/

# Deploy monitoring stack
echo "📦 Deploying Monitoring..."
kubectl apply -f k8s/monitoring/

echo "✅ OpenPolicy Platform deployment complete!"
echo "🌐 Access the platform at: http://localhost"
EOF

    chmod +x deploy-platform.sh
    
    create_cicd_workflow "${ORCHESTRATION_REPO}"
    
    git add .
    git commit -m "Initial orchestration setup" || true
    git push origin main || true
    
    cd ..
    echo -e "${GREEN}✓ Orchestration layer complete${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting layered migration for OpenPolicyPlatform V4${NC}"
    echo -e "${BLUE}GitHub Organization: ${GITHUB_ORG}${NC}"
    echo -e "${BLUE}Azure Subscription: ${AZURE_SUBSCRIPTION}${NC}"
    echo -e "${BLUE}Target Layer: ${LAYER}${NC}"
    echo ""
    
    case "${LAYER}" in
        "infrastructure")
            migrate_infrastructure_layer
            ;;
        "data")
            migrate_data_layer
            ;;
        "business")
            migrate_business_layer
            ;;
        "frontend")
            migrate_frontend_layer
            ;;
        "legacy")
            migrate_legacy_layer
            ;;
        "orchestration")
            create_orchestration_layer
            ;;
        "all")
            migrate_infrastructure_layer
            migrate_data_layer
            migrate_business_layer
            migrate_frontend_layer
            migrate_legacy_layer
            create_orchestration_layer
            ;;
        *)
            echo -e "${RED}Invalid layer: ${LAYER}${NC}"
            echo "Valid options: infrastructure, data, business, frontend, legacy, orchestration, all"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}✅ Migration complete!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ "${LAYER}" == "all" ]; then
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Review each repository and adjust configurations"
        echo "2. Set up Azure credentials in each repository"
        echo "3. Configure environment variables"
        echo "4. Run deployment scripts"
        echo ""
        echo -e "${BLUE}Repositories created:${NC}"
        echo "- https://github.com/${GITHUB_ORG}/${INFRA_REPO}"
        echo "- https://github.com/${GITHUB_ORG}/${DATA_REPO}"
        echo "- https://github.com/${GITHUB_ORG}/${BUSINESS_REPO}"
        echo "- https://github.com/${GITHUB_ORG}/${FRONTEND_REPO}"
        echo "- https://github.com/${GITHUB_ORG}/${LEGACY_REPO}"
        echo "- https://github.com/${GITHUB_ORG}/${ORCHESTRATION_REPO}"
    fi
}

# Run main function
main