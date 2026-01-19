/**
 * E2E Test: Code Editor Submission Flow
 * Tests the complete code editing, execution, and submission workflow
 * Task: T162
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath, verifyAuth } from './setup/authentication';

test.describe('Code Editor Submission Flow', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/code-editor');
    await verifyAuth(page, '');
  });

  test('Complete code editing and submission cycle', async ({ page }) => {
    // Step 1: Verify editor loads with default state
    await expect(page).toHaveURL(/\/code-editor$/);
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    // Step 2: Check editor toolbar is functional
    await expect(page.locator('[data-testid="editor-toolbar"]')).toBeVisible();
    await expect(page.locator('[data-testid="format-btn"]')).toBeVisible();
    await expect(page.locator('[data-testid="run-btn"]')).toBeVisible();
    await expect(page.locator('[data-testid="save-btn"]')).toBeVisible();
    await expect(page.locator('[data-testid="submit-btn"]')).toBeVisible();

    // Step 3: Write Python code
    const pythonCode = `class Student:
    def __init__(self, name, grade):
        self.name = name
        self.grade = grade

    def calculate_average(self, scores):
        return sum(scores) / len(scores)

    def is_passing(self):
        return self.grade >= 60

# Test the class
student = Student("Alice", 85)
scores = [90, 85, 92]
average = student.calculate_average(scores)
print(f"Student: {student.name}")
print(f"Average: {average}")
print(f"Passing: {student.is_passing()}")`;

    // Clear and write code
    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(pythonCode);

    // Step 4: Format code
    await page.click('[data-testid="format-btn"]');
    await expect(page.locator('[data-testid="format-indicator"]')).toContainText('Formatted');

    // Step 5: Run code and verify output
    await page.click('[data-testid="run-btn"]');

    // Wait for execution
    await expect(page.locator('[data-testid="execution-output"]')).toBeVisible();
    await expect(page.locator('[data-testid="execution-output"]')).toContainText('Alice');
    await expect(page.locator('[data-testid="execution-output"]')).toContainText('89.0');
    await expect(page.locator('[data-testid="execution-output"]')).toContainText('True');

    // Step 6: Save code (auto-save or manual)
    await page.click('[data-testid="save-btn"]');

    // Verify save confirmation
    await expect(page.locator('[data-testid="save-toast"]')).toContainText('Saved');
    await expect(page.locator('[data-testid="save-timestamp"]')).toBeVisible();

    // Step 7: Submit assignment
    await page.click('[data-testid="submit-btn"]');

    // Verify submission dialog
    await expect(page.locator('[data-testid="submission-dialog"]')).toBeVisible();
    await expect(page.locator('[data-testid="submission-confirm"]')).toBeVisible();

    // Confirm submission
    await page.click('[data-testid="submission-confirm"]');

    // Step 8: Verify submission success
    await expect(page.locator('[data-testid="submission-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="submission-id"]')).toBeVisible();

    // Step 9: Check for mastery feedback
    await expect(page.locator('[data-testid="mastery-feedback"]')).toBeVisible();
    const masteryChange = await page.locator('[data-testid="mastery-change"]').textContent();
    expect(masteryChange).toBeTruthy();
    expect(masteryChange).toMatch(/[\+\-]?\d+/); // Should show numeric change

    // Step 10: Navigate to dashboard to see updated stats
    await page.click('[data-testid="dashboard-nav"]');
    await expect(page).toHaveURL(/\/dashboard$/);

    // Step 11: Verify submission appears in activity feed
    await expect(page.locator('[data-testid="activity-feed"]')).toBeVisible();
    const activityItems = await page.locator('[data-testid="activity-item"]').count();
    expect(activityItems).toBeGreaterThan(0);
  });

  test('Batch submission workflow', async ({ page }) => {
    // Navigate to batch processing
    await page.goto('/batch');

    // Verify batch interface
    await expect(page).toHaveURL(/\/batch$/);
    await expect(page.locator('[data-testid="batch-uploader"]')).toBeVisible();

    // Upload multiple files
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([
      {
        name: 'exercise1.py',
        mimeType: 'text/x-python',
        buffer: Buffer.from('print("Exercise 1")'),
      },
      {
        name: 'exercise2.py',
        mimeType: 'text/x-python',
        buffer: Buffer.from('x = 10\nprint(x * 2)'),
      },
      {
        name: 'exercise3.py',
        mimeType: 'text/x-python',
        buffer: Buffer.from('def test():\n    return "Success"\nprint(test())'),
      },
    ]);

    // Verify files are uploaded
    await expect(page.locator('[data-testid="uploaded-file"]')).toHaveCount(3);

    // Start batch processing
    await page.click('[data-testid="start-batch-btn"]');

    // Monitor progress
    await expect(page.locator('[data-testid="batch-progress"]')).toBeVisible();

    // Wait for completion
    await expect(page.locator('[data-testid="batch-complete"]')).toBeVisible();

    // Check results
    await expect(page.locator('[data-testid="batch-results"]')).toBeVisible();

    const successCount = await page.locator('[data-testid="success-result"]').count();
    expect(successCount).toBeGreaterThan(0);
  });

  test('Code with syntax errors handling', async ({ page }) => {
    // Write code with intentional syntax error
    const invalidCode = `def broken_function():
    print("Start")
    return undefined_var  # Variable not defined
    extra line here without proper indentation`;

    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(invalidCode);

    // Try to run
    await page.click('[data-testid="run-btn"]');

    // Should show error in diagnostics
    await expect(page.locator('[data-testid="diagnostics-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="diagnostic-error"]')).toBeVisible();

    // Verify error message is helpful
    const errorText = await page.locator('[data-testid="diagnostic-error"]').textContent();
    expect(errorText).toBeTruthy();
    expect(errorText?.length).toBeGreaterThan(5);
  });

  test('Real-time collaboration indicators', async ({ page }) => {
    // Mock collaboration indicator (in real scenario, this would show other users)
    await page.goto('/code-editor');

    // Check for collaboration UI
    await expect(page.locator('[data-testid="collaboration-indicator"]')).toBeVisible();

    // Should show user count (even if it's just 1)
    const userCount = await page.locator('[data-testid="active-users"]').textContent();
    expect(userCount).toBeTruthy();

    // Check for cursors or presence indicators
    await expect(page.locator('[data-testid="user-presence"]')).toBeVisible();
  });

  test('Auto-save functionality', async ({ page }) => {
    await page.goto('/code-editor');

    // Type some code
    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.type('print("Auto-save test")');

    // Wait for auto-save (should trigger automatically)
    await page.waitForTimeout(3500); // Wait longer than auto-save interval

    // Check for auto-save indicator
    await expect(page.locator('[data-testid="auto-save-indicator"]')).toContainText('Auto-saved');

    // Verify timestamp updated
    const timestamp = await page.locator('[data-testid="last-saved-time"]').textContent();
    expect(timestamp).toBeTruthy();
  });
});

test.describe('Code Editor - Performance & Stress Testing', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Large file handling', async ({ page }) => {
    await page.goto('/code-editor');

    // Generate large code (1000+ lines)
    const largeCode = Array.from(
      { length: 1500 },
      (_, i) => `def function_${i}():\n    return ${i}\n\n`
    ).join('');

    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(largeCode);

    // Editor should still be responsive
    await expect(page.locator('[data-testid="monaco-editor"]')).toBeVisible();

    // Formatting should work (might take longer)
    await page.click('[data-testid="format-btn"]');
    await expect(page.locator('[data-testid="format-indicator"]')).toContainText('Formatted');

    // Running might take time but should eventually work
    await page.click('[data-testid="run-btn"]');
    await expect(page.locator('[data-testid="execution-output"], [data-testid="execution-error"]')).toBeVisible();
  });

  test('Rapid code changes', async ({ page }) => {
    await page.goto('/code-editor');

    // Perform rapid edits
    for (let i = 0; i < 10; i++) {
      await page.click('[data-testid="monaco-editor"]');
      await page.keyboard.type(`# Edit ${i}\n`);
      await page.waitForTimeout(100); // Small delay between edits
    }

    // Should handle rapid changes without crashing
    await expect(page.locator('[data-testid="monaco-editor"]')).toBeVisible();
  });
});

test.describe('Code Editor - Accessibility', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Keyboard navigation works throughout editor', async ({ page }) => {
    await page.goto('/code-editor');

    // Test tab navigation
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="editor-toolbar"]')).toBeFocused();

    // Navigate to run button with keyboard
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter'); // Should trigger run

    // Should show execution output
    await expect(page.locator('[data-testid="execution-output"]')).toBeVisible();
  });

  test('Screen reader compatibility', async ({ page }) => {
    await page.goto('/code-editor');

    // Check for ARIA labels
    await expect(page.locator('[aria-label="Code Editor"]')).toBeVisible();
    await expect(page.locator('[aria-label="Run Code"]')).toBeVisible();
    await expect(page.locator('[aria-label="Save Code"]')).toBeVisible();

    // Check for proper heading structure
    await expect(page.locator('h1, h2, h3')).toBeVisible();
  });
});