#!/bin/bash
set -e

echo "==================================="
echo "Setting up E2E Testing Framework"
echo "==================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing E2E testing dependencies...${NC}"

# Install Cypress
npm install --save-dev cypress @cypress/react @cypress/webpack-dev-server
npm install --save-dev @testing-library/cypress cypress-axe

# Install Playwright
npm install --save-dev @playwright/test

# Install additional testing utilities
npm install --save-dev cross-env start-server-and-test wait-on

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create Cypress fixtures
echo -e "${YELLOW}Creating test fixtures...${NC}"

mkdir -p testing/e2e/cypress/fixtures

# Create session fixture
cat > testing/e2e/cypress/fixtures/session.json << 'EOF'
{
  "user": {
    "id": "test-user-123",
    "email": "test@openpolicy.local",
    "name": "Test User",
    "role": "user"
  },
  "token": "test-jwt-token",
  "expiresAt": "2025-12-31T23:59:59Z"
}
EOF

# Create policies fixture
cat > testing/e2e/cypress/fixtures/policies.json << 'EOF'
{
  "data": [
    {
      "id": "policy-1",
      "title": "Healthcare Reform Act",
      "description": "Comprehensive healthcare reform legislation",
      "status": "active",
      "sponsor": "Rep. John Smith",
      "votesFor": 250,
      "votesAgainst": 185
    },
    {
      "id": "policy-2",
      "title": "Education Funding Bill",
      "description": "Increase funding for public education",
      "status": "passed",
      "sponsor": "Sen. Jane Doe",
      "votesFor": 315,
      "votesAgainst": 120
    }
  ],
  "total": 2,
  "page": 1,
  "pageSize": 10
}
EOF

# Create representatives fixture
cat > testing/e2e/cypress/fixtures/representatives.json << 'EOF'
{
  "data": [
    {
      "id": "rep-1",
      "name": "John Smith",
      "party": "Liberal",
      "riding": "Toronto Centre",
      "province": "ON",
      "photo": "/images/representatives/john-smith.jpg",
      "email": "john.smith@parliament.ca"
    },
    {
      "id": "rep-2",
      "name": "Jane Doe",
      "party": "Conservative",
      "riding": "Calgary West",
      "province": "AB",
      "photo": "/images/representatives/jane-doe.jpg",
      "email": "jane.doe@parliament.ca"
    }
  ],
  "total": 2,
  "page": 1,
  "pageSize": 10
}
EOF

echo -e "${GREEN}✓ Test fixtures created${NC}"

# Update package.json scripts
echo -e "${YELLOW}Updating package.json scripts...${NC}"

# Add E2E test scripts
npm pkg set scripts.cy:open="cypress open"
npm pkg set scripts.cy:run="cypress run"
npm pkg set scripts.e2e="start-server-and-test dev http://localhost:3000 cy:run"
npm pkg set scripts.e2e:headed="start-server-and-test dev http://localhost:3000 cy:open"
npm pkg set scripts.playwright="playwright test"
npm pkg set scripts.playwright:ui="playwright test --ui"
npm pkg set scripts.playwright:debug="playwright test --debug"
npm pkg set scripts.test:e2e="npm run e2e && npm run playwright"

echo -e "${GREEN}✓ Package.json scripts updated${NC}"

# Create test database setup script
echo -e "${YELLOW}Creating test database setup...${NC}"

cat > testing/e2e/setup-test-db.sh << 'EOF'
#!/bin/bash
# Setup test database with sample data

echo "Setting up test database..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "PostgreSQL is not running. Please start it first."
    exit 1
fi

# Create test database
createdb -h localhost -p 5432 openpolicy_e2e_test || true

# Run migrations
psql -h localhost -p 5432 -d openpolicy_e2e_test -f database/complete-schema-setup.sql

