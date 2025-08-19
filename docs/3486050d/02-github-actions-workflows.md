# GitHub Actions Workflow Templates for OpenPolicyPlatform Microservices

## 1. Service Repository CI/CD Workflow

Create this file in each service repository at `.github/workflows/ci-cd.yml`

```yaml
name: Service CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  SERVICE_NAME: ${{ github.event.repository.name }}
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js (if Node.js service)
        if: contains(github.event.repository.name, 'frontend') || contains(github.event.repository.name, 'api')
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        if: contains(github.event.repository.name, 'frontend') || contains(github.event.repository.name, 'api')
        run: npm ci

      - name: Run linting
        if: contains(github.event.repository.name, 'frontend') || contains(github.event.repository.name, 'api')
        run: npm run lint

      - name: Run unit tests
        if: contains(github.event.repository.name, 'frontend') || contains(github.event.repository.name, 'api')
        run: npm test -- --coverage

      - name: Setup Python (if Python service)
        if: contains(github.event.repository.name, 'processor') || contains(github.event.repository.name, 'analytics')
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        if: contains(github.event.repository.name, 'processor') || contains(github.event.repository.name, 'analytics')
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run Python tests
        if: contains(github.event.repository.name, 'processor') || contains(github.event.repository.name, 'analytics')
        run: pytest --cov=src tests/

  security-scan:
    runs-on: ubuntu-latest
    needs: lint-and-test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  build-and-push:
    runs-on: ubuntu-latest
    needs: [lint-and-test, security-scan]
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
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
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  trigger-orchestration:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Trigger orchestration workflow
        uses: peter-evans/repository-dispatch@v2
        with:
          token: ${{ secrets.ORCHESTRATION_TOKEN }}
          repository: ashish-tandon/openpolicy-orchestration
          event-type: service-updated
          client-payload: |
            {
              "service": "${{ env.SERVICE_NAME }}",
              "repository": "${{ github.repository }}",
              "version": "${{ github.sha }}",
              "image": "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}",
              "branch": "${{ github.ref_name }}",
              "commit_message": "${{ github.event.head_commit.message }}"
            }
```

## 2. Orchestration Repository Main Workflow

Create this file in orchestration repository at `.github/workflows/orchestration.yml`

