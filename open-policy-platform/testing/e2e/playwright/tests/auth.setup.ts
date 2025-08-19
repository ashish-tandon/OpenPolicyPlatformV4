import { test as setup } from '@playwright/test'

const authFile = 'playwright/.auth/user.json'
const adminAuthFile = 'playwright/.auth/admin.json'

setup('authenticate as user', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[data-cy=email-input]', process.env.TEST_USER_EMAIL || 'test@openpolicy.local')
  await page.fill('[data-cy=password-input]', process.env.TEST_USER_PASSWORD || 'testpassword123')
  await page.click('[data-cy=login-button]')
  
  // Wait for redirect
  await page.waitForURL('/')
  
  // Save authentication state
  await page.context().storageState({ path: authFile })
})

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/admin/login')
  await page.fill('[data-cy=email-input]', process.env.ADMIN_USER_EMAIL || 'admin@openpolicy.local')
  await page.fill('[data-cy=password-input]', process.env.ADMIN_USER_PASSWORD || 'adminpassword123')
  await page.click('[data-cy=login-button]')
  
  // Wait for redirect
  await page.waitForURL('/admin/dashboard')
  
  // Save authentication state
  await page.context().storageState({ path: adminAuthFile })
})