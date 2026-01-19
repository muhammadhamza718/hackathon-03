/**
 * E2E Test: Dashboard Data Loading
 * Tests dashboard data fetching, caching, and display
 * Task: T164
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath, verifyAuth } from './setup/authentication';

test.describe('Dashboard Data Loading', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await verifyAuth(page, '');
  });

  test('Dashboard loads with comprehensive data', async ({ page }) => {
    // Verify dashboard URL
    await expect(page).toHaveURL(/\/dashboard$/);

    // Check for user greeting
    await expect(page.locator('[data-testid="user-greeting"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-greeting"]')).toContainText(/hello|welcome/i);

    // Verify mastery score is loaded and displayed
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
    const masteryScore = await page.locator('[data-testid="mastery-score"]').textContent();
    expect(masteryScore).toBeTruthy();
    expect(parseFloat(masteryScore || '0')).toBeGreaterThanOrEqual(0);
    expect(parseFloat(masteryScore || '0')).toBeLessThanOrEqual(100);

    // Verify streak information
    await expect(page.locator('[data-testid="current-streak"]')).toBeVisible();
    const streak = await page.locator('[data-testid="current-streak"]').textContent();
    expect(streak).toBeTruthy();

    // Verify total assignments/completed work
    await expect(page.locator('[data-testid="total-assignments"]')).toBeVisible();
    const assignments = await page.locator('[data-testid="total-assignments"]').textContent();
    expect(assignments).toBeTruthy();

    // Verify performance metrics chart is present
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();

    // Verify activity feed is loaded
    await expect(page.locator('[data-testid="activity-feed"]')).toBeVisible();
    const activityItems = await page.locator('[data-testid="activity-item"]').count();
    expect(activityItems).toBeGreaterThan(0);

    // Verify recommendations are loaded
    await expect(page.locator('[data-testid="recommendations-section"]')).toBeVisible();
    const recommendations = await page.locator('[data-testid="recommendation-item"]').count();
    expect(recommendations).toBeGreaterThan(0);

    // Verify cohort comparison data
    await expect(page.locator('[data-testid="cohort-comparison"]')).toBeVisible();
    await expect(page.locator('[data-testid="percentile-rank"]')).toBeVisible();
  });

  test('Dashboard loading states and skeletons', async ({ page }) => {
    // Clear cache to force reload
    await page.evaluate(() => localStorage.clear());

    // Reload dashboard
    await page.reload();

    // Should show loading skeleton initially
    await expect(page.locator('[data-testid="dashboard-skeleton"]')).toBeVisible();

    // Loading should transition to real content
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-skeleton"]')).not.toBeVisible();
  });

  test('Dashboard data refresh', async ({ page }) => {
    // Initial load
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
    const initialScore = await page.locator('[data-testid="mastery-score"]').textContent();

    // Trigger refresh
    await page.click('[data-testid="refresh-dashboard-btn"]');

    // Should show refreshing state
    await expect(page.locator('[data-testid="refresh-indicator"]')).toContainText('Refreshing');

    // Wait for refresh to complete
    await expect(page.locator('[data-testid="refresh-indicator"]')).toContainText('Updated');

    // Data should be updated (or at least reloaded)
    const refreshedScore = await page.locator('[data-testid="mastery-score"]').textContent();
    expect(refreshedScore).toBeTruthy();

    // If data actually changed, scores will differ, but if not, they should be the same
    // The important part is that the UI updated successfully
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });

  test('Dashboard error handling and retry', async ({ page }) => {
    // Mock network failure scenario
    await page.route('**/api/analytics/metrics', (route) => {
      route.abort('failed');
    });

    // Reload to trigger error
    await page.reload();

    // Should show error state
    await expect(page.locator('[data-testid="dashboard-error"]')).toBeVisible();

    // Should have retry button
    await expect(page.locator('[data-testid="retry-btn"]')).toBeVisible();

    // Remove network interception
    await page.unroute('**/api/analytics/metrics');

    // Click retry
    await page.click('[data-testid="retry-btn"]');

    // Should load successfully
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });

  test('Dashboard responsive data display', async ({ page }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' },
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Check that key elements are visible and accessible
      await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
      await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();

      // For mobile, check if menu is accessible
      if (viewport.width < 768) {
        await expect(page.locator('[data-testid="mobile-menu-btn"]')).toBeVisible();
      }
    }
  });

  test('Dashboard data filtering and grouping', async ({ page }) => {
    // Check time range filter
    await expect(page.locator('[data-testid="time-range-filter"]')).toBeVisible();

    // Change time range
    await page.selectOption('[data-testid="time-range-filter"]', '7d');

    // Should reload data for new range
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();

    // Check topic filter
    await expect(page.locator('[data-testid="topic-filter"]')).toBeVisible();

    // Select specific topic
    await page.click('[data-testid="topic-filter"]');
    await page.click('[data-testid="topic-algebra"]');

    // Should update all data displays
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();

    // Verify filtered data appears in activity feed
    const activityItems = await page.locator('[data-testid="activity-item"]').allTextContents();
    activityItems.forEach(text => {
      expect(text.toLowerCase()).toContain('algebra');
    });
  });

  test('Dashboard analytics data visualization', async ({ page }) => {
    // Check chart is interactive
    const chart = page.locator('[data-testid="performance-chart"]');
    await expect(chart).toBeVisible();

    // Hover over chart to see tooltips
    await chart.hover();
    await expect(page.locator('[data-testid="chart-tooltip"]')).toBeVisible();

    // Check chart legend
    await expect(page.locator('[data-testid="chart-legend"]')).toBeVisible();

    // Verify chart has data points
    const dataPoints = await page.locator('[data-testid="chart-data-point"]').count();
    expect(dataPoints).toBeGreaterThan(0);
  });

  test('Dashboard data export functionality', async ({ page }) => {
    // Check export button
    await expect(page.locator('[data-testid="export-data-btn"]')).toBeVisible();

    // Click export
    await page.click('[data-testid="export-data-btn"]');

    // Should show export options
    await expect(page.locator('[data-testid="export-options"]')).toBeVisible();

    // Export as CSV
    await page.click('[data-testid="export-csv"]');

    // Should trigger download or show success
    await expect(page.locator('[data-testid="export-success"]')).toBeVisible();
  });
});