# Insert test data
psql -h localhost -p 5432 -d openpolicy_e2e_test << SQL
-- Insert test users
INSERT INTO users (email, password, role, is_active) VALUES
  ('test@openpolicy.local', '$2b$10$YourHashedPassword', 'user', true),
  ('admin@openpolicy.local', '$2b$10$YourHashedPassword', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- Insert test policies
INSERT INTO bills (title, description, status, sponsor_id) VALUES
  ('Test Healthcare Bill', 'A test bill for healthcare', 'active', 1),
  ('Test Education Bill', 'A test bill for education', 'passed', 1)
ON CONFLICT DO NOTHING;

-- Insert test representatives
INSERT INTO politicians (name, party, email, constituency) VALUES
  ('Test Representative 1', 'Liberal', 'rep1@test.com', 'Test Riding 1'),
  ('Test Representative 2', 'Conservative', 'rep2@test.com', 'Test Riding 2')
ON CONFLICT DO NOTHING;
SQL

echo "Test database setup complete!"
EOF

chmod +x testing/e2e/setup-test-db.sh

echo -e "${GREEN}✓ Test database setup created${NC}"

# Create GitHub Actions workflow for E2E tests
echo -e "${YELLOW}Creating GitHub Actions E2E workflow...${NC}"

mkdir -p .github/workflows

cat > .github/workflows/e2e-tests.yml << 'EOF'
name: E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  cypress-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: openpolicy_e2e_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Setup test database
        run: |
          PGPASSWORD=postgres psql -h localhost -U postgres -d openpolicy_e2e_test -f database/complete-schema-setup.sql
        
      - name: Run Cypress tests
        uses: cypress-io/github-action@v5
        with:
          build: npm run build
          start: npm run start
          wait-on: 'http://localhost:3000'
          record: true
        env:
          CYPRESS_RECORD_KEY: ${{ secrets.CYPRESS_RECORD_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/openpolicy_e2e_test

  playwright-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
      
      - name: Run Playwright tests
        run: npm run playwright
        
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
EOF

echo -e "${GREEN}✓ GitHub Actions workflow created${NC}"

# Create VS Code settings for E2E tests
echo -e "${YELLOW}Creating VS Code settings...${NC}"

mkdir -p .vscode

cat > .vscode/e2e-testing.json << 'EOF'
{
  "cypress.integration.folder": "testing/e2e/cypress/integration",
  "cypress.fixture.folder": "testing/e2e/cypress/fixtures",
  "cypress.support.folder": "testing/e2e/cypress/support",
  "playwright.reuseBrowser": true,
  "playwright.showTrace": true
}
EOF

echo -e "${GREEN}✓ VS Code settings created${NC}"

# Create test runner script
cat > testing/e2e/run-all-tests.sh << 'EOF'
#!/bin/bash
set -e

echo "================================"
echo "Running All E2E Tests"
echo "================================"

# Setup test database
echo "Setting up test database..."
./testing/e2e/setup-test-db.sh

# Run Cypress tests
echo -e "\n📗 Running Cypress tests..."
npm run cy:run

# Run Playwright tests
echo -e "\n🎭 Running Playwright tests..."
npm run playwright

echo -e "\n✅ All E2E tests completed!"

# Generate combined report
if [ -d "cypress/results" ] && [ -d "playwright-report" ]; then
    echo -e "\n📊 Test Reports:"
    echo "  - Cypress: cypress/results/index.html"
    echo "  - Playwright: playwright-report/index.html"
fi
EOF

chmod +x testing/e2e/run-all-tests.sh

echo -e "${GREEN}✓ Test runner script created${NC}"

# Create README for E2E tests
cat > testing/e2e/README.md << 'EOF'
# End-to-End Testing

This directory contains comprehensive E2E tests using both Cypress and Playwright.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Setup test database:
   ```bash
   ./testing/e2e/setup-test-db.sh
   ```

## Running Tests

### Cypress Tests

Interactive mode:
```bash
npm run e2e:headed
```

Headless mode:
```bash
npm run e2e
```

### Playwright Tests

Run all tests:
```bash
npm run playwright
```

Debug mode:
```bash
npm run playwright:debug
```

UI mode:
```bash
npm run playwright:ui
```

### Run All Tests

```bash
./testing/e2e/run-all-tests.sh
```

## Test Structure

- `cypress/integration/`: Cypress test specs
- `playwright/tests/`: Playwright test specs
- `cypress/support/`: Custom commands and helpers
- `cypress/fixtures/`: Test data fixtures

## Writing Tests

### Cypress Example

```typescript
describe('Feature', () => {
  it('should do something', () => {
    cy.visit('/page')
    cy.get('[data-cy=element]').click()
    cy.contains('Expected text').should('be.visible')
  })
})
```

### Playwright Example

```typescript
test('should do something', async ({ page }) => {
  await page.goto('/page')
  await page.click('[data-cy=element]')
  await expect(page.locator('text=Expected text')).toBeVisible()
})
```

## Best Practices

1. Use `data-cy` attributes for element selection
2. Keep tests independent and idempotent
3. Use fixtures for test data
4. Mock external services when appropriate
5. Run tests in parallel when possible
6. Keep tests focused and atomic

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests

See `.github/workflows/e2e-tests.yml` for configuration.
EOF

echo -e "${GREEN}✓ E2E test documentation created${NC}"

echo -e "\n${GREEN}==================================="
echo "E2E Testing Setup Complete!"
echo "==================================="
echo -e "${NC}"
echo "Next steps:"
echo "1. Run 'npm install' to install dependencies"
echo "2. Set up test database: ./testing/e2e/setup-test-db.sh"
echo "3. Run Cypress tests: npm run e2e"
echo "4. Run Playwright tests: npm run playwright"
echo "5. Run all tests: ./testing/e2e/run-all-tests.sh"
echo ""
echo "For more information, see testing/e2e/README.md"