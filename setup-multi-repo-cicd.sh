#!/bin/bash

# 🚀 OpenPolicyPlatform V5 - Multi-Repository & CI/CD Setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}🚀 OpenPolicyPlatform V5 - Multi-Repo & CI/CD Setup${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# ========================================
# REPOSITORY STRUCTURE
# ========================================

echo -e "${CYAN}Step 1: Creating Repository Structure...${NC}"

# Create repository configuration
cat > repositories-config.json <<EOF
{
  "repositories": [
    {
      "name": "openpolicy-platform-core",
      "description": "Core platform services and infrastructure",
      "type": "core",
      "services": ["api-gateway", "postgres", "redis", "nginx"]
    },
    {
      "name": "openpolicy-platform-services",
      "description": "Business logic microservices",
      "type": "services",
      "services": ["auth", "policy", "analytics", "monitoring", "etl", "scraper"]
    },
    {
      "name": "openpolicy-platform-web",
      "description": "Web applications and frontend",
      "type": "frontend",
      "services": ["web", "admin-dashboard", "mobile-web"]
    },
    {
      "name": "openpolicy-platform-monitoring",
      "description": "Monitoring, logging, and observability",
      "type": "monitoring",
      "services": ["prometheus", "grafana", "elasticsearch", "logstash", "fluentd"]
    },
    {
      "name": "openpolicy-platform-deployment",
      "description": "Deployment configurations and scripts",
      "type": "deployment",
      "services": ["docker", "kubernetes", "helm", "terraform"]
    },
    {
      "name": "openpolicy-platform-docs",
      "description": "Documentation and API references",
      "type": "documentation",
      "services": ["docs", "api-specs", "guides"]
    }
  ]
}
EOF

echo -e "${GREEN}✅ Created repository configuration${NC}"

# ========================================
# GITHUB ACTIONS CI/CD
# ========================================

echo -e "${CYAN}Step 2: Setting up GitHub Actions CI/CD...${NC}"

mkdir -p .github/workflows

# Main CI/CD workflow
cat > .github/workflows/main-ci-cd.yml <<EOF
name: 🚀 OpenPolicyPlatform V5 - Main CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: \${{ github.repository }}

jobs:
  # ========================================
  # CODE QUALITY & TESTING
  # ========================================
  
  code-quality:
    name: 🔍 Code Quality & Testing
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐍 Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: 🟢 Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        
    - name: 📦 Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black isort mypy
        
    - name: 📦 Install Node.js dependencies
      run: |
        cd open-policy-platform/apps/web
        npm ci
        
    - name: 🔍 Run Python linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
        isort --check-only .
        mypy .
        
    - name: 🔍 Run Node.js linting
      run: |
        cd open-policy-platform/apps/web
        npm run lint
        
    - name: 🧪 Run Python tests
      run: |
        pytest --cov=. --cov-report=xml --cov-report=html
        
    - name: 🧪 Run Node.js tests
      run: |
        cd open-policy-platform/apps/web
        npm test
        
    - name: 📊 Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  # ========================================
  # SECURITY SCANNING
  # ========================================
  
  security-scan:
    name: 🔒 Security Scanning
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🔍 Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
        
    - name: 🔍 Run Bandit security linter
      run: |
        pip install bandit
        bandit -r . -f json -o bandit-report.json
        
    - name: 🔍 Run Safety check
      run: |
        pip install safety
        safety check --json --output safety-report.json
        
    - name: 📊 Upload security results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: trivy-results.sarif

  # ========================================
  # BUILD & TEST CONTAINERS
  # ========================================
  
  build-containers:
    name: 🐳 Build & Test Containers
    runs-on: ubuntu-latest
    needs: [code-quality, security-scan]
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🔐 Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
      
    - name: 🔐 Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: \${{ env.REGISTRY }}
        username: \${{ github.actor }}
        password: \${{ secrets.GITHUB_TOKEN }}
        
    - name: 🐳 Build and test containers
      run: |
        # Build core services
        docker build -t \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}/api-gateway:latest ./open-policy-platform/services/api-gateway
        docker build -t \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}/web:latest ./open-policy-platform/apps/web
        
        # Test containers
        docker run --rm \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}/api-gateway:latest --help
        docker run --rm \${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}/web:latest --help
        
    - name: 📊 Upload container scan results
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: '\${{ env.REGISTRY }}/\${{ env.IMAGE_NAME }}/api-gateway:latest'
        format: 'sarif'
        output: 'container-scan-results.sarif'

  # ========================================
  # DEPLOYMENT
  # ========================================
  
  deploy-staging:
    name: 🚀 Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build-containers]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐳 Deploy to staging
      run: |
        echo "🚀 Deploying to staging environment..."
        # Add your staging deployment commands here
        # Example: kubectl apply -f k8s/staging/
        
    - name: 🔍 Health check
      run: |
        echo "🔍 Running health checks..."
        # Add your health check commands here
        
  deploy-production:
    name: 🚀 Deploy to Production
    runs-on: ubuntu-latest
    needs: [build-containers]
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐳 Deploy to production
      run: |
        echo "🚀 Deploying to production environment..."
        # Add your production deployment commands here
        # Example: kubectl apply -f k8s/production/
        
    - name: 🔍 Health check
      run: |
        echo "🔍 Running health checks..."
        # Add your health check commands here
        
    - name: 🏷️ Create release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: v\${{ github.run_number }}
        release_name: Release v\${{ github.run_number }}
        draft: false
        prerelease: false