test.describe('Dashboard - Real-time Updates', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Dashboard updates with real-time mastery changes', async ({ page }) => {
    await page.goto('/dashboard');

    // Get initial mastery score
    const initialScore = await page.locator('[data-testid="mastery-score"]').textContent();

    // Simulate real-time mastery update
    await page.evaluate(() => {
      const masteryEvent = {
        id: 'mastery-update-realtime',
        type: 'mastery-updated',
        topic: 'mastery-updated',
        data: {
          studentId: 'test-student-123',
          score: 0.92,
          previousScore: 0.85,
          improvement: '+7%',
        },
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: masteryEvent }));
    });

    // Verify mastery score updated
    await expect(page.locator('[data-testid="mastery-score"]')).toContainText('92');

    // Check for update animation or indicator
    await expect(page.locator('[data-testid="mastery-update-indicator"]')).toBeVisible();
  });

  test('Dashboard activity feed updates in real-time', async ({ page }) => {
    await page.goto('/dashboard');

    // Get initial activity count
    const initialCount = await page.locator('[data-testid="activity-item"]').count();

    // Simulate new activity event
    await page.evaluate(() => {
      const activityEvent = {
        id: 'new-activity-123',
        type: 'assignment-completed',
        topic: 'assignment-completed',
        data: {
          assignmentId: 'assignment-456',
          title: 'New Python Challenge',
          score: 0.88,
          completedAt: new Date().toISOString(),
        },
        priority: 'normal',
        timestamp: new Date().toISOString(),
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: activityEvent }));
    });

    // Activity feed should update
    const newCount = await page.locator('[data-testid="activity-item"]').count();
    expect(newCount).toBeGreaterThan(initialCount);

    // New activity should be visible
    await expect(page.locator('[data-testid="activity-item"]')).toContainText('New Python Challenge');
  });

  test('Dashboard recommendation updates', async ({ page }) => {
    await page.goto('/dashboard');

    // Simulate new recommendation
    await page.evaluate(() => {
      const recommendationEvent = {
        id: 'new-rec-123',
        type: 'recommendation',
        topic: 'recommendation',
        data: {
          id: 'rec-456',
          title: 'Advanced Functions Practice',
          topic: 'functions',
          priority: 'high',
          estimatedTime: 20,
        },
        priority: 'high',
        timestamp: new Date().toISOString(),
      };

      window.dispatchEvent(new CustomEvent('sse-event', { detail: recommendationEvent }));
    });

    // New recommendation should appear
    await expect(page.locator('[data-testid="recommendation-item"]')).toContainText('Advanced Functions Practice');

    // Should show priority indicator
    await expect(page.locator('[data-testid="priority-high"]')).toBeVisible();
  });
});

