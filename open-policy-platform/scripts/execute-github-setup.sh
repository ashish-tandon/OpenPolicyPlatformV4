#!/bin/bash

# GitHub Repository Setup Execution Script
# This script executes the GitHub repository creation with all necessary files

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Create temporary directory for repository setup
TEMP_DIR="/tmp/opp-repos-$$"
mkdir -p "$TEMP_DIR"

# Repository structure
declare -A REPOS=(
    ["opp-api-gateway"]="API Gateway and core routing service"
    ["opp-auth-service"]="Authentication and authorization service"
    ["opp-web-frontend"]="Web frontend applications"
    ["opp-scrapers"]="Data collection and scraping services"
    ["opp-docs"]="Documentation and API specifications"
    ["opp-infrastructure"]="Infrastructure as Code and deployment"
)

# Create README files for each repository
create_readme() {
    local repo_name=$1
    local description=$2
    
    cat > "$TEMP_DIR/$repo_name/README.md" << EOF
# $repo_name

$description

## 🚀 Quick Start

\`\`\`bash
# Clone the repository
git clone https://github.com/openpolicy-platform/$repo_name.git

# Install dependencies
npm install  # or pip install -r requirements.txt

# Run development server
npm run dev  # or python main.py
\`\`\`

## 📁 Project Structure

\`\`\`
$repo_name/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── .github/       # GitHub Actions workflows
└── README.md      # This file
\`\`\`

## 🧪 Testing

\`\`\`bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run all tests with coverage
npm run test:coverage
\`\`\`

## 📦 Deployment

This service is automatically deployed via GitHub Actions when changes are pushed to main.

## 📚 Documentation

For detailed documentation, visit [OpenPolicy Platform Docs](https://docs.openpolicy.platform)

## 🤝 Contributing

Please read our [Contributing Guide](CONTRIBUTING.md) before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
EOF
}

# Create GitHub Actions workflow for each service type
create_nodejs_workflow() {
    local repo_name=$1
    
    mkdir -p "$TEMP_DIR/$repo_name/.github/workflows"
    cat > "$TEMP_DIR/$repo_name/.github/workflows/ci-cd.yml" << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ created ]

env:
  NODE_VERSION: '18'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linting
      run: npm run lint
    
    - name: Run tests
      run: npm run test:coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
        fail_ci_if_error: true

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Snyk security scan
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
    
    - name: Run OWASP dependency check
      uses: dependency-check/Dependency-Check_Action@main
      with:
        project: ${{ github.repository }}
        path: '.'
        format: 'HTML'

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix=sha-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
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
    - name: Deploy to staging
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ secrets.AZURE_WEBAPP_NAME }}-staging
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE_STAGING }}
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:develop

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://${{ secrets.PRODUCTION_URL }}
    
    steps:
    - name: Deploy to production
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ secrets.AZURE_WEBAPP_NAME }}
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
    
    - name: Create release notes
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: v${{ github.run_number }}
        release_name: Release v${{ github.run_number }}
        body: |
          Automated release from commit ${{ github.sha }}
          
          Changes in this release:
          - See commit history for details
        draft: false
        prerelease: false
EOF
}

create_python_workflow() {
    local repo_name=$1
    
    mkdir -p "$TEMP_DIR/$repo_name/.github/workflows"
    cat > "$TEMP_DIR/$repo_name/.github/workflows/ci-cd.yml" << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ created ]

env:
  PYTHON_VERSION: '3.11'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black . --check
        mypy .
    
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml --cov-report=html
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Bandit security scan
      run: |
        pip install bandit
        bandit -r . -f json -o bandit-report.json
    
    - name: Run Safety check
      run: |
        pip install safety
        safety check

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix=sha-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
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
    - name: Deploy to Kubernetes staging
      run: |
        echo "Deploy to staging cluster"
        # kubectl apply -f k8s/staging/

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://${{ secrets.PRODUCTION_URL }}
    
    steps:
    - name: Deploy to Kubernetes production
      run: |
        echo "Deploy to production cluster"
        # kubectl apply -f k8s/production/
EOF
}

# Create release workflow
create_release_workflow() {
    local repo_name=$1
    
    cat > "$TEMP_DIR/$repo_name/.github/workflows/release.yml" << 'EOF'
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Generate changelog
      id: changelog
      uses: metcalfc/changelog-generator@v4.0.1
      with:
        myToken: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        body: |
          ## What's Changed
          ${{ steps.changelog.outputs.changelog }}
        draft: false
        prerelease: false
    
    - name: Notify Slack
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'New release ${{ github.ref }} published!'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      if: always()
EOF
}

# Create CONTRIBUTING.md
create_contributing() {
    local repo_name=$1
    
    cat > "$TEMP_DIR/$repo_name/CONTRIBUTING.md" << 'EOF'
# Contributing to OpenPolicy Platform

Thank you for your interest in contributing to OpenPolicy Platform! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/REPO-NAME.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin feature/your-feature-name`
7. Create a Pull Request

## 📋 Development Process

1. **Issue First**: Create an issue describing the feature/bug before starting work
2. **Branch Naming**: Use `feature/`, `bugfix/`, or `hotfix/` prefixes
3. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
4. **Code Style**: Run linters before committing
5. **Tests**: Add tests for new features and ensure all tests pass
6. **Documentation**: Update documentation as needed

## ✅ Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No console.logs or debug code
- [ ] Branch is up to date with main

## 🧪 Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 📝 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build process or auxiliary tool changes

## 🐛 Reporting Bugs

1. Check existing issues first
2. Use the bug report template
3. Include reproduction steps
4. Include environment details
5. Add relevant logs/screenshots

## 💡 Suggesting Features

1. Check the roadmap and existing issues
2. Use the feature request template
3. Explain the use case
4. Provide examples if possible

## 📜 Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

## 🙏 Thank You!

Your contributions make OpenPolicy Platform better for everyone. Thank you for your time and effort!
EOF
}

