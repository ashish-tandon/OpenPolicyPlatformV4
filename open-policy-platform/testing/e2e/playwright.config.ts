import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './playwright/tests',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'results/junit.xml' }],
    ['json', { outputFile: 'results/report.json' }]
  ],
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Authentication state
    storageState: 'playwright/.auth/user.json',
  },

  projects: [
    // Setup project for authentication
    { 
      name: 'setup', 
      testMatch: /.*\.setup\.ts/ 
    },
    
    // Desktop browsers
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup'],
    },

    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup'],
    },

    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup'],
    },

    // Mobile browsers
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
      dependencies: ['setup'],
    },
    
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
      dependencies: ['setup'],
    },

    // Tablet
    {
      name: 'iPad',
      use: { ...devices['iPad Pro'] },
      dependencies: ['setup'],
    },

    // Branded browsers
    {
      name: 'Microsoft Edge',
      use: { 
        ...devices['Desktop Edge'], 
        channel: 'msedge' 
      },
      dependencies: ['setup'],
    },
    
    {
      name: 'Google Chrome',
      use: { 
        ...devices['Desktop Chrome'], 
        channel: 'chrome' 
      },
      dependencies: ['setup'],
    },
  ],

  // Run local dev server before starting tests
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
})