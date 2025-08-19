// ***********************************************************
// This file is processed and loaded automatically before test files.
// You can change the location of this file or turn off loading
// the support files with the 'supportFile' configuration option.
// ***********************************************************

import './commands'

// Import commands.js using ES2015 syntax:
// Alternatively you can use CommonJS syntax:
// require('./commands')

// Custom error handling
Cypress.on('uncaught:exception', (err, runnable) => {
  // Prevent Cypress from failing tests on uncaught exceptions
  // that are expected in the application
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false
  }
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false
  }
  // Let other errors fail the test
  return true
})

// Add custom logging
beforeEach(() => {
  cy.log('Test started: ' + Cypress.currentTest.title)
})

afterEach(() => {
  cy.log('Test completed: ' + Cypress.currentTest.title)
})

// Global test configuration
before(() => {
  // Clear all data before test suite
  cy.task('db:seed')
  
  // Set up test data
  cy.task('createTestUsers')
  cy.task('createTestPolicies')
  cy.task('createTestRepresentatives')
})

// Clean up after all tests
after(() => {
  cy.task('db:cleanup')
})

// Add viewport presets
Cypress.Commands.add('setMobileViewport', () => {
  cy.viewport('iphone-x')
})

Cypress.Commands.add('setTabletViewport', () => {
  cy.viewport('ipad-2')
})

Cypress.Commands.add('setDesktopViewport', () => {
  cy.viewport(1920, 1080)
})

// Performance monitoring
Cypress.Commands.add('measurePerformance', (label: string) => {
  cy.window().then((win) => {
    win.performance.mark(`${label}-start`)
    
    cy.on('command:end', () => {
      win.performance.mark(`${label}-end`)
      win.performance.measure(label, `${label}-start`, `${label}-end`)
      
      const measure = win.performance.getEntriesByName(label)[0]
      cy.log(`Performance: ${label} took ${measure.duration}ms`)
    })
  })
})

// Network stubbing helpers
Cypress.Commands.add('stubAPIEndpoints', () => {
  // Stub common API endpoints for faster tests
  cy.intercept('GET', '/api/auth/session', { fixture: 'session.json' }).as('getSession')
  cy.intercept('GET', '/api/policies*', { fixture: 'policies.json' }).as('getPolicies')
  cy.intercept('GET', '/api/representatives*', { fixture: 'representatives.json' }).as('getRepresentatives')
})

// Accessibility testing
Cypress.Commands.add('checkA11y', (context?: string) => {
  cy.injectAxe()
  cy.checkA11y(context, {
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa']
    }
  })
})

// Visual regression testing placeholder
Cypress.Commands.add('compareSnapshot', (name: string) => {
  cy.screenshot(name)
  // In a real implementation, this would compare with baseline images
})

// API testing helpers
Cypress.Commands.add('apiRequest', (method: string, url: string, body?: any) => {
  cy.request({
    method,
    url: Cypress.env('API_URL') + url,
    body,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${window.localStorage.getItem('authToken')}`
    }
  })
})

// Custom wait helpers
Cypress.Commands.add('waitForLoadingToFinish', () => {
  cy.get('[data-cy=loading]').should('not.exist')
  cy.get('[data-cy=spinner]').should('not.exist')
})