/**
 * Playwright Configuration for E2E Testing
 * Task: T160
 *
 * Last Updated: 2026-01-15
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  // Look for test files in the tests/e2e directory
  testDir: './tests/e2e',

  // Maximum time one test can run for
  timeout: 30 * 1000,

  // Expect a test to take up to 5 seconds
  expect: {
    timeout: 5000,
  },

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI to avoid resource contention
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use. See https://playwright.dev/docs/test-reporters
  reporter: [
    ['html', { open: 'never' }], // HTML report
    ['json', { outputFile: 'test-results/e2e-results.json' }], // JSON report for CI
    ['list', { printSteps: true }], // Console output
  ],

  // Shared settings for all projects
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',

    // Collect trace when failing. See https://playwright.dev/docs/trace-viewer
    trace: 'on-first-retry',

    // Collect video on first retry
    video: 'on-first-retry',

    // Capture screenshot on failure
    screenshot: 'only-on-failure',

    // Record har for network analysis
    har: process.env.CI ? undefined : 'test-results/e2e-network.har',

    // Time to wait for page actions
    actionTimeout: 10000,

    // Navigation timeout
    navigationTimeout: 30000,

    // Accept insecure certs for local development
    ignoreHTTPSErrors: process.env.NODE_ENV === 'development',

    // Enable mobile viewport for testing
    viewport: { width: 1280, height: 720 },

    // User agent
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Custom device settings
        viewport: { width: 1920, height: 1080 },
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 },
      },
      // Skip Firefox on CI if needed
      retry: process.env.CI ? 0 : 1,
    },

    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 },
      },
    },

    // Mobile projects
    {
      name: 'Mobile Chrome',
      use: {
        ...devices['Pixel 5'],
      },
    },

    {
      name: 'Mobile Safari',
      use: {
        ...devices['iPhone 14'],
      },
    },
  ],

  // Local dev server configuration
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
    env: {
      NODE_ENV: 'test',
      PORT: '3000',
    },
  },

  // Additional configurations
  outputDir: 'test-results/e2e',

  // Metadata
  metadata: {
    platform: process.platform,
    nodeVersion: process.version,
    commitHash: process.env.GIT_COMMIT || 'unknown',
    timestamp: new Date().toISOString(),
  },
});