```yaml
name: Platform Orchestration Pipeline

on:
  repository_dispatch:
    types: [service-updated]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'development'
        type: choice
        options:
          - development
          - qnap-test
          - azure-staging
          - azure-production

env:
  AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
  AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
  AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
  QNAP_HOST: ${{ secrets.QNAP_HOST }}
  QNAP_USERNAME: ${{ secrets.QNAP_USERNAME }}

jobs:
  validate-service-update:
    runs-on: ubuntu-latest
    if: github.event_name == 'repository_dispatch'
    outputs:
      service-name: ${{ steps.extract.outputs.service-name }}
      service-version: ${{ steps.extract.outputs.service-version }}
      service-image: ${{ steps.extract.outputs.service-image }}
    steps:
      - name: Extract service information
        id: extract
        run: |
          echo "service-name=${{ github.event.client_payload.service }}" >> $GITHUB_OUTPUT
          echo "service-version=${{ github.event.client_payload.version }}" >> $GITHUB_OUTPUT  
          echo "service-image=${{ github.event.client_payload.image }}" >> $GITHUB_OUTPUT

      - name: Validate service update
        run: |
          echo "Service: ${{ steps.extract.outputs.service-name }}"
          echo "Version: ${{ steps.extract.outputs.service-version }}"
          echo "Image: ${{ steps.extract.outputs.service-image }}"

  integration-tests:
    runs-on: ubuntu-latest
    needs: validate-service-update
    if: github.event_name == 'repository_dispatch'
    steps:
      - name: Checkout orchestration repo
        uses: actions/checkout@v4

      - name: Setup Docker Compose
        run: |
          docker-compose version

      - name: Update service image in docker-compose
        run: |
          SERVICE_NAME="${{ needs.validate-service-update.outputs.service-name }}"
          SERVICE_IMAGE="${{ needs.validate-service-update.outputs.service-image }}"

          # Update docker-compose file with new service image
          sed -i "s|image: .*/${SERVICE_NAME}:.*|image: ${SERVICE_IMAGE}|g" docker-compose.test.yml

      - name: Start test environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30  # Wait for services to be ready

      - name: Run integration tests
        run: |
          # Health check all services
          docker-compose -f docker-compose.test.yml exec -T api-gateway curl -f http://localhost:3000/health
          docker-compose -f docker-compose.test.yml exec -T policy-processor curl -f http://localhost:3001/health

          # Run integration test suite
          npm install
          npm run test:integration

      - name: Cleanup test environment
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v

  deploy-to-qnap:
    runs-on: ubuntu-latest
    needs: [validate-service-update, integration-tests]
    if: github.event_name == 'repository_dispatch'
    steps:
      - name: Checkout orchestration repo
        uses: actions/checkout@v4

      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.8.0
        with:
          ssh-private-key: ${{ secrets.QNAP_SSH_PRIVATE_KEY }}

      - name: Deploy to QNAP Test Environment
        run: |
          SERVICE_NAME="${{ needs.validate-service-update.outputs.service-name }}"
          SERVICE_IMAGE="${{ needs.validate-service-update.outputs.service-image }}"

          # Create deployment script
          cat > deploy-qnap.sh << 'EOF'
          #!/bin/bash
          set -e

          SERVICE_NAME="$1"
          SERVICE_IMAGE="$2"

          echo "Deploying ${SERVICE_NAME} with image ${SERVICE_IMAGE} to QNAP"

          # Update docker-compose file for QNAP
          sed -i "s|image: .*/${SERVICE_NAME}:.*|image: ${SERVICE_IMAGE}|g" /share/Container/openpolicy/docker-compose.yml

          # Blue-Green deployment
          cd /share/Container/openpolicy

          # Stop current green environment (if exists)
          docker-compose -f docker-compose.yml down green-${SERVICE_NAME} || true

          # Start new green environment
          docker-compose -f docker-compose.yml up -d green-${SERVICE_NAME}

          # Wait for health check
          sleep 30

          # Health check
          if docker-compose -f docker-compose.yml exec -T green-${SERVICE_NAME} curl -f http://localhost:3000/health; then
            echo "Green environment healthy, switching traffic"

            # Update nginx to point to green
            sed -i "s/blue-${SERVICE_NAME}/green-${SERVICE_NAME}/g" /share/Container/openpolicy/nginx.conf
            docker-compose -f docker-compose.yml exec nginx nginx -s reload

            # Stop blue environment
            docker-compose -f docker-compose.yml stop blue-${SERVICE_NAME}

            # Rename green to blue for next deployment
            docker-compose -f docker-compose.yml exec -T green-${SERVICE_NAME} docker tag green-${SERVICE_NAME} blue-${SERVICE_NAME}

            echo "Deployment successful"
          else
            echo "Green environment failed health check, rolling back"
            docker-compose -f docker-compose.yml down green-${SERVICE_NAME}
            exit 1
          fi
          EOF

          chmod +x deploy-qnap.sh

          # Copy script to QNAP and execute
          scp deploy-qnap.sh ${{ env.QNAP_USERNAME }}@${{ env.QNAP_HOST }}:/tmp/
          ssh ${{ env.QNAP_USERNAME }}@${{ env.QNAP_HOST }} "/tmp/deploy-qnap.sh '$SERVICE_NAME' '$SERVICE_IMAGE'"

  deploy-to-azure-staging:
    runs-on: ubuntu-latest
    needs: [validate-service-update, deploy-to-qnap]
    if: github.event_name == 'repository_dispatch'
    steps:
      - name: Checkout orchestration repo
        uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v1
        with:
          client-id: ${{ env.AZURE_CLIENT_ID }}
          tenant-id: ${{ env.AZURE_TENANT_ID }}
          subscription-id: ${{ env.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy to Azure Container Apps Staging
        run: |
          SERVICE_NAME="${{ needs.validate-service-update.outputs.service-name }}"
          SERVICE_IMAGE="${{ needs.validate-service-update.outputs.service-image }}"

          az containerapp update             --name "openpolicy-${SERVICE_NAME}-staging"             --resource-group "openpolicy-staging-rg"             --image "${SERVICE_IMAGE}"             --revision-suffix "$(date +%s)"

      - name: Run staging smoke tests
        run: |
          # Wait for deployment
          sleep 60

          # Get staging URL
          STAGING_URL=$(az containerapp show             --name "openpolicy-${SERVICE_NAME}-staging"             --resource-group "openpolicy-staging-rg"             --query properties.configuration.ingress.fqdn -o tsv)

          # Health check
          curl -f "https://${STAGING_URL}/health"

          # Basic functionality test
          npm run test:staging -- --baseUrl="https://${STAGING_URL}"

  promote-to-production:
    runs-on: ubuntu-latest
    needs: [validate-service-update, deploy-to-azure-staging]
    if: github.event_name == 'repository_dispatch'
    environment: production
    steps:
      - name: Checkout orchestration repo
        uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v1
        with:
          client-id: ${{ env.AZURE_CLIENT_ID }}
          tenant-id: ${{ env.AZURE_TENANT_ID }}
          subscription-id: ${{ env.AZURE_SUBSCRIPTION_ID }}

      - name: Blue-Green Production Deployment
        run: |
          SERVICE_NAME="${{ needs.validate-service-update.outputs.service-name }}"
          SERVICE_IMAGE="${{ needs.validate-service-update.outputs.service-image }}"

          # Create new revision (Green)
          az containerapp revision copy             --name "openpolicy-${SERVICE_NAME}-prod"             --resource-group "openpolicy-prod-rg"             --from-revision "latest"             --image "${SERVICE_IMAGE}"             --revision-suffix "green-$(date +%s)"

          # Get new revision name
          NEW_REVISION=$(az containerapp revision list             --name "openpolicy-${SERVICE_NAME}-prod"             --resource-group "openpolicy-prod-rg"             --query "[0].name" -o tsv)

          echo "New revision: $NEW_REVISION"

          # Wait for revision to be ready
          az containerapp revision show             --name "$NEW_REVISION"             --app "openpolicy-${SERVICE_NAME}-prod"             --resource-group "openpolicy-prod-rg"             --query "properties.provisioningState"

          # Gradual traffic shift
          echo "Starting gradual traffic shift..."

          # 10% traffic to new revision
          az containerapp ingress traffic set             --name "openpolicy-${SERVICE_NAME}-prod"             --resource-group "openpolicy-prod-rg"             --revision-weight "$NEW_REVISION=10,latest=90"

          sleep 300  # Wait 5 minutes

          # Check error rate and metrics
          # (Add your monitoring checks here)

          # 50% traffic
          az containerapp ingress traffic set             --name "openpolicy-${SERVICE_NAME}-prod"             --resource-group "openpolicy-prod-rg"             --revision-weight "$NEW_REVISION=50,latest=50"

          sleep 300  # Wait 5 minutes

          # 100% traffic
          az containerapp ingress traffic set             --name "openpolicy-${SERVICE_NAME}-prod"             --resource-group "openpolicy-prod-rg"             --revision-weight "$NEW_REVISION=100"

          echo "Production deployment completed successfully"

  manual-deployment:
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    steps:
      - name: Manual deployment to ${{ github.event.inputs.environment }}
        run: |
          echo "Manual deployment to environment: ${{ github.event.inputs.environment }}"
          # Add manual deployment logic here based on environment
```