EOF

echo -e "${GREEN}✅ Created main CI/CD workflow${NC}"

# Repository-specific workflows
cat > .github/workflows/repository-sync.yml <<EOF
name: 🔄 Repository Synchronization

on:
  push:
    branches: [ main ]
    paths:
      - 'repositories/**'
      - '.github/workflows/repository-sync.yml'
  workflow_dispatch:

jobs:
  sync-repositories:
    name: 🔄 Sync All Repositories
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout main repository
      uses: actions/checkout@v4
      with:
        token: \${{ secrets.REPO_SYNC_TOKEN }}
        
    - name: 🔄 Sync core repository
      run: |
        echo "🔄 Syncing core repository..."
        # Add sync logic for openpolicy-platform-core
        
    - name: 🔄 Sync services repository
      run: |
        echo "🔄 Syncing services repository..."
        # Add sync logic for openpolicy-platform-services
        
    - name: 🔄 Sync web repository
      run: |
        echo "🔄 Syncing web repository..."
        # Add sync logic for openpolicy-platform-web
        
    - name: 🔄 Sync monitoring repository
      run: |
        echo "🔄 Syncing monitoring repository..."
        # Add sync logic for openpolicy-platform-monitoring
        
    - name: 🔄 Sync deployment repository
      run: |
        echo "🔄 Syncing deployment repository..."
        # Add sync logic for openpolicy-platform-deployment
        
    - name: 🔄 Sync docs repository
      run: |
        echo "🔄 Syncing docs repository..."
        # Add sync logic for openpolicy-platform-docs
EOF

echo -e "${GREEN}✅ Created repository sync workflow${NC}"

# ========================================
# REPOSITORY TEMPLATES
# ========================================

echo -e "${CYAN}Step 3: Creating Repository Templates...${NC}"

# Core repository template
mkdir -p repository-templates/core
cat > repository-templates/core/README.md <<EOF
# 🏗️ OpenPolicyPlatform Core

Core infrastructure and foundational services for OpenPolicyPlatform V5.

## Services
- **API Gateway**: Go-based API routing and management
- **PostgreSQL**: Primary database service
- **Redis**: Cache and message broker
- **Nginx**: Reverse proxy and load balancer

