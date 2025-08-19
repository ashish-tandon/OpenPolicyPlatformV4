#!/bin/bash

# GitHub Repository Setup Script for OpenPolicyPlatform V4
# This script creates all 6 repositories with proper CI/CD pipelines

set -e

# Configuration
GITHUB_ORG="openpolicy-platform"  # Change to your organization
GITHUB_USER=""  # Set if using personal account instead of org
PROJECT_PREFIX="opp"

# Repository definitions
declare -A REPOS=(
    ["core-services"]="Core API services (auth, policy, notification, config)"
    ["business-services"]="Business logic services (analytics, monitoring, ETL, search)"
    ["data-services"]="Data processing services (scraper, representatives, committees)"
    ["web-frontend"]="Web frontend and admin dashboard"
    ["mobile-apps"]="Mobile applications (iOS and Android)"
    ["infrastructure"]="Infrastructure as Code, Helm charts, and deployment scripts"
)

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
    
    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        error "GitHub CLI not found. Please install: https://cli.github.com/"
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        error "Not authenticated with GitHub. Please run: gh auth login"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        error "Git not found. Please install git"
    fi
    
    log "✅ Prerequisites check passed"
}

# Create repository
create_repository() {
    local repo_name=$1
    local description=$2
    local visibility=${3:-"private"}  # Default to private
    
    log "Creating repository: $repo_name"
    
    if [ -n "$GITHUB_ORG" ]; then
        gh repo create "$GITHUB_ORG/$repo_name" \
            --description "$description" \
            --$visibility \
            --enable-issues \
            --enable-wiki \
            || warning "Repository $repo_name might already exist"
    else
        gh repo create "$repo_name" \
            --description "$description" \
            --$visibility \
            --enable-issues \
            --enable-wiki \
            || warning "Repository $repo_name might already exist"
    fi
}

# Create branch protection rules
setup_branch_protection() {
    local repo=$1
    
    log "Setting up branch protection for $repo"
    
    # Main branch protection
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        "/repos/${GITHUB_ORG:-$GITHUB_USER}/$repo/branches/main/protection" \
        -f required_status_checks='{"strict":true,"contexts":["build","test","security-scan"]}' \
        -f enforce_admins=false \
        -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
        -f restrictions=null \
        -f allow_force_pushes=false \
        -f allow_deletions=false
}

# Create secrets for repository
create_repository_secrets() {
    local repo=$1
    
    log "Creating secrets for $repo"
    
    # Docker Hub credentials
    gh secret set DOCKER_USERNAME -b"${DOCKER_USERNAME}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
    gh secret set DOCKER_PASSWORD -b"${DOCKER_PASSWORD}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
    
    # Azure credentials
    gh secret set AZURE_CREDENTIALS -b"${AZURE_CREDENTIALS}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
    gh secret set ACR_USERNAME -b"${ACR_USERNAME}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
    gh secret set ACR_PASSWORD -b"${ACR_PASSWORD}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
    
    # Kubernetes config
    gh secret set KUBE_CONFIG -b"${KUBE_CONFIG}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
    
    # Monitoring
    gh secret set SLACK_WEBHOOK -b"${SLACK_WEBHOOK}" -R"${GITHUB_ORG:-$GITHUB_USER}/$repo" || true
}

# Create GitHub Actions workflow for services
create_service_workflow() {
    local repo=$1
    local workflow_file=".github/workflows/ci-cd.yml"
    
    cat > $workflow_file << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ created ]

env:
  REGISTRY: docker.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [auth-service, policy-service, notification-service, config-service]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        cd services/${{ matrix.service }}
        pip install -r requirements.txt
        pip install pytest pytest-cov black flake8 bandit
    
    - name: Lint code
      run: |
        cd services/${{ matrix.service }}
        black --check .
        flake8 .
    
    - name: Security scan
      run: |
        cd services/${{ matrix.service }}
        bandit -r . -f json -o bandit-report.json
    
    - name: Run tests
      run: |
        cd services/${{ matrix.service }}
        pytest --cov=. --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./services/${{ matrix.service }}/coverage.xml
        flags: ${{ matrix.service }}

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [auth-service, policy-service, notification-service, config-service]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./services/${{ matrix.service }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Set up Kubectl
      uses: azure/setup-kubectl@v3
    
    - name: Deploy to Staging
      run: |
        kubectl apply -f k8s/staging/ --namespace=staging
        kubectl rollout status deployment -n staging

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy to Production
      run: |
        helm upgrade --install ${{ github.event.repository.name }} \
          ./charts/${{ github.event.repository.name }} \
          --namespace production \
          --values ./charts/${{ github.event.repository.name }}/values-prod.yaml \
          --set image.tag=${{ github.event.release.tag_name }}
    
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      if: always()
EOF
}