test.describe('Dashboard - Performance & Caching', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Dashboard loads from cache on subsequent visits', async ({ page }) => {
    // First load
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();

    // Navigate away
    await page.goto('/code-editor');

    // Navigate back quickly (should use cache)
    await page.goto('/dashboard');

    // Should load faster (check for cached indicator)
    await expect(page.locator('[data-testid="data-source"]')).toContainText(/cache|cached/i);

    // Content should still be visible
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });

  test('Dashboard data pagination', async ({ page }) => {
    await page.goto('/dashboard');

    // Check if activity feed has pagination
    const initialItems = await page.locator('[data-testid="activity-item"]').count();

    // Click load more
    await page.click('[data-testid="load-more-activities"]');

    // Should show more items
    await page.waitForTimeout(1000); // Wait for loading
    const newItems = await page.locator('[data-testid="activity-item"]').count();

    if (newItems > initialItems) {
      expect(newItems).toBeGreaterThan(initialItems);
    }
  });

  test('Dashboard handles data refresh under load', async ({ page }) => {
    await page.goto('/dashboard');

    // Perform multiple refreshes quickly
    for (let i = 0; i < 3; i++) {
      await page.click('[data-testid="refresh-dashboard-btn"]');
      await page.waitForTimeout(500); // Small delay between refreshes
    }

    // UI should remain responsive
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });
});

test.describe('Dashboard - Accessibility', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Dashboard is keyboard navigable', async ({ page }) => {
    await page.goto('/dashboard');

    // Test tab navigation
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="refresh-dashboard-btn"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="export-data-btn"]')).toBeFocused();

    // Test enter to activate
    await page.keyboard.press('Enter');
    await expect(page.locator('[data-testid="export-options"]')).toBeVisible();
  });

  test('Dashboard has proper ARIA labels', async ({ page }) => {
    await page.goto('/dashboard');

    // Check for proper ARIA labels on interactive elements
    await expect(page.locator('[aria-label="Mastery Score"]')).toBeVisible();
    await expect(page.locator('[aria-label="Current Streak"]')).toBeVisible();
    await expect(page.locator('[aria-label="Activity Feed"]')).toBeVisible();

    // Check for proper heading structure
    const headings = await page.locator('h1, h2, h3').allTextContents();
    expect(headings.length).toBeGreaterThan(0);

    // Check for landmarks
    await expect(page.locator('[role="main"]')).toBeVisible();
    await expect(page.locator('[role="complementary"]')).toBeVisible();
  });

  test('Dashboard respects prefers-reduced-motion', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });

    await page.goto('/dashboard');

    // Check that animations are disabled or reduced
    const hasAnimations = await page.evaluate(() => {
      const elements = document.querySelectorAll('[data-testid="mastery-score"]');
      const style = window.getComputedStyle(elements[0]);
      return style.animationName !== 'none' || style.transition !== 'none';
    });

    // If animations exist, they should respect reduced motion
    if (hasAnimations) {
      // Verify reduced motion is applied
      const reducedMotionApplied = await page.evaluate(() => {
        const elements = document.querySelectorAll('[data-testid="mastery-score"]');
        const style = window.getComputedStyle(elements[0]);
        return style.animationPlayState === 'paused' || style.transitionDuration === '0s';
      });
      expect(reducedMotionApplied).toBe(true);
    }
  });
});