## Quick Start
\`\`\`bash
docker-compose up -d
\`\`\`

## Development
\`\`\`bash
# Build services
docker-compose build

# Run tests
docker-compose run --rm api-gateway go test ./...

# Development mode
docker-compose -f docker-compose.dev.yml up
\`\`\`
EOF

# Services repository template
mkdir -p repository-templates/services
cat > repository-templates/services/README.md <<EOF
# 🔧 OpenPolicyPlatform Services

Business logic microservices for OpenPolicyPlatform V5.

## Services
- **Auth Service**: Authentication and authorization
- **Policy Service**: Policy management and analysis
- **Analytics Service**: Data analytics and insights
- **Monitoring Service**: Service monitoring and health
- **ETL Service**: Data extraction, transformation, loading
- **Scraper Service**: Web scraping and data collection

## Quick Start
\`\`\`bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d auth-service policy-service
\`\`\`

## Development
\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run service locally
uvicorn main:app --reload
\`\`\`
EOF

# Web repository template
mkdir -p repository-templates/web
cat > repository-templates/web/README.md <<EOF
# 🌐 OpenPolicyPlatform Web

Web applications and frontend for OpenPolicyPlatform V5.

## Applications
- **Web App**: Main user interface
- **Admin Dashboard**: Administrative interface
- **Mobile Web**: Mobile-optimized web app

## Quick Start
\`\`\`bash
# Install dependencies
npm install

# Development mode
npm run dev

# Build for production
npm run build
\`\`\`

## Development
\`\`\`bash
# Run tests
npm test

# Lint code
npm run lint

# Type check
npm run type-check
\`\`\`
EOF

# Monitoring repository template
mkdir -p repository-templates/monitoring
cat > repository-templates/monitoring/README.md <<EOF
# 📊 OpenPolicyPlatform Monitoring

Monitoring, logging, and observability for OpenPolicyPlatform V5.

## Services
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Elasticsearch**: Log storage and search
- **Logstash**: Log processing pipeline
- **Fluentd**: Log aggregation

## Quick Start
\`\`\`bash
# Start monitoring stack
docker-compose up -d

# Access Grafana
open http://localhost:3001
# Default: admin/admin

# Access Prometheus
open http://localhost:9090
\`\`\`

## Dashboards
- Platform Overview
- Service Health
- Performance Metrics
- Error Tracking
EOF

# Deployment repository template
mkdir -p repository-templates/deployment
cat > repository-templates/deployment/README.md <<EOF
# 🚀 OpenPolicyPlatform Deployment

Deployment configurations and infrastructure for OpenPolicyPlatform V5.

## Environments
- **Development**: Local development setup
- **Staging**: Pre-production testing
- **Production**: Live production environment

## Technologies
- **Docker**: Containerization
- **Kubernetes**: Orchestration
- **Helm**: Package management
- **Terraform**: Infrastructure as Code

## Quick Start
\`\`\`bash
# Local development
./deploy-local.sh

# Staging deployment
./deploy-staging.sh

# Production deployment
./deploy-production.sh
\`\`\`

## Infrastructure
- Azure Cloud
- QNAP NAS
- Kubernetes clusters
- Load balancers
EOF

# Documentation repository template
mkdir -p repository-templates/docs
cat > repository-templates/docs/README.md <<EOF
# 📚 OpenPolicyPlatform Documentation

Comprehensive documentation for OpenPolicyPlatform V5.

## Sections
- **User Guides**: End-user documentation
- **API Reference**: API specifications
- **Developer Guides**: Development documentation
- **Architecture**: System design documents
- **Deployment**: Deployment guides

## Quick Start
\`\`\`bash
# Install documentation tools
npm install -g docsify-cli

# Serve locally
docsify serve docs

# Build static site
npm run build
\`\`\`

## Contributing
1. Edit markdown files in \`docs/\`
2. Update API specifications
3. Add diagrams and examples
4. Submit pull request
EOF

echo -e "${GREEN}✅ Created repository templates${NC}"

# ========================================
# REPOSITORY CREATION SCRIPT
# ========================================

echo -e "${CYAN}Step 4: Creating Repository Setup Script...${NC}"

cat > create-repositories.sh <<'EOF'
#!/bin/bash

# Script to create all OpenPolicyPlatform V5 repositories

set -e

echo "🚀 Creating OpenPolicyPlatform V5 Repositories..."

# GitHub organization/user
ORG="ashish-tandon"

# Repository names
REPOS=(
    "openpolicy-platform-core"
    "openpolicy-platform-services"
    "openpolicy-platform-web"
    "openpolicy-platform-monitoring"
    "openpolicy-platform-deployment"
    "openpolicy-platform-docs"
)

# Create each repository
for repo in "${REPOS[@]}"; do
    echo "📦 Creating $repo..."
    
    # Create repository using GitHub CLI
    gh repo create "$ORG/$repo" \
        --description "OpenPolicyPlatform V5 - $repo" \
        --public \
        --clone
    
    echo "✅ Created $repo"
done

echo ""
echo "🎉 All repositories created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Push code to each repository"
echo "2. Set up branch protection rules"
echo "3. Configure CI/CD workflows"
echo "4. Set up repository secrets"
echo "5. Enable security scanning"
EOF

chmod +x create-repositories.sh

# ========================================
# BRANCH PROTECTION CONFIGURATION
# ========================================

echo -e "${CYAN}Step 5: Creating Branch Protection Configuration...${NC}"

cat > branch-protection-config.json <<EOF
{
  "branch_protection": {
    "main": {
      "required_status_checks": {
        "strict": true,
        "contexts": [
          "code-quality",
          "security-scan",
          "build-containers"
        ]
      },
      "enforce_admins": true,
      "required_pull_request_reviews": {
        "required_approving_review_count": 2,
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": true
      },
      "restrictions": {
        "users": [],
        "teams": ["admin-team"]
      }
    },
    "develop": {
      "required_status_checks": {
        "strict": false,
        "contexts": [
          "code-quality",
          "security-scan"
        ]
      },
      "enforce_admins": false,
      "required_pull_request_reviews": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": true
      }
    }
  }
}
EOF

# ========================================
# SECURITY CONFIGURATION
# ========================================

echo -e "${CYAN}Step 6: Creating Security Configuration...${NC}"

cat > security-config.yml <<EOF
# Security configuration for OpenPolicyPlatform V5

## Dependabot Configuration
dependabot:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

## CodeQL Analysis
codeql:
  languages: ["python", "javascript", "go"]
  queries: security-extended, security-and-quality

## Secret Scanning
secret-scanning:
  push-protection: true
  alert-retention: 90

## Security Policies
security-policies:
  - name: "Vulnerability Disclosure"
    url: "SECURITY.md"
  - name: "Code of Conduct"
    url: "CODE_OF_CONDUCT.md"
EOF

# ========================================
# DEPLOYMENT CONFIGURATIONS
# ========================================

echo -e "${CYAN}Step 7: Creating Deployment Configurations...${NC}"

# Kubernetes deployment
mkdir -p k8s
cat > k8s/deployment.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openpolicy-platform-v5
  labels:
    app: openpolicy-platform-v5
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openpolicy-platform-v5
  template:
    metadata:
      labels:
        app: openpolicy-platform-v5
    spec:
      containers:
      - name: api-gateway
        image: ghcr.io/ashish-tandon/openpolicy-platform-core/api-gateway:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: openpolicy-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: openpolicy-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: openpolicy-platform-service
spec:
  selector:
    app: openpolicy-platform-v5
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9000
  type: LoadBalancer
EOF

# Helm chart
mkdir -p charts/open-policy-platform
cat > charts/open-policy-platform/Chart.yaml <<EOF
apiVersion: v2
name: open-policy-platform
description: OpenPolicyPlatform V5 - Policy Management Platform
type: application
version: 0.1.0
appVersion: "5.0.0"
keywords:
  - policy
  - governance
  - analytics
  - monitoring
home: https://github.com/ashish-tandon/openpolicy-platform-v5
sources:
  - https://github.com/ashish-tandon/openpolicy-platform-v5
maintainers:
  - name: OpenPolicyPlatform Team
    email: team@openpolicyplatform.org
EOF

# ========================================
# FINAL SETUP SCRIPT
# ========================================

echo -e "${CYAN}Step 8: Creating Final Setup Script...${NC}"

cat > setup-complete.sh <<'EOF'
#!/bin/bash

# Complete setup for OpenPolicyPlatform V5 Multi-Repository CI/CD

echo "🎉 OpenPolicyPlatform V5 Multi-Repository CI/CD Setup Complete!"
echo "================================================================"
echo ""
echo "📋 What was created:"
echo "  ✅ Repository configuration (repositories-config.json)"
echo "  ✅ GitHub Actions workflows (.github/workflows/)"
echo "  ✅ Repository templates (repository-templates/)"
echo "  ✅ Repository creation script (create-repositories.sh)"
echo "  ✅ Branch protection config (branch-protection-config.json)"
echo "  ✅ Security configuration (security-config.yml)"
echo "  ✅ Kubernetes deployment (k8s/)"
echo "  ✅ Helm charts (charts/)"
echo ""
echo "🚀 Next Steps:"
echo "1. Run: ./create-repositories.sh (requires GitHub CLI)"
echo "2. Push code to each repository"
echo "3. Set up repository secrets:"
echo "   - REPO_SYNC_TOKEN"
echo "   - DOCKER_REGISTRY_TOKEN"
echo "   - KUBERNETES_CONFIG"
echo "4. Configure branch protection rules"
echo "5. Enable security scanning"
echo "6. Set up monitoring and alerting"
echo ""
echo "📚 Documentation:"
echo "  - README.md (main repository)"
echo "  - .github/workflows/ (CI/CD workflows)"
echo "  - repository-templates/ (repository structure)"
echo ""
echo "🔒 Security Features:"
echo "  - Automated vulnerability scanning"
echo "  - Secret detection"
echo "  - Code quality checks"
echo "  - Security policy enforcement"
echo ""
echo "🎯 CI/CD Pipeline:"
echo "  - Code quality & testing"
echo "  - Security scanning"
echo "  - Container building"
echo "  - Automated deployment"
echo "  - Repository synchronization"
EOF

chmod +x setup-complete.sh

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ MULTI-REPOSITORY & CI/CD SETUP COMPLETE!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}📋 What was created:${NC}"
echo -e "  - Repository configuration and templates"
echo -e "  - GitHub Actions CI/CD workflows"
echo -e "  - Repository creation scripts"
echo -e "  - Branch protection configuration"
echo -e "  - Security scanning setup"
echo -e "  - Kubernetes deployment configs"
echo -e "  - Helm charts"
echo
echo -e "${CYAN}🚀 To complete setup:${NC}"
echo -e "  1. Install GitHub CLI: brew install gh"
echo -e "  2. Authenticate: gh auth login"
echo -e "  3. Run: ./create-repositories.sh"
echo -e "  4. Push code to repositories"
echo -e "  5. Configure secrets and protection rules"
echo
echo -e "${PURPLE}🎉 Your OpenPolicyPlatform V5 is ready for multi-repository CI/CD!${NC}"
