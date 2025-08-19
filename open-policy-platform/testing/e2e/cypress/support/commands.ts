/// <reference types="cypress" />

// Custom command type definitions
declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string, redirectTo?: string): Chainable<void>
      logout(): Chainable<void>
      createUser(user: any): Chainable<any>
      deleteUser(userId: string): Chainable<void>
      clearDatabase(): Chainable<void>
      seedDatabase(): Chainable<void>
      waitForAPI(alias: string): Chainable<any>
      uploadFile(selector: string, fileName: string, fileType?: string): Chainable<void>
      dragAndDrop(subject: string, target: string): Chainable<void>
      selectDatePicker(selector: string, date: string): Chainable<void>
      checkNotification(message: string, type?: 'success' | 'error' | 'warning'): Chainable<void>
      dismissNotification(): Chainable<void>
      setMobileViewport(): Chainable<void>
      setTabletViewport(): Chainable<void>
      setDesktopViewport(): Chainable<void>
      measurePerformance(label: string): Chainable<void>
      stubAPIEndpoints(): Chainable<void>
      checkA11y(context?: string): Chainable<void>
      compareSnapshot(name: string): Chainable<void>
      apiRequest(method: string, url: string, body?: any): Chainable<Response<any>>
      waitForLoadingToFinish(): Chainable<void>
    }
  }
}

// Authentication commands
Cypress.Commands.add('login', (email: string, password: string, redirectTo = '/') => {
  cy.session(
    [email, password],
    () => {
      cy.visit('/login')
      cy.get('[data-cy=email-input]').type(email)
      cy.get('[data-cy=password-input]').type(password)
      cy.get('[data-cy=login-button]').click()
      
      // Wait for redirect after login
      cy.url().should('not.include', '/login')
      
      // Verify session is established
      cy.getCookie('session').should('exist')
    },
    {
      validate() {
        cy.getCookie('session').should('exist')
      }
    }
  )
  
  cy.visit(redirectTo)
})

Cypress.Commands.add('logout', () => {
  cy.get('[data-cy=user-menu]').click()
  cy.get('[data-cy=logout-button]').click()
  cy.url().should('include', '/login')
  cy.getCookie('session').should('not.exist')
})

// User management commands
Cypress.Commands.add('createUser', (user) => {
  return cy.request('POST', `${Cypress.env('API_URL')}/api/auth/register`, user)
    .then((response) => response.body)
})

Cypress.Commands.add('deleteUser', (userId: string) => {
  cy.request('DELETE', `${Cypress.env('API_URL')}/api/users/${userId}`)
})

// Database commands
Cypress.Commands.add('clearDatabase', () => {
  cy.task('db:clear')
})

Cypress.Commands.add('seedDatabase', () => {
  cy.task('db:seed')
})

// API wait helper
Cypress.Commands.add('waitForAPI', (alias: string) => {
  cy.intercept('GET', `**/${alias}**`).as(alias)
  cy.wait(`@${alias}`)
})

// File upload command
Cypress.Commands.add('uploadFile', (selector: string, fileName: string, fileType = 'text/plain') => {
  cy.get(selector).then(subject => {
    cy.fixture(fileName, 'base64').then((fileContent) => {
      const file = new File([Cypress.Blob.base64StringToBlob(fileContent)], fileName, { type: fileType })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file)
      
      const el = subject[0] as HTMLInputElement
      el.files = dataTransfer.files
      
      cy.wrap(subject).trigger('change', { force: true })
    })
  })
})

// Drag and drop command
Cypress.Commands.add('dragAndDrop', (subject: string, target: string) => {
  cy.get(subject)
    .trigger('mousedown', { button: 0 })
  
  cy.get(target)
    .trigger('mousemove')
    .trigger('mouseup', { force: true })
})

// Date picker helper
Cypress.Commands.add('selectDatePicker', (selector: string, date: string) => {
  cy.get(selector).click()
  
  // Parse date
  const [year, month, day] = date.split('-')
  
  // Navigate to correct month/year if needed
  cy.get('[data-cy=datepicker-year]').then($year => {
    if ($year.text() !== year) {
      cy.get('[data-cy=datepicker-year]').click()
      cy.get(`[data-cy=year-${year}]`).click()
    }
  })
  
  cy.get('[data-cy=datepicker-month]').then($month => {
    const monthIndex = parseInt(month) - 1
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    if ($month.text() !== monthNames[monthIndex]) {
      cy.get('[data-cy=datepicker-month]').click()
      cy.get(`[data-cy=month-${monthNames[monthIndex]}]`).click()
    }
  })
  
  // Click the day
  cy.get(`[data-cy=day-${parseInt(day)}]`).click()
})

// Notification helpers
Cypress.Commands.add('checkNotification', (message: string, type = 'success') => {
  cy.get(`[data-cy=notification-${type}]`)
    .should('be.visible')
    .and('contain', message)
})

Cypress.Commands.add('dismissNotification', () => {
  cy.get('[data-cy=notification-close]').click()
  cy.get('[data-cy^=notification]').should('not.exist')
})

// Custom assertion for checking element visibility in viewport
chai.Assertion.addMethod('inViewport', function () {
  const subject = this._obj
  
  cy.window().then(win => {
    const rect = subject[0].getBoundingClientRect()
    const windowHeight = win.innerHeight
    const windowWidth = win.innerWidth
    
    const inViewport = (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= windowHeight &&
      rect.right <= windowWidth
    )
    
    this.assert(
      inViewport,
      'expected #{this} to be in viewport',
      'expected #{this} not to be in viewport',
      this._obj
    )
  })
})

// Tab key navigation helper
Cypress.Commands.add('tab', { prevSubject: 'optional' }, (subject) => {
  if (subject) {
    cy.wrap(subject).trigger('keydown', { keyCode: 9, which: 9 })
  } else {
    cy.focused().trigger('keydown', { keyCode: 9, which: 9 })
  }
})

// Local storage helpers
Cypress.Commands.add('saveLocalStorage', () => {
  Object.keys(localStorage).forEach(key => {
    cy.task('save', { key, value: localStorage[key] })
  })
})

Cypress.Commands.add('restoreLocalStorage', () => {
  cy.task('getAll').then((storage: any) => {
    Object.keys(storage).forEach(key => {
      localStorage.setItem(key, storage[key])
    })
  })
})

// Export empty object to make this a module
export {}