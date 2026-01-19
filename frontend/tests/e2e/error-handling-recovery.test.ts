/**
 * E2E Test: Error Handling and Recovery
 * Tests error scenarios and graceful recovery mechanisms
 * Task: T165
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath, verifyAuth } from './setup/authentication';

test.describe('Error Handling and Recovery - Authentication', () => {
  test('Invalid login credentials', async ({ page }) => {
    await page.goto('/login');

    // Enter invalid credentials
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    // Should show error message
    await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-error"]')).toContainText(/invalid|incorrect|failed/i);

    // Should remain on login page
    await expect(page).toHaveURL(/\/login$/);
  });

  test('Expired session recovery', async ({ page }) => {
    // Login normally
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test-student@example.com');
    await page.fill('input[name="password"]', 'TestStudent123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard$/);

    // Simulate session expiration
    await page.evaluate(() => {
      // Clear auth tokens
      localStorage.removeItem('auth_token');
      sessionStorage.removeItem('auth_token');
    });

    // Try to make authenticated request
    await page.click('[data-testid="refresh-dashboard-btn"]');

    // Should handle session expiration gracefully
    await expect(page.locator('[data-testid="session-expired-modal"]')).toBeVisible();

    // Should offer to re-login
    await expect(page.locator('[data-testid="relogin-btn"]')).toBeVisible();
    await page.click('[data-testid="relogin-btn"]');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login$/);
  });

  test('Network error during authentication', async ({ page }) => {
    // Intercept auth requests
    await page.route('**/api/auth/**', (route) => {
      route.abort('failed');
    });

    await page.goto('/login');

    // Attempt login
    await page.fill('input[name="email"]', 'test-student@example.com');
    await page.fill('input[name="password"]', 'TestStudent123!');
    await page.click('button[type="submit"]');

    // Should show network error
    await expect(page.locator('[data-testid="network-error"]')).toBeVisible();

    // Should offer retry
    await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();

    // Remove interception and retry
    await page.unroute('**/api/auth/**');
    await page.click('[data-testid="retry-btn"]');

    // Should succeed now
    await expect(page).toHaveURL(/\/dashboard$/);
  });
});

test.describe('Error Handling and Recovery - API', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('API error during data fetching', async ({ page }) => {
    // Intercept dashboard API calls
    await page.route('**/api/analytics/**', (route) => {
      route.abort('failed');
    });

    await page.goto('/dashboard');

    // Should show error state
    await expect(page.locator('[data-testid="dashboard-error"]')).toBeVisible();

    // Should show retry button
    await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();

    // Remove interception
    await page.unroute('**/api/analytics/**');

    // Retry
    await page.click('[data-testid="retry-btn"]');

    // Should load successfully
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });

  test('Partial data failure (some APIs fail, some succeed)', async ({ page }) => {
    // Intercept only specific API calls
    await page.route('**/api/recommendations/**', (route) => {
      route.abort('failed');
    });

    await page.goto('/dashboard');

    // Some data should load (master score, activity feed)
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
    await expect(page.locator('[data-testid="activity-feed"]')).toBeVisible();

    // Recommendations section should show error
    await expect(page.locator('[data-testid="recommendations-error"]')).toBeVisible();

    // Rest of dashboard should be functional
    await page.click('[data-testid="refresh-dashboard-btn"]');
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });

  test('Rate limiting response', async ({ page }) => {
    // Mock rate limiting (429 response)
    await page.route('**/api/**', (route) => {
      if (route.request().url().includes('/api/')) {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Rate limit exceeded',
            retryAfter: 1,
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.goto('/dashboard');

    // Should show rate limit message
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();

    // Should show retry countdown
    await expect(page.locator('[data-testid="retry-countdown"]')).toBeVisible();

    // After countdown, should auto-retry
    await page.waitForTimeout(2000);

    // Remove interception
    await page.unroute('**/api/**');

    // Should eventually load
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });
});

test.describe('Error Handling and Recovery - Code Execution', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Code execution timeout', async ({ page }) => {
    await page.goto('/code-editor');

    // Write infinite loop code
    const infiniteCode = `while True:
    pass  # Infinite loop`;

    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(infiniteCode);

    // Mock execution timeout
    await page.route('**/api/code/execute', (route) => {
      route.fulfill({
        status: 408, // Request Timeout
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Execution timeout',
          message: 'Code execution took too long',
        }),
      });
    });

    await page.click('[data-testid="run-btn"]');

    // Should show timeout error
    await expect(page.locator('[data-testid="execution-timeout"]')).toBeVisible();

    // Should show stop execution button
    await expect(page.locator('[data-testid="stop-execution-btn"]')).toBeVisible();

    // Remove interception
    await page.unroute('**/api/code/execute');
  });

  test('Code compilation errors', async ({ page }) => {
    await page.goto('/code-editor');

    // Write syntactically invalid code
    const invalidCode = `def broken():
    print("Hello"
    return "world"  # Missing closing parenthesis`;

    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(invalidCode);

    // Mock compilation error response
    await page.route('**/api/code/execute', (route) => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Compilation failed',
          details: ['SyntaxError: EOL while scanning string literal at line 2'],
          line: 2,
          column: 15,
        }),
      });
    });

    await page.click('[data-testid="run-btn"]');

    // Should show compilation error
    await expect(page.locator('[data-testid="compilation-error"]')).toBeVisible();

    // Should highlight the error line
    await expect(page.locator('[data-testid="error-line-2"]')).toBeVisible();

    // Should show error details
    await expect(page.locator('[data-testid="error-message"]')).toContainText('SyntaxError');

    await page.unroute('**/api/code/execute');
  });

  test('Code execution runtime error', async ({ page }) => {
    await page.goto('/code-editor');

    // Write code that causes runtime error
    const runtimeError = `def divide(a, b):
    return a / b

result = divide(10, 0)  # Division by zero`;

    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(runtimeError);

    // Mock runtime error response
    await page.route('**/api/code/execute', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Runtime error',
          details: ['ZeroDivisionError: division by zero'],
          traceback: [
            'File "code.py", line 4, in <module>',
            'result = divide(10, 0)',
            'File "code.py", line 2, in divide',
            'return a / b',
          ],
        }),
      });
    });

    await page.click('[data-testid="run-btn"]');

    // Should show runtime error
    await expect(page.locator('[data-testid="runtime-error"]')).toBeVisible();

    // Should show traceback
    await expect(page.locator('[data-testid="traceback"]')).toBeVisible();

    // Should highlight error line
    await expect(page.locator('[data-testid="error-line"]')).toBeVisible();

    await page.unroute('**/api/code/execute');
  });
});

