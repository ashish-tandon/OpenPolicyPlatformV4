/// <reference types="cypress" />

describe('Admin Dashboard', () => {
  beforeEach(() => {
    cy.login(Cypress.env('ADMIN_USER_EMAIL'), Cypress.env('ADMIN_USER_PASSWORD'), '/admin')
    cy.visit('/admin/dashboard')
  })

  describe('Service Health Monitoring', () => {
    it('should display all service statuses', () => {
      cy.get('[data-cy=service-status-grid]').should('be.visible')
      cy.get('[data-cy=service-card]').should('have.length', 23) // 23 microservices
      
      // Check each service has status indicator
      cy.get('[data-cy=service-card]').each(($el) => {
        cy.wrap($el).find('[data-cy=service-name]').should('be.visible')
        cy.wrap($el).find('[data-cy=service-status]').should('be.visible')
        cy.wrap($el).find('[data-cy=service-uptime]').should('be.visible')
      })
    })

    it('should refresh service statuses', () => {
      cy.get('[data-cy=refresh-status]').click()
      cy.get('[data-cy=loading-spinner]').should('be.visible')
      cy.get('[data-cy=loading-spinner]').should('not.exist')
      cy.get('[data-cy=last-updated]').should('contain', 'Just now')
    })

    it('should view service details', () => {
      cy.get('[data-cy=service-card]').first().click()
      
      cy.get('[data-cy=service-detail-modal]').should('be.visible')
      cy.get('[data-cy=service-logs]').should('be.visible')
      cy.get('[data-cy=service-metrics]').should('be.visible')
      cy.get('[data-cy=service-endpoints]').should('be.visible')
    })

    it('should restart a service', () => {
      cy.get('[data-cy=service-card]').first().within(() => {
        cy.get('[data-cy=service-actions]').click()
        cy.get('[data-cy=restart-service]').click()
      })
      
      cy.get('[data-cy=confirm-modal]').should('be.visible')
      cy.get('[data-cy=confirm-restart]').click()
      
      cy.get('[data-cy=notification]').should('contain', 'Service restarting')
    })
  })

  describe('System Metrics', () => {
    it('should display system overview metrics', () => {
      cy.get('[data-cy=metrics-dashboard]').should('be.visible')
      cy.get('[data-cy=total-users]').should('be.visible')
      cy.get('[data-cy=active-sessions]').should('be.visible')
      cy.get('[data-cy=api-requests]').should('be.visible')
      cy.get('[data-cy=system-uptime]').should('be.visible')
    })

    it('should display real-time charts', () => {
      cy.get('[data-cy=cpu-usage-chart]').should('be.visible')
      cy.get('[data-cy=memory-usage-chart]').should('be.visible')
      cy.get('[data-cy=network-traffic-chart]').should('be.visible')
      cy.get('[data-cy=response-time-chart]').should('be.visible')
    })

    it('should export metrics data', () => {
      cy.get('[data-cy=export-metrics]').click()
      cy.get('[data-cy=export-modal]').should('be.visible')
      
      cy.get('[data-cy=date-range-start]').type('2024-01-01')
      cy.get('[data-cy=date-range-end]').type('2024-01-31')
      cy.get('[data-cy=export-format]').select('csv')
      cy.get('[data-cy=export-button]').click()
      
      cy.get('[data-cy=export-success]').should('be.visible')
    })
  })

  describe('User Management', () => {
    it('should display user list', () => {
      cy.visit('/admin/users')
      
      cy.get('[data-cy=users-table]').should('be.visible')
      cy.get('[data-cy=user-row]').should('have.length.greaterThan', 0)
    })

    it('should search and filter users', () => {
      cy.visit('/admin/users')
      
      // Search by email
      cy.get('[data-cy=user-search]').type('test@')
      cy.get('[data-cy=user-row]').each(($el) => {
        cy.wrap($el).find('[data-cy=user-email]').should('contain', 'test@')
      })
      
      // Filter by role
      cy.get('[data-cy=role-filter]').select('admin')
      cy.get('[data-cy=user-row]').each(($el) => {
        cy.wrap($el).find('[data-cy=user-role]').should('contain', 'Admin')
      })
    })

    it('should edit user details', () => {
      cy.visit('/admin/users')
      
      cy.get('[data-cy=user-row]').first().find('[data-cy=edit-user]').click()
      cy.get('[data-cy=edit-user-modal]').should('be.visible')
      
      cy.get('[data-cy=user-role-select]').select('moderator')
      cy.get('[data-cy=save-user]').click()
      
      cy.get('[data-cy=notification]').should('contain', 'User updated successfully')
    })

    it('should manage user permissions', () => {
      cy.visit('/admin/users')
      
      cy.get('[data-cy=user-row]').first().find('[data-cy=manage-permissions]').click()
      cy.get('[data-cy=permissions-modal]').should('be.visible')
      
      cy.get('[data-cy=permission-toggle-write-policies]').click()
      cy.get('[data-cy=permission-toggle-delete-content]').click()
      cy.get('[data-cy=save-permissions]').click()
      
      cy.get('[data-cy=notification]').should('contain', 'Permissions updated')
    })
  })

  describe('Audit Logs', () => {
    it('should display audit log entries', () => {
      cy.visit('/admin/audit-logs')
      
      cy.get('[data-cy=audit-logs-table]').should('be.visible')
      cy.get('[data-cy=log-entry]').should('have.length.greaterThan', 0)
      
      // Check log entry details
      cy.get('[data-cy=log-entry]').first().within(() => {
        cy.get('[data-cy=log-timestamp]').should('be.visible')
        cy.get('[data-cy=log-user]').should('be.visible')
        cy.get('[data-cy=log-action]').should('be.visible')
        cy.get('[data-cy=log-resource]').should('be.visible')
      })
    })

    it('should filter audit logs', () => {
      cy.visit('/admin/audit-logs')
      
      // Filter by action type
      cy.get('[data-cy=action-filter]').select('user_login')
      cy.get('[data-cy=log-entry]').each(($el) => {
        cy.wrap($el).find('[data-cy=log-action]').should('contain', 'Login')
      })
      
      // Filter by date range
      cy.get('[data-cy=date-filter-start]').type('2024-01-01')
      cy.get('[data-cy=date-filter-end]').type('2024-01-31')
      cy.get('[data-cy=apply-filters]').click()
      
      cy.get('[data-cy=log-entry]').should('have.length.greaterThan', 0)
    })
  })

  describe('System Configuration', () => {
    it('should manage environment variables', () => {
      cy.visit('/admin/configuration')
      
      cy.get('[data-cy=env-vars-section]').should('be.visible')
      cy.get('[data-cy=env-var-item]').should('have.length.greaterThan', 0)
      
      // Edit an environment variable
      cy.get('[data-cy=env-var-item]').first().find('[data-cy=edit-env-var]').click()
      cy.get('[data-cy=env-var-value]').clear().type('new-value')
      cy.get('[data-cy=save-env-var]').click()
      
      cy.get('[data-cy=notification]').should('contain', 'Configuration updated')
    })

    it('should manage feature flags', () => {
      cy.visit('/admin/configuration/features')
      
      cy.get('[data-cy=feature-flags-list]').should('be.visible')
      
      // Toggle a feature flag
      cy.get('[data-cy=feature-flag-item]').first().within(() => {
        cy.get('[data-cy=feature-toggle]').click()
      })
      
      cy.get('[data-cy=notification]').should('contain', 'Feature flag updated')
    })
  })

  describe('Backup and Recovery', () => {
    it('should create manual backup', () => {
      cy.visit('/admin/backup')
      
      cy.get('[data-cy=create-backup]').click()
      cy.get('[data-cy=backup-modal]').should('be.visible')
      
      cy.get('[data-cy=backup-name]').type('Manual Backup Test')
      cy.get('[data-cy=include-database]').check()
      cy.get('[data-cy=include-files]').check()
      cy.get('[data-cy=start-backup]').click()
      
      cy.get('[data-cy=backup-progress]').should('be.visible')
      cy.get('[data-cy=backup-complete]', { timeout: 30000 }).should('be.visible')
    })

    it('should restore from backup', () => {
      cy.visit('/admin/backup')
      
      cy.get('[data-cy=backup-list]').should('be.visible')
      cy.get('[data-cy=backup-item]').first().find('[data-cy=restore-backup]').click()
      
      cy.get('[data-cy=restore-modal]').should('be.visible')
      cy.get('[data-cy=confirm-restore]').click()
      
      cy.get('[data-cy=restore-progress]').should('be.visible')
    })
  })
})