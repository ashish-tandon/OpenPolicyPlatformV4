/// <reference types="cypress" />

describe('Representatives', () => {
  beforeEach(() => {
    cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
    cy.visit('/representatives')
  })

  describe('Representatives List', () => {
    it('should display list of representatives', () => {
      cy.get('[data-cy=representatives-grid]').should('be.visible')
      cy.get('[data-cy=representative-card]').should('have.length.greaterThan', 0)
    })

    it('should filter representatives by party', () => {
      cy.get('[data-cy=party-filter]').select('Liberal')
      cy.get('[data-cy=representative-card]').each(($el) => {
        cy.wrap($el).find('[data-cy=party-badge]').should('contain', 'Liberal')
      })

      cy.get('[data-cy=party-filter]').select('Conservative')
      cy.get('[data-cy=representative-card]').each(($el) => {
        cy.wrap($el).find('[data-cy=party-badge]').should('contain', 'Conservative')
      })
    })

    it('should filter representatives by province', () => {
      cy.get('[data-cy=province-filter]').select('Ontario')
      cy.get('[data-cy=representative-card]').each(($el) => {
        cy.wrap($el).find('[data-cy=province-info]').should('contain', 'ON')
      })
    })

    it('should search representatives by name', () => {
      const searchName = 'Smith'
      cy.get('[data-cy=search-representatives]').type(searchName)
      cy.get('[data-cy=search-button]').click()

      cy.get('[data-cy=representative-card]').each(($el) => {
        cy.wrap($el).find('[data-cy=representative-name]')
          .should('contain.text', searchName, { matchCase: false })
      })
    })

    it('should sort representatives', () => {
      // Sort by name
      cy.get('[data-cy=sort-dropdown]').select('name-asc')
      cy.wait(500)
      
      let previousName = ''
      cy.get('[data-cy=representative-name]').each(($el) => {
        const currentName = $el.text()
        if (previousName) {
          expect(currentName.localeCompare(previousName)).to.be.at.least(0)
        }
        previousName = currentName
      })
    })
  })

  describe('Representative Profile', () => {
    it('should view representative profile', () => {
      cy.get('[data-cy=representative-card]').first().click()
      
      cy.url().should('match', /\/representatives\/[a-zA-Z0-9-]+/)
      cy.get('[data-cy=representative-photo]').should('be.visible')
      cy.get('[data-cy=representative-name]').should('be.visible')
      cy.get('[data-cy=representative-party]').should('be.visible')
      cy.get('[data-cy=representative-riding]').should('be.visible')
      cy.get('[data-cy=contact-info]').should('be.visible')
    })

    it('should display voting record', () => {
      cy.get('[data-cy=representative-card]').first().click()
      
      cy.get('[data-cy=voting-record-tab]').click()
      cy.get('[data-cy=voting-record]').should('be.visible')
      cy.get('[data-cy=vote-entry]').should('have.length.greaterThan', 0)
      
      // Check vote breakdown
      cy.get('[data-cy=vote-stats]').within(() => {
        cy.get('[data-cy=votes-for]').should('be.visible')
        cy.get('[data-cy=votes-against]').should('be.visible')
        cy.get('[data-cy=votes-abstained]').should('be.visible')
      })
    })

    it('should display attendance record', () => {
      cy.get('[data-cy=representative-card]').first().click()
      
      cy.get('[data-cy=attendance-tab]').click()
      cy.get('[data-cy=attendance-chart]').should('be.visible')
      cy.get('[data-cy=attendance-percentage]').should('be.visible')
    })

    it('should display committee memberships', () => {
      cy.get('[data-cy=representative-card]').first().click()
      
      cy.get('[data-cy=committees-tab]').click()
      cy.get('[data-cy=committee-list]').should('be.visible')
      cy.get('[data-cy=committee-item]').should('have.length.greaterThan', 0)
    })

    it('should display speeches and statements', () => {
      cy.get('[data-cy=representative-card]').first().click()
      
      cy.get('[data-cy=speeches-tab]').click()
      cy.get('[data-cy=speeches-list]').should('be.visible')
      cy.get('[data-cy=speech-item]').should('have.length.greaterThan', 0)
      
      // View speech details
      cy.get('[data-cy=speech-item]').first().click()
      cy.get('[data-cy=speech-content]').should('be.visible')
      cy.get('[data-cy=speech-date]').should('be.visible')
    })
  })

  describe('Representative Comparison', () => {
    it('should compare multiple representatives', () => {
      // Select representatives for comparison
      cy.get('[data-cy=compare-mode-toggle]').click()
      cy.get('[data-cy=representative-card]').eq(0).find('[data-cy=compare-checkbox]').check()
      cy.get('[data-cy=representative-card]').eq(1).find('[data-cy=compare-checkbox]').check()
      cy.get('[data-cy=representative-card]').eq(2).find('[data-cy=compare-checkbox]').check()
      
      cy.get('[data-cy=compare-button]').click()
      
      // Verify comparison view
      cy.url().should('include', '/representatives/compare')
      cy.get('[data-cy=comparison-table]').should('be.visible')
      cy.get('[data-cy=comparison-chart]').should('be.visible')
    })
  })

  describe('Contact Representative', () => {
    it('should send message to representative', () => {
      cy.get('[data-cy=representative-card]').first().click()
      
      cy.get('[data-cy=contact-button]').click()
      cy.get('[data-cy=contact-modal]').should('be.visible')
      
      cy.get('[data-cy=subject-input]').type('Policy Inquiry')
      cy.get('[data-cy=message-textarea]').type('I would like to discuss the recent healthcare policy...')
      cy.get('[data-cy=send-message-button]').click()
      
      cy.get('[data-cy=success-notification]').should('contain', 'Message sent successfully')
    })
  })
})