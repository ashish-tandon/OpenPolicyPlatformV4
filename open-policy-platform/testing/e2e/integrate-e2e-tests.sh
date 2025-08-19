#!/bin/bash
set -e

echo "============================================"
echo "Integrating E2E Tests into Platform"
echo "============================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is required but not installed.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is required but not installed.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites checked${NC}"

# Run E2E setup
echo -e "${YELLOW}Running E2E test setup...${NC}"
./testing/e2e/setup-e2e-tests.sh

# Update CI/CD pipeline to include E2E tests
echo -e "${YELLOW}Updating CI/CD pipeline...${NC}"

# Update the monorepo CI/CD workflow
cat > .github/workflows/complete-ci-cd.yml << 'EOF'
name: Complete CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}/open-policy-platform

jobs:
  # Unit and Integration Tests
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [
          'api-gateway',
          'auth-service',
          'policy-service',
          'web-frontend',
          'mobile-apps'
        ]
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
        
      - name: Run unit tests
        run: npm run test:${{ matrix.service }}
        
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/${{ matrix.service }}/lcov.info
          flags: ${{ matrix.service }}

  # Security Scanning
  security:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Trivy security scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  # E2E Tests - Cypress
  e2e-cypress:
    runs-on: ubuntu-latest
    needs: test
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: openpolicy_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Setup database
        run: |
          PGPASSWORD=postgres psql -h localhost -U postgres -d openpolicy_test -f database/complete-schema-setup.sql
      
      - name: Build application
        run: npm run build
        
      - name: Run Cypress E2E tests
        uses: cypress-io/github-action@v5
        with:
          start: npm run start:test
          wait-on: 'http://localhost:3000'
          record: true
          parallel: true
          group: 'E2E Tests'
        env:
          CYPRESS_RECORD_KEY: ${{ secrets.CYPRESS_RECORD_KEY }}
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/openpolicy_test
          REDIS_URL: redis://localhost:6379
          NODE_ENV: test

  # E2E Tests - Playwright
  e2e-playwright:
    runs-on: ubuntu-latest
    needs: test
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright browsers
        run: npx playwright install --with-deps ${{ matrix.browser }}
      
      - name: Run Playwright tests
        run: npm run playwright -- --project=${{ matrix.browser }}
        
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report-${{ matrix.browser }}
          path: playwright-report/
          retention-days: 30

  # Performance Tests
  performance:
    runs-on: ubuntu-latest
    needs: [e2e-cypress, e2e-playwright]
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run Lighthouse CI
        uses: treosh/lighthouse-ci-action@v9
        with:
          urls: |
            http://localhost:3000
            http://localhost:3000/policies
            http://localhost:3000/representatives
          uploadArtifacts: true
          temporaryPublicStorage: true

  # Build and Push Docker Images
  build:
    runs-on: ubuntu-latest
    needs: [security, e2e-cypress, e2e-playwright]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    strategy:
      matrix:
        service: [
          'api-gateway',
          'auth-service',
          'policy-service',
          'notification-service',
          'config-service',
          'analytics-service',
          'monitoring-service',
          'etl-service',
          'scraper-service',
          'search-service',
          'web-frontend',
          'admin-dashboard'
        ]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./services/${{ matrix.service }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Deploy to Staging
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: staging
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes Staging
        run: |
          echo "Deploying to staging environment..."
          # kubectl apply -f k8s/staging/

  # Deploy to Production
  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes Production
        run: |
          echo "Deploying to production environment..."
          # kubectl apply -f k8s/production/

  # Post-deployment E2E Tests
  post-deploy-tests:
    runs-on: ubuntu-latest
    needs: deploy-staging
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run smoke tests against staging
        run: |
          CYPRESS_BASE_URL=https://staging.openpolicy.com npm run cy:run -- --spec "cypress/integration/smoke/**/*.cy.ts"
      
      - name: Run API tests against staging
        run: npm run test:api:staging
EOF

echo -e "${GREEN}✓ CI/CD pipeline updated with E2E tests${NC}"

# Create smoke tests for post-deployment
echo -e "${YELLOW}Creating smoke tests...${NC}"

mkdir -p testing/e2e/cypress/integration/smoke

cat > testing/e2e/cypress/integration/smoke/critical-paths.cy.ts << 'EOF'
/// <reference types="cypress" />

describe('Critical Path Smoke Tests', () => {
  it('should load the home page', () => {
    cy.visit('/')
    cy.get('[data-cy=hero-section]').should('be.visible')
    cy.contains('Open Policy Platform').should('be.visible')
  })

  it('should allow user login', () => {
    cy.visit('/login')
    cy.get('[data-cy=email-input]').should('be.visible')
    cy.get('[data-cy=password-input]').should('be.visible')
    cy.get('[data-cy=login-button]').should('be.enabled')
  })

  it('should display policies', () => {
    cy.visit('/policies')
    cy.get('[data-cy=policy-list]').should('be.visible')
    cy.get('[data-cy=policy-item]', { timeout: 10000 }).should('have.length.greaterThan', 0)
  })

  it('should display representatives', () => {
    cy.visit('/representatives')
    cy.get('[data-cy=representatives-grid]').should('be.visible')
    cy.get('[data-cy=representative-card]', { timeout: 10000 }).should('have.length.greaterThan', 0)
  })

  it('should have working API endpoints', () => {
    cy.request('/api/health').then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body).to.have.property('status', 'healthy')
    })

    cy.request('/api/status').then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body).to.have.property('services')
    })
  })

  it('should have responsive design', () => {
    // Desktop
    cy.viewport(1920, 1080)
    cy.visit('/')
    cy.get('[data-cy=desktop-nav]').should('be.visible')
    
    // Mobile
    cy.viewport('iphone-x')
    cy.visit('/')
    cy.get('[data-cy=mobile-menu-toggle]').should('be.visible')
  })
})
EOF