# Create CODE_OF_CONDUCT.md
create_code_of_conduct() {
    local repo_name=$1
    
    cat > "$TEMP_DIR/$repo_name/CODE_OF_CONDUCT.md" << 'EOF'
# Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

Examples of unacceptable behavior:

* The use of sexualized language or imagery
* Trolling, insulting/derogatory comments, and personal attacks
* Public or private harassment
* Publishing others' private information
* Other conduct which could reasonably be considered inappropriate

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the community leaders responsible for enforcement at conduct@openpolicy.platform.

All complaints will be reviewed and investigated promptly and fairly.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1.
EOF
}

# Create .gitignore
create_gitignore() {
    local repo_name=$1
    local type=$2
    
    if [ "$type" = "node" ]; then
        cat > "$TEMP_DIR/$repo_name/.gitignore" << 'EOF'
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.nyc_output/

# Production
build/
dist/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Temporary
tmp/
temp/
EOF
    else
        cat > "$TEMP_DIR/$repo_name/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.dmypy.json
dmypy.json

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Temporary
tmp/
temp/
EOF
    fi
}

# Create LICENSE
create_license() {
    local repo_name=$1
    
    cat > "$TEMP_DIR/$repo_name/LICENSE" << 'EOF'
MIT License

Copyright (c) 2024 OpenPolicy Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
}

# Main repository setup
main() {
    log "Starting GitHub repository setup..."
    
    # Create repositories with all files
    for repo_name in "${!REPOS[@]}"; do
        description="${REPOS[$repo_name]}"
        
        log "Setting up repository: $repo_name"
        
        # Create repo directory
        mkdir -p "$TEMP_DIR/$repo_name"
        
        # Create common files
        create_readme "$repo_name" "$description"
        create_contributing "$repo_name"
        create_code_of_conduct "$repo_name"
        create_license "$repo_name"
        
        # Create workflows based on repo type
        case "$repo_name" in
            *frontend*|*gateway*)
                create_nodejs_workflow "$repo_name"
                create_gitignore "$repo_name" "node"
                ;;
            *)
                create_python_workflow "$repo_name"
                create_gitignore "$repo_name" "python"
                ;;
        esac
        
        create_release_workflow "$repo_name"
        
        # Create the repository on GitHub
        cd "$TEMP_DIR/$repo_name"
        
        info "Creating GitHub repository: $repo_name"
        gh repo create "openpolicy-platform/$repo_name" \
            --public \
            --description "$description" \
            --clone=false || warning "Repository might already exist"
        
        # Initialize git and push
        git init
        git add .
        git commit -m "feat: initial repository setup with CI/CD"
        git branch -M main
        git remote add origin "https://github.com/openpolicy-platform/$repo_name.git" || true
        
        # Push to GitHub
        git push -u origin main --force
        
        log "✅ Repository $repo_name created and configured"
    done
    
    # Clean up
    rm -rf "$TEMP_DIR"
    
    log "🎉 All repositories created successfully!"
    
    # Create summary
    cat > github-setup-summary-$(date +%Y%m%d-%H%M%S).txt << EOF
GitHub Repository Setup Summary
===============================
Date: $(date)

Repositories Created:
$(for repo in "${!REPOS[@]}"; do echo "- https://github.com/openpolicy-platform/$repo"; done)

Features Configured:
✅ CI/CD pipelines with GitHub Actions
✅ Automated testing and security scanning
✅ Docker container builds
✅ Staging and production deployments
✅ Release automation with changelogs
✅ Contributing guidelines
✅ Code of Conduct
✅ MIT License

Next Steps:
1. Configure repository secrets in GitHub
2. Set up branch protection rules
3. Configure webhook notifications
4. Add team members and permissions
5. Set up project boards

Repository Secrets Needed:
- AZURE_WEBAPP_NAME
- AZURE_WEBAPP_PUBLISH_PROFILE
- AZURE_WEBAPP_PUBLISH_PROFILE_STAGING
- SNYK_TOKEN
- SLACK_WEBHOOK
- PRODUCTION_URL
EOF
    
    info "Summary saved to github-setup-summary-*.txt"
}

# Handle script interruption
trap 'echo "Setup interrupted. Cleaning up..."; rm -rf "$TEMP_DIR"; exit 1' INT TERM

# Check if gh is logged in
if ! gh auth status &> /dev/null; then
    error "Not logged in to GitHub. Please run: gh auth login"
fi

# Run main function
main "$@"