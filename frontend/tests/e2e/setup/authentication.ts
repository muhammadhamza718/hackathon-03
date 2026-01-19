/**
 * Playwright Authentication Setup
 * Provides authenticated context for E2E tests
 * Task: T160
 *
 * Last Updated: 2026-01-15
 */

import { test as setup } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// Define paths for authenticated storage
const STORAGE_STATE_PATH = path.join(__dirname, '../.auth/storage-state.json');
const USER_CREDENTIALS_PATH = path.join(__dirname, '../.auth/user-credentials.json');

// Test user credentials (these should match your test database)
export const TEST_USERS = {
  student: {
    email: 'test-student@example.com',
    password: 'TestStudent123!',
    username: 'test_student',
    id: 'test-student-123',
  },
  advancedStudent: {
    email: 'advanced-student@example.com',
    password: 'AdvancedStudent123!',
    username: 'advanced_student',
    id: 'advanced-student-456',
  },
  admin: {
    email: 'admin@example.com',
    password: 'Admin123!',
    username: 'admin',
    id: 'admin-789',
  },
};

/**
 * Helper to create authentication state for a specific user role
 */
async function createAuthState(
  page: any,
  credentials: { email: string; password: string },
  baseUrl: string
): Promise<void> {
  // Navigate to login page
  await page.goto(`${baseUrl}/login`);

  // Fill login form
  await page.fill('input[name="email"]', credentials.email);
  await page.fill('input[name="password"]', credentials.password);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for navigation to dashboard
  await page.waitForURL(`${baseUrl}/dashboard`, { timeout: 10000 });

  // Wait for any async operations to complete
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Extra stability
}

/**
 * Setup authenticated state for student user
 */
setup('authenticate as student', async ({ page }) => {
  const baseUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';

  await createAuthState(page, TEST_USERS.student, baseUrl);

  // Save authenticated state
  await page.context().storageState({ path: STORAGE_STATE_PATH });

  // Save user credentials for reference
  fs.writeFileSync(
    USER_CREDENTIALS_PATH,
    JSON.stringify({
      role: 'student',
      user: TEST_USERS.student,
      timestamp: new Date().toISOString(),
    })
  );
});

/**
 * Setup authenticated state for advanced student user
 */
setup('authenticate as advanced student', async ({ page }) => {
  const baseUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';

  await createAuthState(page, TEST_USERS.advancedStudent, baseUrl);

  // Save authenticated state for advanced user
  const advancedStoragePath = path.join(__dirname, '../.auth/storage-state-advanced.json');
  await page.context().storageState({ path: advancedStoragePath });

  // Save credentials
  fs.writeFileSync(
    path.join(__dirname, '../.auth/user-credentials-advanced.json'),
    JSON.stringify({
      role: 'advanced-student',
      user: TEST_USERS.advancedStudent,
      timestamp: new Date().toISOString(),
    })
  );
});

/**
 * Setup authenticated state for admin user
 */
setup('authenticate as admin', async ({ page }) => {
  const baseUrl = process.env.E2E_BASE_URL || 'http://localhost:3000';

  await createAuthState(page, TEST_USERS.admin, baseUrl);

  // Save authenticated state for admin
  const adminStoragePath = path.join(__dirname, '../.auth/storage-state-admin.json');
  await page.context().storageState({ path: adminStoragePath });

  // Save credentials
  fs.writeFileSync(
    path.join(__dirname, '../.auth/user-credentials-admin.json'),
    JSON.stringify({
      role: 'admin',
      user: TEST_USERS.admin,
      timestamp: new Date().toISOString(),
    })
  );
});

/**
 * Helper function to get authenticated storage state for tests
 */
export function getAuthStoragePath(role: 'student' | 'advanced-student' | 'admin' = 'student'): string {
  const baseDir = path.join(__dirname, '../.auth');

  switch (role) {
    case 'advanced-student':
      return path.join(baseDir, 'storage-state-advanced.json');
    case 'admin':
      return path.join(baseDir, 'storage-state-admin.json');
    default:
      return path.join(baseDir, 'storage-state.json');
  }
}

/**
 * Helper to verify authentication was successful
 */
export async function verifyAuth(page: any, baseUrl: string): Promise<void> {
  // Check that we're on a protected page
  await page.waitForURL(`${baseUrl}/dashboard`, { timeout: 10000 });

  // Verify user avatar or profile element exists
  await page.waitForSelector('[data-testid="user-avatar"]', { timeout: 5000 });

  // Verify logout button exists
  await page.waitForSelector('[data-testid="logout-button"]', { timeout: 5000 });
}

/**
 * Helper to perform logout
 */
export async function performLogout(page: any): Promise<void> {
  // Click user avatar or profile menu
  await page.click('[data-testid="user-avatar"]');

  // Click logout button
  await page.click('[data-testid="logout-button"]');

  // Wait for navigation to login page
  await page.waitForURL(/\/login$/, { timeout: 5000 });
}

/**
 * Helper to clear all authentication state
 */
export function clearAuthState(): void {
  const authDir = path.join(__dirname, '../.auth');

  if (fs.existsSync(authDir)) {
    fs.rmSync(authDir, { recursive: true, force: true });
  }

  // Recreate directory
  fs.mkdirSync(authDir, { recursive: true });
}

/**
 * Helper to create test user context
 */
export function createTestContext(
  role: 'student' | 'advanced-student' | 'admin' = 'student'
): { storageState: string } {
  return {
    storageState: getAuthStoragePath(role),
  };
}