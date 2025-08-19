/// <reference types="cypress" />

describe('Mobile Responsiveness', () => {
  const viewports = [
    { name: 'iPhone SE', width: 375, height: 667 },
    { name: 'iPhone 12', width: 390, height: 844 },
    { name: 'iPad Mini', width: 768, height: 1024 },
    { name: 'iPad Pro', width: 1024, height: 1366 }
  ]

  viewports.forEach(viewport => {
    describe(`${viewport.name} (${viewport.width}x${viewport.height})`, () => {
      beforeEach(() => {
        cy.viewport(viewport.width, viewport.height)
        cy.login(Cypress.env('TEST_USER_EMAIL'), Cypress.env('TEST_USER_PASSWORD'))
      })

      describe('Navigation', () => {
        it('should toggle mobile menu', () => {
          cy.visit('/')
          
          // Menu should be hidden initially
          cy.get('[data-cy=mobile-menu]').should('not.be.visible')
          
          // Open menu
          cy.get('[data-cy=mobile-menu-toggle]').click()
          cy.get('[data-cy=mobile-menu]').should('be.visible')
          
          // Close menu
          cy.get('[data-cy=mobile-menu-close]').click()
          cy.get('[data-cy=mobile-menu]').should('not.be.visible')
        })

        it('should navigate through mobile menu', () => {
          cy.visit('/')
          cy.get('[data-cy=mobile-menu-toggle]').click()
          
          cy.get('[data-cy=mobile-nav-policies]').click()
          cy.url().should('include', '/policies')
          
          cy.get('[data-cy=mobile-menu-toggle]').click()
          cy.get('[data-cy=mobile-nav-representatives]').click()
          cy.url().should('include', '/representatives')
        })
      })

      describe('Content Layout', () => {
        it('should display responsive policy cards', () => {
          cy.visit('/policies')
          
          cy.get('[data-cy=policy-grid]').should('be.visible')
          
          if (viewport.width < 768) {
            // Single column on mobile
            cy.get('[data-cy=policy-grid]').should('have.css', 'grid-template-columns')
              .and('match', /^\d+px$/) // Single column
          } else {
            // Multiple columns on tablet
            cy.get('[data-cy=policy-grid]').should('have.css', 'grid-template-columns')
              .and('not.match', /^\d+px$/) // Multiple columns
          }
        })

        it('should display responsive representative cards', () => {
          cy.visit('/representatives')
          
          cy.get('[data-cy=representatives-grid]').should('be.visible')
          
          // Check card layout adjusts properly
          cy.get('[data-cy=representative-card]').first().then($card => {
            const cardWidth = $card.width()
            if (viewport.width < 768) {
              expect(cardWidth).to.be.closeTo(viewport.width - 32, 50) // Full width minus padding
            }
          })
        })
      })

      describe('Touch Interactions', () => {
        it('should support swipe gestures on carousels', () => {
          cy.visit('/')
          
          if (cy.get('[data-cy=featured-carousel]').should('exist')) {
            // Swipe left
            cy.get('[data-cy=featured-carousel]')
              .trigger('touchstart', { touches: [{ clientX: 300, clientY: 200 }] })
              .trigger('touchmove', { touches: [{ clientX: 100, clientY: 200 }] })
              .trigger('touchend')
            
            cy.get('[data-cy=carousel-slide-2]').should('be.visible')
          }
        })

        it('should have touch-friendly buttons', () => {
          cy.visit('/policies')
          
          // Check button sizes
          cy.get('[data-cy=filter-button]').should('have.css', 'min-height')
            .and('match', /^(44|48|[5-9]\d|\d{3,})px$/) // At least 44px for touch targets
        })
      })

      describe('Forms', () => {
        it('should display responsive forms', () => {
          cy.visit('/login')
          
          // Check form layout
          cy.get('[data-cy=login-form]').should('be.visible')
          
          if (viewport.width < 768) {
            cy.get('[data-cy=login-form]').should('have.css', 'padding')
              .and('match', /^\d+px/) // Has padding on mobile
          }
          
          // Check input sizes
          cy.get('[data-cy=email-input]').should('have.css', 'font-size')
            .and('match', /^1[6-9]px$/) // At least 16px to prevent zoom on iOS
        })

        it('should handle virtual keyboard', () => {
          cy.visit('/search')
          
          // Focus on search input
          cy.get('[data-cy=search-input]').focus()
          
          // Check that viewport adjusts (simulation)
          cy.window().then(win => {
            // In real mobile, keyboard would reduce available height
            // Here we just check the input is visible
            cy.get('[data-cy=search-input]').should('be.visible')
          })
        })
      })

      describe('Tables', () => {
        it('should display responsive tables', () => {
          cy.visit('/dashboard')
          
          if (viewport.width < 768) {
            // Tables should transform on mobile
            cy.get('[data-cy=data-table]').should('have.class', 'mobile-table')
            
            // Or use horizontal scroll
            cy.get('[data-cy=table-wrapper]').should('have.css', 'overflow-x', 'auto')
          } else {
            // Normal table display on tablet
            cy.get('[data-cy=data-table]').should('not.have.class', 'mobile-table')
          }
        })
      })

      describe('Modals and Overlays', () => {
        it('should display full-screen modals on mobile', () => {
          cy.visit('/policies')
          cy.get('[data-cy=policy-item]').first().click()
          
          if (viewport.width < 768) {
            cy.get('[data-cy=policy-modal]').should('have.css', 'position', 'fixed')
            cy.get('[data-cy=policy-modal]').should('have.css', 'width')
              .and('match', new RegExp(`^${viewport.width}px$`))
          }
        })

        it('should handle bottom sheets on mobile', () => {
          if (viewport.width < 768) {
            cy.visit('/representatives')
            cy.get('[data-cy=filter-button]').click()
            
            // Filters should appear as bottom sheet
            cy.get('[data-cy=filter-sheet]').should('be.visible')
            cy.get('[data-cy=filter-sheet]').should('have.css', 'position', 'fixed')
            cy.get('[data-cy=filter-sheet]').should('have.css', 'bottom', '0px')
          }
        })
      })

      describe('Performance', () => {
        it('should lazy load images', () => {
          cy.visit('/representatives')
          
          // Check images have loading attribute
          cy.get('[data-cy=representative-photo]').each($img => {
            cy.wrap($img).should('have.attr', 'loading', 'lazy')
          })
        })

        it('should use responsive images', () => {
          cy.visit('/')
          
          // Check for srcset attribute
          cy.get('[data-cy=hero-image]').should('have.attr', 'srcset')
          
          // Or picture element with sources
          cy.get('picture source').should('exist')
        })
      })

      describe('Accessibility on Mobile', () => {
        it('should have proper touch target sizes', () => {
          cy.visit('/')
          
          // Check all interactive elements
          cy.get('button, a, [role="button"]').each($el => {
            const width = $el.width()
            const height = $el.height()
            
            // WCAG recommends at least 44x44px
            expect(Math.min(width, height)).to.be.at.least(44)
          })
        })

        it('should maintain focus visibility', () => {
          cy.visit('/policies')
          
          // Tab through elements
          cy.get('body').tab()
          
          // Check focus is visible
          cy.focused().should('have.css', 'outline-style')
            .and('not.eq', 'none')
        })
      })
    })
  })

  describe('Orientation Changes', () => {
    it('should handle portrait to landscape transition', () => {
      // Start in portrait
      cy.viewport(375, 667)
      cy.visit('/')
      
      // Switch to landscape
      cy.viewport(667, 375)
      
      // Check layout adjusts
      cy.get('[data-cy=header]').should('be.visible')
      cy.get('[data-cy=main-content]').should('be.visible')
    })
  })
})