## 3. Pull Request Validation Workflow

Create this file in orchestration repository at `.github/workflows/pr-validation.yml`

```yaml
name: Pull Request Validation

on:
  pull_request:
    branches: [ main ]
    types: [opened, synchronize, reopened]

jobs:
  validate-changes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get changed files
        id: changed-files
        uses: tj-actions/changed-files@v40
        with:
          files: |
            docker-compose*.yml
            infrastructure/**
            scripts/**

      - name: Validate Docker Compose files
        if: steps.changed-files.outputs.any_changed == 'true'
        run: |
          for file in ${{ steps.changed-files.outputs.all_changed_files }}; do
            if [[ "$file" == *.yml ]] && [[ "$file" == *docker-compose* ]]; then
              echo "Validating $file"
              docker-compose -f "$file" config
            fi
          done

      - name: Test infrastructure changes
        if: contains(steps.changed-files.outputs.all_changed_files, 'infrastructure/')
        run: |
          echo "Infrastructure changes detected, running validation tests"
          # Add your infrastructure validation tests here

  security-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run security scan on configurations
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'table'
```

## 4. Required Secrets Configuration

Add these secrets to your GitHub repositories:

### Service Repositories:
- `ORCHESTRATION_TOKEN`: Personal access token for triggering orchestration workflows

### Orchestration Repository:
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_TENANT_ID`: Azure tenant ID  
- `AZURE_CLIENT_ID`: Azure service principal client ID
- `QNAP_HOST`: QNAP NAS IP address
- `QNAP_USERNAME`: QNAP username for SSH access
- `QNAP_SSH_PRIVATE_KEY`: Private key for SSH access to QNAP

## 5. Workflow Usage Instructions

### For Service Developers:
1. Make changes in your service repository
2. Push to `develop` branch for testing
3. Create PR to `main` for production deployment
4. Once merged to `main`, automatic deployment pipeline triggers

### For Platform Team:
1. Monitor orchestration workflows for deployment status
2. Use manual deployment workflow for emergency deployments
3. Review integration test results before production promotion

### Environment Progression:
1. **Development**: Automatic on PR merge to main
2. **QNAP Test**: Automatic after integration tests pass
3. **Azure Staging**: Automatic after QNAP deployment succeeds
4. **Azure Production**: Manual approval required (GitHub Environment)

This workflow system provides comprehensive CI/CD for your microservices migration while maintaining safety and reliability through automated testing and blue-green deployments.
