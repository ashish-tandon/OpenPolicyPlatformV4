/// <reference types="cypress" />

describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  describe('User Registration', () => {
    it('should register a new user successfully', () => {
      cy.get('[data-cy=signup-link]').click()
      cy.url().should('include', '/signup')
      
      const timestamp = Date.now()
      const email = `user${timestamp}@test.com`
      
      cy.get('[data-cy=email-input]').type(email)
      cy.get('[data-cy=password-input]').type('TestPassword123!')
      cy.get('[data-cy=confirm-password-input]').type('TestPassword123!')
      cy.get('[data-cy=terms-checkbox]').check()
      cy.get('[data-cy=signup-button]').click()
      
      // Verify email verification page
      cy.url().should('include', '/verify-email')
      cy.contains('Please check your email').should('be.visible')
    })

    it('should validate registration form', () => {
      cy.get('[data-cy=signup-link]').click()
      
      // Test invalid email
      cy.get('[data-cy=email-input]').type('invalid-email')
      cy.get('[data-cy=signup-button]').click()
      cy.contains('Please enter a valid email').should('be.visible')
      
      // Test password mismatch
      cy.get('[data-cy=email-input]').clear().type('test@example.com')
      cy.get('[data-cy=password-input]').type('Password123!')
      cy.get('[data-cy=confirm-password-input]').type('DifferentPassword123!')
      cy.get('[data-cy=signup-button]').click()
      cy.contains('Passwords do not match').should('be.visible')
    })
  })

  describe('User Login', () => {
    it('should login with valid credentials', () => {
      cy.get('[data-cy=login-link]').click()
      cy.url().should('include', '/login')
      
      cy.get('[data-cy=email-input]').type(Cypress.env('TEST_USER_EMAIL'))
      cy.get('[data-cy=password-input]').type(Cypress.env('TEST_USER_PASSWORD'))
      cy.get('[data-cy=login-button]').click()
      
      // Verify successful login
      cy.url().should('eq', Cypress.config().baseUrl + '/')
      cy.get('[data-cy=user-menu]').should('be.visible')
      cy.get('[data-cy=user-menu]').click()
      cy.contains(Cypress.env('TEST_USER_EMAIL')).should('be.visible')
    })

    it('should show error for invalid credentials', () => {
      cy.get('[data-cy=login-link]').click()
      
      cy.get('[data-cy=email-input]').type('wrong@email.com')
      cy.get('[data-cy=password-input]').type('wrongpassword')
      cy.get('[data-cy=login-button]').click()
      
      cy.contains('Invalid email or password').should('be.visible')
    })

    it('should handle password reset flow', () => {
      cy.get('[data-cy=login-link]').click()
      cy.get('[data-cy=forgot-password-link]').click()
      
      cy.url().should('include', '/forgot-password')
      cy.get('[data-cy=email-input]').type(Cypress.env('TEST_USER_EMAIL'))
      cy.get('[data-cy=reset-password-button]').click()
      
      cy.contains('Password reset email sent').should('be.visible')
    })
  })

  describe('User Logout', () => {
    beforeEach(() => {
      // Login first
      cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
    })

    it('should logout successfully', () => {
      cy.get('[data-cy=user-menu]').click()
      cy.get('[data-cy=logout-button]').click()
      
      cy.url().should('eq', Cypress.config().baseUrl + '/')
      cy.get('[data-cy=login-link]').should('be.visible')
      cy.get('[data-cy=user-menu]').should('not.exist')
    })
  })

  describe('Session Management', () => {
    it('should maintain session on page refresh', () => {
      cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
      
      cy.reload()
      cy.get('[data-cy=user-menu]').should('be.visible')
    })

    it('should redirect to login when session expires', () => {
      cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
      
      // Simulate session expiration
      cy.clearCookies()
      cy.clearLocalStorage()
      
      cy.visit('/dashboard')
      cy.url().should('include', '/login')
    })
  })
})