test.describe('Error Handling and Recovery - Real-time Features', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('SSE connection failure and reconnection', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate SSE connection failure
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('sse-error', { detail: { message: 'Connection failed' } }));
    });

    // Should show connection error
    await expect(page.locator('[data-testid="sse-connection-error"]')).toBeVisible();

    // Should show reconnection attempts
    await expect(page.locator('[data-testid="reconnection-attempts"]')).toContainText('1');

    // Simulate successful reconnection
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('sse-reconnect-success'));
    });

    // Should show connected status
    await expect(page.locator('[data-testid="sse-status"]')).toContainText('connected');
  });

  test('Event processing error handling', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate malformed event
    await page.evaluate(() => {
      const malformedEvent = {
        // Missing required fields
        type: 'incomplete-event',
      };

      try {
        window.dispatchEvent(new CustomEvent('sse-event', { detail: malformedEvent }));
      } catch (error) {
        // Error should be caught and handled gracefully
        window.dispatchEvent(
          new CustomEvent('sse-processing-error', { detail: { error: error.message } })
        );
      }
    });

    // Should show error boundary or fallback UI
    await expect(page.locator('[data-testid="event-processing-error"]')).toBeVisible();

    // Should not break the rest of the UI
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('High event volume backpressure', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate high volume of events
    await page.evaluate(() => {
      const events = Array.from({ length: 200 }, (_, i) => ({
        id: `flood-event-${i}`,
        type: 'mastery-updated',
        topic: 'mastery-updated',
        data: { score: Math.random() },
        priority: 'normal',
        timestamp: new Date().toISOString(),
      }));

      events.forEach(event => {
        window.dispatchEvent(new CustomEvent('sse-event', { detail: event }));
      });
    });

    // Should handle flood gracefully without crashing
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    // Event queue should be limited
    const eventCount = await page.locator('[data-testid="event-item"]').count();
    expect(eventCount).toBeLessThanOrEqual(50); // Should have reasonable limit

    // UI should remain responsive
    await page.click('[data-testid="refresh-dashboard-btn"]');
    await expect(page.locator('[data-testid="refresh-indicator"]')).toBeVisible();
  });
});

