/// <reference types="cypress" />

describe('Search Functionality', () => {
  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
    cy.visit('/')
  })

  describe('Global Search', () => {
    it('should perform global search', () => {
      cy.get('[data-cy=global-search]').type('healthcare{enter}')
      
      cy.url().should('include', '/search?q=healthcare')
      cy.get('[data-cy=search-results]').should('be.visible')
      cy.get('[data-cy=result-count]').should('contain', 'results')
    })

    it('should display search suggestions', () => {
      cy.get('[data-cy=global-search]').type('health')
      
      cy.get('[data-cy=search-suggestions]').should('be.visible')
      cy.get('[data-cy=suggestion-item]').should('have.length.greaterThan', 0)
      
      // Click a suggestion
      cy.get('[data-cy=suggestion-item]').first().click()
      cy.url().should('include', '/search')
    })

    it('should display recent searches', () => {
      // Perform some searches
      cy.get('[data-cy=global-search]').type('education{enter}')
      cy.visit('/')
      cy.get('[data-cy=global-search]').type('environment{enter}')
      cy.visit('/')
      
      // Check recent searches
      cy.get('[data-cy=global-search]').click()
      cy.get('[data-cy=recent-searches]').should('be.visible')
      cy.get('[data-cy=recent-search-item]').should('contain', 'education')
      cy.get('[data-cy=recent-search-item]').should('contain', 'environment')
    })
  })

  describe('Search Filters', () => {
    beforeEach(() => {
      cy.get('[data-cy=global-search]').type('policy{enter}')
    })

    it('should filter by content type', () => {
      cy.get('[data-cy=filter-policies]').click()
      cy.get('[data-cy=result-item]').each(($el) => {
        cy.wrap($el).find('[data-cy=result-type]').should('contain', 'Policy')
      })

      cy.get('[data-cy=filter-representatives]').click()
      cy.get('[data-cy=result-item]').each(($el) => {
        cy.wrap($el).find('[data-cy=result-type]').should('contain', 'Representative')
      })
    })

    it('should filter by date range', () => {
      cy.get('[data-cy=date-filter-toggle]').click()
      cy.get('[data-cy=date-from]').type('2024-01-01')
      cy.get('[data-cy=date-to]').type('2024-12-31')
      cy.get('[data-cy=apply-date-filter]').click()
      
      cy.get('[data-cy=result-item]').should('have.length.greaterThan', 0)
    })

    it('should sort search results', () => {
      cy.get('[data-cy=sort-dropdown]').select('date-desc')
      cy.wait(500)
      
      let previousDate = new Date()
      cy.get('[data-cy=result-date]').each(($el) => {
        const currentDate = new Date($el.text())
        expect(currentDate.getTime()).to.be.at.most(previousDate.getTime())
        previousDate = currentDate
      })
    })
  })

  describe('Advanced Search', () => {
    it('should access advanced search', () => {
      cy.get('[data-cy=advanced-search-link]').click()
      cy.url().should('include', '/search/advanced')
      
      cy.get('[data-cy=advanced-search-form]').should('be.visible')
    })

    it('should perform advanced search with multiple criteria', () => {
      cy.visit('/search/advanced')
      
      cy.get('[data-cy=keyword-input]').type('climate change')
      cy.get('[data-cy=category-select]').select('environment')
      cy.get('[data-cy=author-input]').type('Smith')
      cy.get('[data-cy=date-from]').type('2024-01-01')
      cy.get('[data-cy=date-to]').type('2024-12-31')
      
      cy.get('[data-cy=advanced-search-button]').click()
      
      cy.url().should('include', '/search')
      cy.get('[data-cy=search-results]').should('be.visible')
      cy.get('[data-cy=applied-filters]').should('contain', 'climate change')
      cy.get('[data-cy=applied-filters]').should('contain', 'Environment')
    })

    it('should save search query', () => {
      cy.visit('/search/advanced')
      
      cy.get('[data-cy=keyword-input]').type('infrastructure')
      cy.get('[data-cy=category-select]').select('transportation')
      
      cy.get('[data-cy=save-search]').click()
      cy.get('[data-cy=search-name-input]').type('Infrastructure Search')
      cy.get('[data-cy=confirm-save]').click()
      
      cy.get('[data-cy=notification]').should('contain', 'Search saved')
      
      // Verify saved search
      cy.visit('/dashboard/saved-searches')
      cy.get('[data-cy=saved-search-item]').should('contain', 'Infrastructure Search')
    })
  })

  describe('Search Results', () => {
    beforeEach(() => {
      cy.get('[data-cy=global-search]').type('bill{enter}')
    })

    it('should view search result details', () => {
      cy.get('[data-cy=result-item]').first().click()
      
      // Should navigate to appropriate detail page
      cy.url().should('match', /\/(policies|representatives|committees)\/[a-zA-Z0-9-]+/)
    })

    it('should paginate search results', () => {
      cy.get('[data-cy=search-pagination]').should('be.visible')
      
      // Go to page 2
      cy.get('[data-cy=page-2]').click()
      cy.url().should('include', 'page=2')
      
      // Use next/prev buttons
      cy.get('[data-cy=next-page]').click()
      cy.url().should('include', 'page=3')
      
      cy.get('[data-cy=prev-page]').click()
      cy.url().should('include', 'page=2')
    })

    it('should export search results', () => {
      cy.get('[data-cy=export-results]').click()
      cy.get('[data-cy=export-modal]').should('be.visible')
      
      cy.get('[data-cy=export-format]').select('csv')
      cy.get('[data-cy=export-button]').click()
      
      cy.get('[data-cy=export-success]').should('be.visible')
    })
  })

  describe('Search Analytics', () => {
    it('should track search queries', () => {
      // Perform searches
      cy.get('[data-cy=global-search]').type('taxation{enter}')
      cy.visit('/')
      cy.get('[data-cy=global-search]').type('housing{enter}')
      
      // Check search history in profile
      cy.visit('/profile/search-history')
      cy.get('[data-cy=search-history-item]').should('contain', 'taxation')
      cy.get('[data-cy=search-history-item]').should('contain', 'housing')
    })

    it('should display trending searches', () => {
      cy.visit('/search/trending')
      
      cy.get('[data-cy=trending-searches]').should('be.visible')
      cy.get('[data-cy=trending-item]').should('have.length.greaterThan', 0)
      
      // Click trending item
      cy.get('[data-cy=trending-item]').first().click()
      cy.url().should('include', '/search?q=')
    })
  })
})