/// <reference types="cypress" />

describe('Policies and Bills', () => {
  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
    cy.visit('/policies')
  })

  describe('Policy List', () => {
    it('should display list of policies', () => {
      cy.get('[data-cy=policy-list]').should('be.visible')
      cy.get('[data-cy=policy-item]').should('have.length.greaterThan', 0)
    })

    it('should filter policies by status', () => {
      // Filter by active policies
      cy.get('[data-cy=status-filter]').select('active')
      cy.get('[data-cy=policy-item]').each(($el) => {
        cy.wrap($el).find('[data-cy=policy-status]').should('contain', 'Active')
      })

      // Filter by passed policies
      cy.get('[data-cy=status-filter]').select('passed')
      cy.get('[data-cy=policy-item]').each(($el) => {
        cy.wrap($el).find('[data-cy=policy-status]').should('contain', 'Passed')
      })
    })

    it('should search policies by keyword', () => {
      const searchTerm = 'healthcare'
      cy.get('[data-cy=search-input]').type(searchTerm)
      cy.get('[data-cy=search-button]').click()

      cy.get('[data-cy=policy-item]').each(($el) => {
        cy.wrap($el).should('contain.text', searchTerm, { matchCase: false })
      })
    })

    it('should paginate through policies', () => {
      // Check pagination exists
      cy.get('[data-cy=pagination]').should('be.visible')
      
      // Go to next page
      cy.get('[data-cy=next-page]').click()
      cy.url().should('include', 'page=2')
      
      // Go to previous page
      cy.get('[data-cy=prev-page]').click()
      cy.url().should('include', 'page=1')
    })
  })

  describe('Policy Details', () => {
    it('should view policy details', () => {
      cy.get('[data-cy=policy-item]').first().click()
      
      cy.url().should('match', /\/policies\/[a-zA-Z0-9-]+/)
      cy.get('[data-cy=policy-title]').should('be.visible')
      cy.get('[data-cy=policy-description]').should('be.visible')
      cy.get('[data-cy=policy-sponsor]').should('be.visible')
      cy.get('[data-cy=policy-status]').should('be.visible')
    })

    it('should display voting history', () => {
      cy.get('[data-cy=policy-item]').first().click()
      
      cy.get('[data-cy=voting-tab]').click()
      cy.get('[data-cy=voting-history]').should('be.visible')
      cy.get('[data-cy=vote-item]').should('have.length.greaterThan', 0)
    })

    it('should display related documents', () => {
      cy.get('[data-cy=policy-item]').first().click()
      
      cy.get('[data-cy=documents-tab]').click()
      cy.get('[data-cy=document-list]').should('be.visible')
      cy.get('[data-cy=document-item]').should('have.length.greaterThan', 0)
    })

    it('should download policy PDF', () => {
      cy.get('[data-cy=policy-item]').first().click()
      
      cy.get('[data-cy=download-pdf]').click()
      // Verify download was initiated (Cypress cannot verify actual file download)
      cy.get('[data-cy=download-success]').should('be.visible')
    })
  })

  describe('Policy Tracking', () => {
    it('should add policy to watchlist', () => {
      cy.get('[data-cy=policy-item]').first().within(() => {
        cy.get('[data-cy=add-to-watchlist]').click()
      })
      
      cy.get('[data-cy=notification]').should('contain', 'Added to watchlist')
      
      // Verify in user's watchlist
      cy.visit('/dashboard/watchlist')
      cy.get('[data-cy=watchlist-item]').should('have.length.greaterThan', 0)
    })

    it('should receive notifications for tracked policies', () => {
      // Add policy to watchlist
      cy.get('[data-cy=policy-item]').first().within(() => {
        cy.get('[data-cy=add-to-watchlist]').click()
      })
      
      // Check notification settings
      cy.visit('/settings/notifications')
      cy.get('[data-cy=policy-updates-toggle]').should('be.checked')
    })
  })

  describe('Policy Analytics', () => {
    it('should view policy impact analytics', () => {
      cy.get('[data-cy=policy-item]').first().click()
      cy.get('[data-cy=analytics-tab]').click()
      
      cy.get('[data-cy=impact-chart]').should('be.visible')
      cy.get('[data-cy=demographics-chart]').should('be.visible')
      cy.get('[data-cy=timeline-chart]').should('be.visible')
    })

    it('should export analytics data', () => {
      cy.get('[data-cy=policy-item]').first().click()
      cy.get('[data-cy=analytics-tab]').click()
      
      cy.get('[data-cy=export-data]').click()
      cy.get('[data-cy=export-format]').select('csv')
      cy.get('[data-cy=export-button]').click()
      
      cy.get('[data-cy=export-success]').should('be.visible')
    })
  })
})