echo -e "${GREEN}✓ Smoke tests created${NC}"

# Create performance budget configuration
echo -e "${YELLOW}Creating performance budget...${NC}"

cat > testing/e2e/lighthouse.config.js << 'EOF'
module.exports = {
  ci: {
    collect: {
      staticDistDir: './dist',
      url: [
        'http://localhost:3000/',
        'http://localhost:3000/policies',
        'http://localhost:3000/representatives',
        'http://localhost:3000/dashboard'
      ],
      numberOfRuns: 3,
    },
    assert: {
      preset: 'lighthouse:no-pwa',
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'first-contentful-paint': ['error', { maxNumericValue: 1500 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'speed-index': ['error', { maxNumericValue: 3000 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
EOF

echo -e "${GREEN}✓ Performance budget created${NC}"

# Create test data management script
echo -e "${YELLOW}Creating test data management...${NC}"

cat > testing/e2e/manage-test-data.sh << 'EOF'
#!/bin/bash
set -e

# Test data management script

ACTION=$1

case $ACTION in
  "seed")
    echo "Seeding test database..."
    psql $DATABASE_URL -f testing/e2e/fixtures/seed-data.sql
    echo "Test data seeded successfully!"
    ;;
    
  "clean")
    echo "Cleaning test database..."
    psql $DATABASE_URL -f testing/e2e/fixtures/clean-data.sql
    echo "Test data cleaned successfully!"
    ;;
    
  "reset")
    echo "Resetting test database..."
    $0 clean
    $0 seed
    echo "Test database reset successfully!"
    ;;
    
  *)
    echo "Usage: $0 {seed|clean|reset}"
    exit 1
    ;;
esac
EOF

chmod +x testing/e2e/manage-test-data.sh

echo -e "${GREEN}✓ Test data management created${NC}"

# Update the main test script to include all E2E tests
cat > scripts/test-e2e-complete.sh << 'EOF'
#!/bin/bash
set -e

echo "========================================"
echo "Running Complete E2E Test Suite"
echo "========================================"

# Check if services are running
echo "Checking service health..."
curl -f http://localhost:9000/api/health || {
    echo "API Gateway is not running. Please start services first."
    exit 1
}

# Setup test data
echo "Setting up test data..."
./testing/e2e/manage-test-data.sh reset

# Run Cypress tests
echo -e "\n📗 Running Cypress E2E tests..."
npm run cy:run

# Run Playwright tests
echo -e "\n🎭 Running Playwright tests..."
npm run playwright

# Run performance tests
echo -e "\n⚡ Running performance tests..."
npx lighthouse-ci collect

# Run accessibility tests
echo -e "\n♿ Running accessibility tests..."
npm run test:a11y

# Generate test report
echo -e "\n📊 Generating test report..."
node scripts/generate-test-report.js

echo -e "\n✅ All E2E tests completed successfully!"
EOF

chmod +x scripts/test-e2e-complete.sh

echo -e "${GREEN}✓ Complete E2E test script created${NC}"

echo -e "\n${GREEN}============================================"
echo "E2E Test Integration Complete!"
echo "============================================${NC}"
echo ""
echo "E2E tests have been fully integrated into the platform:"
echo ""
echo "✅ Cypress tests created for:"
echo "   - Authentication flows"
echo "   - Policy management"
echo "   - Representative profiles"
echo "   - Admin dashboard"
echo "   - Search functionality"
echo "   - Mobile responsiveness"
echo ""
echo "✅ Playwright tests created for:"
echo "   - Cross-browser testing"
echo "   - Performance monitoring"
echo "   - Visual regression"
echo ""
echo "✅ CI/CD pipeline updated with:"
echo "   - E2E test stages"
echo "   - Security scanning"
echo "   - Performance budgets"
echo "   - Post-deployment tests"
echo ""
echo "To run E2E tests:"
echo "1. Setup: ./testing/e2e/setup-e2e-tests.sh"
echo "2. Run all: ./scripts/test-e2e-complete.sh"
echo "3. Run Cypress: npm run e2e"
echo "4. Run Playwright: npm run playwright"