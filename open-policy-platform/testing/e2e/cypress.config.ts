import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    
    env: {
      API_URL: 'http://localhost:9000',
      ADMIN_URL: 'http://localhost:3001',
      TEST_USER_EMAIL: 'test@openpolicy.local',
      TEST_USER_PASSWORD: 'testpassword123',
      ADMIN_USER_EMAIL: 'admin@openpolicy.local', 
      ADMIN_USER_PASSWORD: 'adminpassword123'
    },
    
    setupNodeEvents(on, config) {
      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message)
          return null
        },
      })
    },
    
    specPattern: 'testing/e2e/cypress/integration/**/*.cy.{js,ts}',
    supportFile: 'testing/e2e/cypress/support/e2e.ts',
    
    // Retry configuration for flaky tests
    retries: {
      runMode: 2,
      openMode: 0
    },
    
    // Timeouts
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    
    // Security headers handling
    chromeWebSecurity: false
  },
})