# Create GitHub Actions workflow for frontend
create_frontend_workflow() {
    local repo=$1
    local workflow_file=".github/workflows/ci-cd.yml"
    
    cat > $workflow_file << 'EOF'
name: Frontend CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Lint
      run: npm run lint
    
    - name: Type check
      run: npm run type-check
    
    - name: Test
      run: npm run test:ci
    
    - name: Build
      run: npm run build

  deploy-preview:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-args: '--prod'
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID}}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID}}

  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and Deploy to Azure Static Web Apps
      uses: Azure/static-web-apps-deploy@v1
      with:
        azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
        repo_token: ${{ secrets.GITHUB_TOKEN }}
        action: "upload"
        app_location: "/"
        output_location: "dist"
EOF
}

# Initialize repository with basic structure
initialize_repository() {
    local repo=$1
    local repo_type=$2
    
    log "Initializing repository structure for $repo"
    
    # Clone repository
    if [ -n "$GITHUB_ORG" ]; then
        git clone "https://github.com/$GITHUB_ORG/$repo.git" temp-$repo
    else
        git clone "https://github.com/$GITHUB_USER/$repo.git" temp-$repo
    fi
    
    cd temp-$repo
    
    # Create basic structure
    mkdir -p .github/workflows
    
    # Add README
    cat > README.md << EOF
# $repo

${REPOS[$repo_type]}

## Overview

This repository is part of the OpenPolicyPlatform V4 microservices architecture.

## Getting Started

\`\`\`bash
# Clone the repository
git clone https://github.com/${GITHUB_ORG:-$GITHUB_USER}/$repo.git
cd $repo

# Install dependencies
make install

# Run locally
make run

# Run tests
make test
\`\`\`

## CI/CD

This repository uses GitHub Actions for continuous integration and deployment.

- **Branches**:
  - \`main\`: Production branch
  - \`develop\`: Development branch
  - Feature branches: \`feature/*\`

- **Deployment**:
  - Pull requests: Preview deployments
  - \`develop\`: Staging deployment
  - \`main\`: Production deployment

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
EOF

    # Add CONTRIBUTING.md
    cat > CONTRIBUTING.md << 'EOF'
# Contributing to OpenPolicyPlatform

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Add tests for new functionality
4. Ensure no decrease in code coverage
5. Request review from maintainers

## Coding Standards

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write meaningful commit messages
- Add appropriate comments and documentation
EOF

    # Add appropriate workflow
    case $repo_type in
        "core-services"|"business-services"|"data-services")
            create_service_workflow $repo
            ;;
        "web-frontend"|"mobile-apps")
            create_frontend_workflow $repo
            ;;
        "infrastructure")
            # Infrastructure has different workflow
            ;;
    esac
    
    # Commit and push
    git add .
    git commit -m "Initial repository setup with CI/CD pipeline"
    git push origin main
    
    cd ..
    rm -rf temp-$repo
}

# Main execution
main() {
    echo "🚀 GitHub Repository Setup for OpenPolicyPlatform V4"
    echo "=================================================="
    echo ""
    echo "This script will create the following repositories:"
    for repo in "${!REPOS[@]}"; do
        echo "- ${PROJECT_PREFIX}-${repo}: ${REPOS[$repo]}"
    done
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    check_prerequisites
    
    # Create repositories
    for repo_type in "${!REPOS[@]}"; do
        repo_name="${PROJECT_PREFIX}-${repo_type}"
        create_repository "$repo_name" "${REPOS[$repo_type]}"
        setup_branch_protection "$repo_name"
        create_repository_secrets "$repo_name"
        initialize_repository "$repo_name" "$repo_type"
    done
    
    log "✅ All repositories created successfully!"
    
    # Create summary
    cat > github-setup-summary.txt << EOF
GitHub Repository Setup Summary
==============================
Date: $(date)
Organization: ${GITHUB_ORG:-$GITHUB_USER}

Repositories Created:
EOF
    
    for repo_type in "${!REPOS[@]}"; do
        echo "- https://github.com/${GITHUB_ORG:-$GITHUB_USER}/${PROJECT_PREFIX}-${repo_type}" >> github-setup-summary.txt
    done
    
    cat >> github-setup-summary.txt << EOF

Next Steps:
1. Add team members to repositories
2. Configure webhook integrations
3. Set up project boards
4. Configure deployment environments
5. Add status badges to READMEs

CI/CD Features Configured:
- Automated testing on all branches
- Security scanning with Bandit
- Code coverage reporting
- Docker image building and pushing
- Staging deployment on develop branch
- Production deployment on releases
- Slack notifications
- Branch protection rules

Required Secrets to Configure:
- DOCKER_USERNAME
- DOCKER_PASSWORD
- AZURE_CREDENTIALS
- ACR_USERNAME
- ACR_PASSWORD
- KUBE_CONFIG
- SLACK_WEBHOOK
- VERCEL_TOKEN (for frontend)
- AZURE_STATIC_WEB_APPS_API_TOKEN (for frontend)
EOF
    
    echo ""
    echo "📄 See github-setup-summary.txt for details"
}

# Run main function
main "$@"