test.describe('Error Handling and Recovery - UI/UX', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Graceful degradation when JavaScript fails', async ({ page }) => {
    await page.goto('/dashboard');

    // Disable JavaScript execution for this test
    await page.addInitScript(() => {
      // Override fetch to simulate JS failure
      window.fetch = () => Promise.reject(new Error('Simulated JS failure'));
    });

    await page.reload();

    // Should show degraded but functional UI
    await expect(page.locator('[data-testid="degraded-ui-notice"]')).toBeVisible();

    // Basic navigation should still work
    await expect(page.locator('[data-testid="dashboard-nav"]')).toBeVisible();

    // Should still show essential data
    await expect(page.locator('[data-testid="user-greeting"]')).toBeVisible();
  });

  test('Error boundary display and recovery', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate component error
    await page.evaluate(() => {
      // Trigger error in a component
      const component = document.querySelector('[data-testid="performance-chart"]');
      if (component) {
        component.setAttribute('data-error', 'true');
      }
    });

    // Should show error boundary
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();

    // Should offer recovery options
    await expect(page.locator('[data-testid="reload-component-btn"]')).toBeVisible();
    await expect(page.locator('[data-testid="ignore-error-btn"]')).toBeVisible();

    // Test recovery
    await page.click('[data-testid="reload-component-btn"]');

    // Should attempt to reload component
    await expect(page.locator('[data-testid="component-loading"]')).toBeVisible();
  });

  test('Offline mode handling', async ({ page }) => {
    // Simulate offline network condition
    await page.context().setOffline(true);

    await page.goto('/dashboard');

    // Should show offline indicator
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();

    // Should show cached data
    await expect(page.locator('[data-testid="cached-data-indicator"]')).toBeVisible();

    // Should show offline-friendly UI
    await expect(page.locator('[data-testid="offline-notice"]')).toBeVisible();

    // Bring back online
    await page.context().setOffline(false);

    // Should sync automatically
    await expect(page.locator('[data-testid="sync-complete"]')).toBeVisible();
  });

  test('Cross-browser compatibility errors', async ({ page }) => {
    // Test different browser-specific issues
    await page.goto('/code-editor');

    // Simulate browser-specific API failure
    await page.addInitScript(() => {
      // Remove a browser API to simulate compatibility issue
      delete (window as any).TextEncoder;
    });

    await page.reload();

    // Should show compatibility error
    await expect(page.locator('[data-testid="browser-compatibility-error"]')).toBeVisible();

    // Should suggest workaround or fallback
    await expect(page.locator('[data-testid="compatibility-workaround"]')).toBeVisible();
  });
});

test.describe('Error Handling and Recovery - Performance', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Memory leak prevention under error conditions', async ({ page }) => {
    await page.goto('/dashboard');

    // Monitor initial memory
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Trigger multiple errors
    for (let i = 0; i < 20; i++) {
      await page.route('**/api/analytics/**', (route) => {
        route.abort('failed');
      });

      await page.click('[data-testid="refresh-dashboard-btn"]');
      await page.waitForTimeout(100);

      await page.unroute('**/api/analytics/**');
      await page.waitForTimeout(100);
    }

    // Check final memory
    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Memory increase should be reasonable (not a leak)
    if (initialMemory > 0 && finalMemory > 0) {
      expect(finalMemory).toBeLessThan(initialMemory * 2); // Allow 2x increase for 20 errors
    }

    // UI should still be responsive
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('Error recovery time', async ({ page }) => {
    await page.goto('/dashboard');

    // Measure time to recover from error
    const startTime = Date.now();

    // Simulate network error
    await page.route('**/api/analytics/**', (route) => {
      route.abort('failed');
    });

    await page.click('[data-testid="refresh-dashboard-btn"]');
    await expect(page.locator('[data-testid="dashboard-error"]')).toBeVisible();

    // Remove error and retry
    await page.unroute('**/api/analytics/**');
    await page.click('[data-testid="retry-btn"]');

    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();

    const recoveryTime = Date.now() - startTime;

    // Recovery should be reasonably fast (< 10 seconds)
    expect(recoveryTime).toBeLessThan(10000);
  });
});