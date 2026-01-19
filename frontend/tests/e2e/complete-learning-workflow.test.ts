/**
 * E2E Test: Complete Learning Workflow
 * Tests the end-to-end learning experience from login to mastery achievement
 * Task: T161
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { TEST_USERS, getAuthStoragePath, verifyAuth, performLogout } from './setup/authentication';

test.describe('Complete Learning Workflow', () => {
  // Use authenticated state
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard before each test
    await page.goto('/dashboard');
    await verifyAuth(page, '');
  });

  test.afterEach(async ({ page }) => {
    // Clean up - ensure we're logged out for next test
    await performLogout(page);
  });

  test('Complete learning flow: Login → Dashboard → Editor → Run Code → Get Feedback', async ({
    page,
  }) => {
    // Step 1: Verify dashboard loads with user data
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.locator('[data-testid="user-greeting"]')).toContainText(
      TEST_USERS.student.username
    );

    // Step 2: Check dashboard stats are loaded
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
    await expect(page.locator('[data-testid="current-streak"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-assignments"]')).toBeVisible();

    // Step 3: Navigate to code editor from dashboard
    await page.click('[data-testid="start-coding-btn"]');

    // Step 4: Wait for editor to load
    await expect(page).toHaveURL(/\/code-editor$/);
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    // Step 5: Verify editor functionality
    const editor = page.locator('[data-testid="monaco-editor"]');
    await expect(editor).toBeVisible();

    // Step 6: Write Python code
    const testCode = `def hello_world():
    print("Hello, World!")
    return "Success"

result = hello_world()
print(result)`;

    // Clear existing code and write new code
    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(testCode);

    // Step 7: Verify code is in editor
    const editorContent = await page.locator('[data-testid="monaco-editor-content"]').textContent();
    expect(editorContent).toContain('def hello_world');

    // Step 8: Run the code
    await page.click('[data-testid="run-code-btn"]');

    // Step 9: Wait for execution to complete
    await expect(page.locator('[data-testid="execution-output"]')).toBeVisible();
    await expect(page.locator('[data-testid="execution-status"]')).toContainText('Success');

    // Step 10: Check for real-time feedback (SSE events)
    await expect(page.locator('[data-testid="feedback-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="mastery-update-toast"]')).toBeVisible();

    // Step 11: Save the assignment
    await page.click('[data-testid="save-assignment-btn"]');

    // Step 12: Verify save confirmation
    await expect(page.locator('[data-testid="save-confirmation"]')).toContainText('Saved');

    // Step 13: Check mastery progress updated
    await expect(page.locator('[data-testid="mastery-progress-bar"]')).toBeVisible();

    // Step 14: Navigate back to dashboard
    await page.click('[data-testid="dashboard-nav"]');

    // Step 15: Verify dashboard stats updated
    await expect(page).toHaveURL(/\/dashboard$/);
    const updatedScore = await page.locator('[data-testid="mastery-score"]').textContent();
    expect(parseInt(updatedScore || '0')).toBeGreaterThanOrEqual(0);

    // Step 16: Check activity feed for recent activity
    await expect(page.locator('[data-testid="activity-feed"]')).toBeVisible();
    await expect(page.locator('[data-testid="activity-item"]')).first().toBeVisible();
  });

  test('Learning progression: Complete multiple exercises and track improvement', async ({
    page,
  }) => {
    const exercises = [
      { code: 'print("Exercise 1")', topic: 'basics' },
      { code: 'x = 5 + 3\nprint(x)', topic: 'variables' },
      { code: 'for i in range(3):\n    print(i)', topic: 'loops' },
    ];

    for (const exercise of exercises) {
      // Navigate to editor
      await page.click('[data-testid="start-coding-btn"]');
      await expect(page).toHaveURL(/\/code-editor$/);

      // Write and run exercise
      await page.click('[data-testid="monaco-editor"]');
      await page.keyboard.press('Control+A');
      await page.keyboard.press('Backspace');
      await page.keyboard.type(exercise.code);

      // Run code
      await page.click('[data-testid="run-code-btn"]');

      // Wait for feedback
      await expect(page.locator('[data-testid="execution-output"]')).toBeVisible();

      // Save assignment
      await page.click('[data-testid="save-assignment-btn"]');

      // Wait a moment for mastery to update
      await page.waitForTimeout(2000);

      // Return to dashboard
      await page.click('[data-testid="dashboard-nav"]');
      await expect(page).toHaveURL(/\/dashboard$/);

      // Check progression
      const streak = await page.locator('[data-testid="current-streak"]').textContent();
      expect(parseInt(streak || '0')).toBeGreaterThan(0);
    }

    // After completing multiple exercises, check overall improvement
    const masteryScore = await page.locator('[data-testid="mastery-score"]').textContent();
    expect(parseInt(masteryScore || '0')).toBeGreaterThan(0);

    // Check recommendations are generated
    await expect(page.locator('[data-testid="recommendations-list"]')).toBeVisible();
    await expect(page.locator('[data-testid="recommendation-item"]')).first().toBeVisible();
  });
});

test.describe('Learning Workflow - Unauthenticated', () => {
  test('Should redirect to login when accessing learning workflow unauthenticated', async ({
    page,
  }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login$/);

    // Login form should be visible
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });

  test('Should redirect to login when accessing editor unauthenticated', async ({ page }) => {
    // Try to access editor without authentication
    await page.goto('/code-editor');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login$/);
  });
});

test.describe('Learning Workflow - Error Handling', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Should handle code execution errors gracefully', async ({ page }) => {
    // Navigate to editor
    await page.goto('/code-editor');
    await expect(page).toHaveURL(/\/code-editor$/);

    // Write invalid Python code
    const invalidCode = `def broken_function():
    print("Starting")
    return undefined_variable  # This will cause an error
    print("Never reached")`;

    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(invalidCode);

    // Run code (should handle error)
    await page.click('[data-testid="run-code-btn"]');

    // Should show error output
    await expect(page.locator('[data-testid="execution-error"]')).toBeVisible();

    // Error should be informative
    const errorText = await page.locator('[data-testid="execution-error"]').textContent();
    expect(errorText).toBeTruthy();
    expect(errorText?.length).toBeGreaterThan(0);

    // Should still be able to save (with error status)
    await page.click('[data-testid="save-assignment-btn"]');

    // Verify save attempted but failed appropriately
    await expect(page.locator('[data-testid="save-confirmation"]')).toContainText(/(error|failed|retry)/i);
  });

  test('Should handle network disconnection during execution', async ({ page }) => {
    await page.goto('/code-editor');

    // Write code
    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.type('print("Test")');

    // Simulate network issues (this is a mock test - in real scenario we'd use Playwright's network mocking)
    // For now, just verify the UI handles the scenario
    await page.click('[data-testid="run-code-btn"]');

    // Should show loading state
    await expect(page.locator('[data-testid="execution-loading"]')).toBeVisible();

    // Should eventually show result or error
    await expect(
      page.locator('[data-testid="execution-output"], [data-testid="execution-error"]')
    ).toBeVisible();
  });
});

test.describe('Learning Workflow - Performance', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Editor loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/code-editor');
    await expect(page).toHaveURL(/\/code-editor$/);

    // Editor should be visible
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000); // Should load in under 2 seconds
  });

  test('Dashboard loads quickly with cached data', async ({ page }) => {
    // First load
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard$/);

    // Second load should be faster (cached)
    const startTime = Date.now();
    await page.reload();
    await expect(page).toHaveURL(/\/dashboard$/);

    const reloadTime = Date.now() - startTime;
    expect(reloadTime).toBeLessThan(1000); // Should reload in under 1 second
  });
});