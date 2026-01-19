/**
 * E2E Test: Real-time Feedback Display
 * Tests SSE real-time feedback and event processing
 * Task: T163
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath, verifyAuth } from './setup/authentication';

test.describe('Real-time Feedback Display', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await verifyAuth(page, '');
  });

  test('SSE connection establishes and displays real-time events', async ({ page }) => {
    // Navigate to dashboard where real-time events are displayed
    await expect(page).toHaveURL(/\/dashboard$/);

    // Check for SSE connection indicator
    await expect(page.locator('[data-testid="sse-connection-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="sse-status"]')).toContainText(/connected|connecting/i);

    // Verify event feed is present
    await expect(page.locator('[data-testid="event-feed"]')).toBeVisible();

    // Mock real-time event (in real scenario, this would come from Dapr backend)
    // For this test, we'll simulate receiving an event
    await page.evaluate(() => {
      const event = {
        id: 'test-event-123',
        type: 'mastery-update',
        topic: 'mastery-updated',
        data: {
          studentId: 'test-student-123',
          score: 0.95,
          topic: 'python-functions',
          improvement: '+5%',
        },
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      // Simulate event processing (in real app, this would be handled by SSE client)
      window.dispatchEvent(
        new CustomEvent('sse-event', { detail: event })
      );
    });

    // Verify event appears in UI
    await expect(page.locator('[data-testid="event-item"]')).toBeVisible();
    await expect(page.locator('[data-testid="event-item"]')).toContainText('mastery-updated');

    // Check notification toast
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="notification-toast"]')).toContainText('95%');
  });

  test('Event filtering and prioritization', async ({ page }) => {
    await page.goto('/dashboard');

    // Navigate to event preferences
    await page.click('[data-testid="event-settings-btn"]');
    await expect(page).toHaveURL(/\/events\/settings$/);

    // Configure event filters
    await page.check('[data-testid="filter-mastery-updates"]');
    await page.check('[data-testid="filter-recommendations"]');
    await page.uncheck('[data-testid="filter-progress-updates"]');

    // Save preferences
    await page.click('[data-testid="save-event-preferences"]');

    // Navigate back to dashboard
    await page.goto('/dashboard');

    // Simulate different event types
    await page.evaluate(() => {
      const events = [
        {
          id: 'evt-1',
          type: 'mastery-updated',
          topic: 'mastery-updated',
          data: { score: 0.9 },
          priority: 'high',
          timestamp: new Date().toISOString(),
        },
        {
          id: 'evt-2',
          type: 'recommendation',
          topic: 'recommendation',
          data: { title: 'Practice Exercise' },
          priority: 'normal',
          timestamp: new Date().toISOString(),
        },
        {
          id: 'evt-3',
          type: 'progress',
          topic: 'progress',
          data: { progress: 50 },
          priority: 'low',
          timestamp: new Date().toISOString(),
        },
      ];

      events.forEach(event => {
        window.dispatchEvent(new CustomEvent('sse-event', { detail: event }));
      });
    });

    // Mastery and recommendation events should appear
    await expect(page.locator('[data-testid="event-item"]')).toHaveCount(2);

    // Progress event should not appear (filtered out)
    const allEvents = await page.locator('[data-testid="event-item"]').allTextContents();
    allEvents.forEach(text => {
      expect(text).not.toContain('progress');
    });
  });

  test('Real-time feedback during code execution', async ({ page }) => {
    await page.goto('/code-editor');

    // Write code
    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.type('print("Real-time test")');

    // Start execution with feedback monitoring
    await page.click('[data-testid="run-btn"]');

    // Should show real-time execution feedback
    await expect(page.locator('[data-testid="execution-feedback"]')).toBeVisible();

    // Check for live status updates
    await expect(page.locator('[data-testid="execution-status"]')).toContainText(/running|completed|error/i);

    // Verify real-time logs appear as execution progresses
    const logCount = await page.locator('[data-testid="execution-log"]').count();
    expect(logCount).toBeGreaterThan(0);

    // Final output should appear
    await expect(page.lociator('[data-testid="execution-output"]')).toBeVisible();
  });

  test('Event priority styling and notifications', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate high priority event
    await page.evaluate(() => {
      const highPriorityEvent = {
        id: 'high-priority-123',
        type: 'system-alert',
        topic: 'system-alert',
        data: { message: 'System maintenance in 30 minutes' },
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: highPriorityEvent }));
    });

    // Check for high priority styling
    const highPriorityElement = page.locator('[data-testid="event-item-high-priority"]');
    await expect(highPriorityElement).toBeVisible();

    // Check for persistent notification (toast)
    await expect(page.locator('[data-testid="persistent-notification"]')).toBeVisible();

    // Simulate normal priority event
    await page.evaluate(() => {
      const normalEvent = {
        id: 'normal-123',
        type: 'mastery-update',
        topic: 'mastery-updated',
        data: { score: 0.85 },
        priority: 'normal',
        timestamp: new Date().toISOString(),
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: normalEvent }));
    });

    // Normal events should appear with different styling
    await expect(page.locator('[data-testid="event-item-normal-priority"]')).toBeVisible();
  });

  test('Event acknowledgment and dismissal', async ({ page }) => {
    await page.goto('/dashboard');

    // Create a test event
    await page.evaluate(() => {
      const event = {
        id: 'ack-test-123',
        type: 'info',
        topic: 'info',
        data: { message: 'Test information message' },
        priority: 'normal',
        timestamp: new Date().toISOString(),
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: event }));
    });

    // Verify event appears
    const eventItem = page.locator('[data-testid="event-item"]').first();
    await expect(eventItem).toBeVisible();

    // Click dismiss button
    await eventItem.locator('[data-testid="dismiss-event-btn"]').click();

    // Event should disappear
    await expect(page.locator('[data-testid="event-item"]')).toHaveCount(0);

    // Check for acknowledgment callback (if implemented)
    // This would verify the SSE acknowledgment was sent
  });

  test('Connection health monitoring', async ({ page }) => {
    await page.goto('/dashboard');

    // Check connection health indicator
    await expect(page.locator('[data-testid="connection-health"]')).toBeVisible();

    // Simulate connection issues
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('sse-error', { detail: { message: 'Connection lost' } }));
    });

    // Should show reconnection attempt
    await expect(page.locator('[data-testid="reconnection-attempt"]')).toBeVisible();

    // Simulate reconnection success
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('sse-reconnect-success'));
    });

    // Should show connected status
    await expect(page.locator('[data-testid="sse-status"]')).toContainText('connected');
  });

  test('Event history and replay', async ({ page }) => {
    await page.goto('/dashboard');

    // Add some events to history
    await page.evaluate(() => {
      const events = Array.from({ length: 5 }, (_, i) => ({
        id: `history-${i}`,
        type: 'mastery-updated',
        topic: 'mastery-updated',
        data: { score: 0.8 + i * 0.02 },
        priority: 'normal',
        timestamp: new Date(Date.now() - (5 - i) * 60000).toISOString(), // Past events
      }));

      events.forEach(event => {
        window.dispatchEvent(new CustomEvent('sse-event', { detail: event }));
      });
    });

    // Check event history section
    await expect(page.locator('[data-testid="event-history"]')).toBeVisible();

    // Should show multiple historical events
    const historyItems = await page.locator('[data-testid="history-item"]').count();
    expect(historyItems).toBeGreaterThan(0);

    // Should allow viewing older events
    await page.click('[data-testid="show-more-events"]');
    await expect(page.locator('[data-testid="event-history-expanded"]')).toBeVisible();
  });
});

test.describe('Real-time Feedback - Error Scenarios', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Handles malformed events gracefully', async ({ page }) => {
    await page.goto('/dashboard');

    // Send malformed event
    await page.evaluate(() => {
      const malformedEvent = {
        // Missing required fields
        type: 'incomplete-event',
        // No id, no data
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: malformedEvent }));
    });

    // Should not crash the UI
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    // Should show error boundary or fallback UI
    await expect(page.locator('[data-testid="event-error-boundary"]')).toBeVisible();
  });

  test('Handles connection timeout', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate connection timeout
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('sse-timeout'));
    });

    // Should show timeout message
    await expect(page.locator('[data-testid="connection-timeout"]')).toBeVisible();

    // Should offer retry option
    await expect(page.locator('[data-testid="retry-connection-btn"]')).toBeVisible();
  });

  test('Handles high event volume', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate high volume of events
    await page.evaluate(() => {
      const events = Array.from({ length: 50 }, (_, i) => ({
        id: `bulk-event-${i}`,
        type: 'mastery-updated',
        topic: 'mastery-updated',
        data: { score: 0.8 + (i % 10) * 0.01 },
        priority: i % 3 === 0 ? 'high' : i % 3 === 1 ? 'normal' : 'low',
        timestamp: new Date().toISOString(),
      }));

      events.forEach(event => {
        window.dispatchEvent(new CustomEvent('sse-event', { detail: event }));
      });
    });

    // UI should remain responsive
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    // Event feed should show some events (might be limited)
    const eventCount = await page.locator('[data-testid="event-item"]').count();
    expect(eventCount).toBeGreaterThan(0);
    expect(eventCount).toBeLessThanOrEqual(20); // Should have a reasonable limit
  });
});

test.describe('Real-time Feedback - Performance', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Event processing performance', async ({ page }) => {
    await page.goto('/dashboard');

    const startTime = await page.evaluate(() => performance.now());

    // Send multiple events quickly
    await page.evaluate(() => {
      const events = Array.from({ length: 100 }, (_, i) => ({
        id: `perf-test-${i}`,
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

    const endTime = await page.evaluate(() => performance.now());
    const processingTime = endTime - startTime;

    // Should process 100 events in reasonable time (< 5 seconds)
    expect(processingTime).toBeLessThan(5000);

    // UI should remain responsive
    await page.click('[data-testid="dashboard-nav"]');
    await expect(page).toHaveURL(/\/dashboard$/);
  });

  test('Memory usage under sustained event load', async ({ page }) => {
    await page.goto('/dashboard');

    // Monitor initial memory
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Send events over time
    for (let batch = 0; batch < 5; batch++) {
      await page.evaluate((batchNum) => {
        const events = Array.from({ length: 20 }, (_, i) => ({
          id: `memory-test-${batchNum}-${i}`,
          type: 'mastery-updated',
          topic: 'mastery-updated',
          data: { score: Math.random() },
          priority: 'normal',
          timestamp: new Date().toISOString(),
        }));

        events.forEach(event => {
          window.dispatchEvent(new CustomEvent('sse-event', { detail: event }));
        });
      }, batch);

      await page.waitForTimeout(1000); // Wait between batches
    }

    // Check final memory usage
    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Memory increase should be reasonable (allow 50% increase for 100 events)
    if (initialMemory > 0 && finalMemory > 0) {
      expect(finalMemory).toBeLessThan(initialMemory * 1.5);
    }

    // UI should still be responsive
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });
});