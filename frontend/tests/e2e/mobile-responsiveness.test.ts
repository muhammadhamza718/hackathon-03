/**
 * E2E Test: Mobile Responsiveness
 * Tests mobile device compatibility and responsive design
 * Task: T166
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath, verifyAuth } from './setup/authentication';

test.describe('Mobile Responsiveness - General', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 375, height: 667 }, // iPhone SE
  });

  test('Mobile layout renders correctly', async ({ page }) => {
    await page.goto('/dashboard');

    // Verify mobile viewport is being used
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(viewportWidth).toBeLessThan(768);

    // Mobile menu button should be visible
    await expect(page.locator('[data-testid="mobile-menu-btn"]')).toBeVisible();

    // Desktop navigation should be hidden
    await expect(page.locator('[data-testid="desktop-nav"]')).not.toBeVisible();

    // Mobile navigation should be accessible
    await page.click('[data-testid="mobile-menu-btn"]');
    await expect(page.locator('[data-testid="mobile-nav-drawer"]')).toBeVisible();
  });

  test('Touch targets are appropriately sized', async ({ page }) => {
    await page.goto('/dashboard');

    // Check that interactive elements have minimum touch target size (44x44px)
    const buttons = await page.locator('button, [role="button"], a').all();

    for (const button of buttons) {
      const boundingBox = await button.boundingBox();
      if (boundingBox) {
        expect(boundingBox.width).toBeGreaterThanOrEqual(44);
        expect(boundingBox.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('Text size is readable on mobile', async ({ page }) => {
    await page.goto('/dashboard');

    // Check that text is not too small
    const bodyText = page.locator('body');
    const fontSize = await bodyText.evaluate((el) => window.getComputedStyle(el).fontSize);
    expect(parseInt(fontSize)).toBeGreaterThanOrEqual(14); // Minimum readable size

    // Check headings are appropriately sized
    const headings = await page.locator('h1, h2, h3').all();
    for (const heading of headings) {
      const fontSize = await heading.evaluate((el) => window.getComputedStyle(el).fontSize);
      expect(parseInt(fontSize)).toBeGreaterThanOrEqual(18); // Minimum heading size
    }
  });

  test('Horizontal scrolling prevention', async ({ page }) => {
    await page.goto('/dashboard');

    // Check that page doesn't require horizontal scrolling
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 10); // Allow small rounding difference
  });
});

test.describe('Mobile Responsiveness - Dashboard', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 375, height: 667 },
  });

  test('Dashboard mobile layout', async ({ page }) => {
    await page.goto('/dashboard');

    // Stats cards should stack vertically
    await expect(page.locator('[data-testid="stats-container"]')).toBeVisible();

    // Check if stats are in single column layout
    const statsItems = await page.locator('[data-testid="stat-item"]').all();
    expect(statsItems.length).toBeGreaterThan(0);

    // Charts should be responsive
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();

    // Chart should fit within mobile viewport
    const chartBoundingBox = await page.locator('[data-testid="performance-chart"]').boundingBox();
    if (chartBoundingBox) {
      expect(chartBoundingBox.width).toBeLessThanOrEqual(375); // Should fit in viewport width
    }
  });

  test('Mobile dashboard navigation', async ({ page }) => {
    await page.goto('/dashboard');

    // Open mobile menu
    await page.click('[data-testid="mobile-menu-btn"]');

    // Check menu items are touch-friendly
    const menuItems = await page.locator('[data-testid="mobile-menu-item"]').all();
    expect(menuItems.length).toBeGreaterThan(0);

    for (const item of menuItems) {
      const boundingBox = await item.boundingBox();
      if (boundingBox) {
        expect(boundingBox.height).toBeGreaterThanOrEqual(44); // Minimum touch target
      }
    }

    // Close menu
    await page.click('[data-testid="mobile-menu-close"]');
    await expect(page.locator('[data-testid="mobile-nav-drawer"]')).not.toBeVisible();
  });

  test('Mobile event feed scroll', async ({ page }) => {
    await page.goto('/dashboard');

    // Event feed should be scrollable vertically
    const eventFeed = page.locator('[data-testid="event-feed"]');
    await expect(eventFeed).toBeVisible();

    // Check if feed has enough content to scroll
    const eventItems = await page.locator('[data-testid="event-item"]').count();
    if (eventItems > 3) {
      // Should be scrollable
      const scrollHeight = await eventFeed.evaluate((el) => el.scrollHeight);
      const clientHeight = await eventFeed.evaluate((el) => el.clientHeight);
      expect(scrollHeight).toBeGreaterThan(clientHeight);
    }
  });
});

test.describe('Mobile Responsiveness - Code Editor', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 375, height: 667 },
  });

  test('Code editor mobile layout', async ({ page }) => {
    await page.goto('/code-editor');

    // Editor should be visible but might be smaller
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    // Editor toolbar should be compact
    await expect(page.locator('[data-testid="editor-toolbar"]')).toBeVisible();

    // Buttons should be touch-friendly
    const toolbarButtons = await page.locator('[data-testid="editor-toolbar"] button').all();
    for (const button of toolbarButtons) {
      const boundingBox = await button.boundingBox();
      if (boundingBox) {
        expect(boundingBox.width).toBeGreaterThanOrEqual(44);
        expect(boundingBox.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('Mobile code input handling', async ({ page }) => {
    await page.goto('/code-editor');

    // Focus editor
    await page.click('[data-testid="monaco-editor"]');

    // Type some code using mobile keyboard
    await page.keyboard.type('print("Hello Mobile")');

    // Verify code is entered
    const editorContent = await page.locator('[data-testid="monaco-editor-content"]').textContent();
    expect(editorContent).toContain('Hello Mobile');
  });

  test('Mobile execution feedback display', async ({ page }) => {
    await page.goto('/code-editor');

    // Write and run code
    await page.click('[data-testid="monaco-editor"]');
    await page.keyboard.type('print("Mobile Test")');
    await page.click('[data-testid="run-btn"]');

    // Execution output should be visible and scrollable if needed
    await expect(page.locator('[data-testid="execution-output"]')).toBeVisible();

    // Output should fit in viewport or be scrollable
    const outputElement = page.locator('[data-testid="execution-output"]');
    const boundingBox = await outputElement.boundingBox();
    if (boundingBox) {
      expect(boundingBox.width).toBeLessThanOrEqual(375); // Should fit width
    }
  });
});

test.describe('Mobile Responsiveness - Interactive Features', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 375, height: 667 },
  });

  test('Mobile touch gestures', async ({ page }) => {
    await page.goto('/dashboard');

    // Test swipe gestures for mobile components
    const eventFeed = page.locator('[data-testid="event-feed"]');
    await expect(eventFeed).toBeVisible();

    // Simulate swipe down to refresh (if supported)
    await page.evaluate(() => {
      const eventFeed = document.querySelector('[data-testid="event-feed"]');
      if (eventFeed) {
        eventFeed.scrollTop = 0;
      }
    });

    // Test horizontal swipe for carousels or tabs
    const tabs = page.locator('[data-testid="mobile-tabs"]');
    if (await tabs.isVisible()) {
      await tabs.click(); // Test tab switching
      await expect(page.locator('[data-testid="tab-content"]')).toBeVisible();
    }
  });

  test('Mobile dropdowns and selects', async ({ page }) => {
    await page.goto('/dashboard');

    // Check mobile-friendly select elements
    const selectElements = await page.locator('select').all();

    for (const select of selectElements) {
      await select.click();

      // Mobile should show native picker
      // This varies by browser, but we verify the select opens
      await page.waitForTimeout(500);
    }
  });

  test('Mobile modal/dialog handling', async ({ page }) => {
    await page.goto('/code-editor');

    // Open save dialog
    await page.click('[data-testid="save-btn"]');

    // Modal should be mobile-friendly
    await expect(page.locator('[data-testid="save-dialog"]')).toBeVisible();

    // Dialog should fit within viewport
    const dialog = page.locator('[data-testid="save-dialog"]');
    const boundingBox = await dialog.boundingBox();
    if (boundingBox) {
      expect(boundingBox.width).toBeLessThanOrEqual(375);
    }

    // Close dialog
    await page.click('[data-testid="dialog-close"]');
    await expect(page.locator('[data-testid="save-dialog"]')).not.toBeVisible();
  });
});

test.describe('Mobile Responsiveness - Multiple Devices', () => {
  const devices = [
    { name: 'iPhone SE', width: 375, height: 667 },
    { name: 'iPhone 12', width: 390, height: 844 },
    { name: 'iPhone 14 Pro Max', width: 430, height: 932 },
    { name: 'Pixel 5', width: 393, height: 851 },
    { name: 'Samsung Galaxy S21', width: 360, height: 800 },
    { name: 'iPad Mini', width: 768, height: 1024 },
  ];

  for (const device of devices) {
    test(`Dashboard works on ${device.name}`, async ({ page }) => {
      test.skip(device.width >= 768, 'Skipping tablet/desktop devices in this specific test');

      await page.setViewportSize({ width: device.width, height: device.height });
      await page.goto('/dashboard');

      // Basic elements should be visible
      await expect(page.locator('[data-testid="user-greeting"]')).toBeVisible();
      await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();

      // Mobile menu should be available
      await expect(page.locator('[data-testid="mobile-menu-btn"]')).toBeVisible();
    });
  }

  // Test iPad separately (hybrid device)
  test('iPad/tablet responsive layout', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/dashboard');

    // Tablet might show both mobile and desktop elements
    // Check that layout is appropriate for tablet size
    const viewportWidth = await page.evaluate(() => window.innerWidth);

    if (viewportWidth >= 768 && viewportWidth < 1024) {
      // Tablet range - might show hybrid layout
      // Check that main content is readable
      await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
    }
  });
});

test.describe('Mobile Responsiveness - Accessibility', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 375, height: 667 },
  });

  test('Mobile screen reader compatibility', async ({ page }) => {
    await page.goto('/dashboard');

    // Check ARIA labels for mobile elements
    await expect(page.locator('[aria-label="Mobile navigation menu"]')).toBeVisible();

    // Ensure all interactive elements have labels
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const ariaLabelledBy = await button.getAttribute('aria-labelledby');

      // Either label or labelledby should be present
      expect(ariaLabel || ariaLabelledBy).toBeTruthy();
    }
  });

  test('Mobile focus management', async ({ page }) => {
    await page.goto('/dashboard');

    // Test tab navigation on mobile
    await page.keyboard.press('Tab');

    // Focus should move to next interactive element
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.getAttribute('data-testid');
    });

    expect(focusedElement).toBeTruthy();

    // Open mobile menu and test focus trapping
    await page.click('[data-testid="mobile-menu-btn"]');
    await page.keyboard.press('Tab');

    // Focus should remain within mobile menu
    const menuFocused = await page.evaluate(() => {
      return document.activeElement?.closest('[data-testid="mobile-nav-drawer"]') !== null;
    });

    expect(menuFocused).toBe(true);
  });

  test('Mobile zoom and scaling', async ({ page }) => {
    await page.goto('/dashboard');

    // Check that viewport meta tag allows scaling
    const viewportMeta = await page.$('meta[name="viewport"]');
    const content = await viewportMeta?.getAttribute('content');

    // Should allow user scaling (unless explicitly disabled for good reason)
    if (content) {
      expect(content).not.toContain('user-scalable=no');
      expect(content).not.toContain('maximum-scale=1.0');
    }

    // Test at different zoom levels
    await page.evaluate(() => {
      document.body.style.zoom = '1.5';
    });

    // Content should still be usable
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    await page.evaluate(() => {
      document.body.style.zoom = '1';
    });
  });
});

test.describe('Mobile Responsiveness - Performance', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 375, height: 667 },
  });

  test('Mobile page load performance', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    const loadTime = Date.now() - startTime;

    // Mobile should load reasonably fast (< 5 seconds)
    expect(loadTime).toBeLessThan(5000);
  });

  test('Mobile memory usage under load', async ({ page }) => {
    await page.goto('/dashboard');

    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Scroll through content to trigger rendering
    await page.evaluate(() => {
      window.scrollBy(0, 500);
    });

    // Perform multiple interactions
    for (let i = 0; i < 5; i++) {
      await page.click('[data-testid="mobile-menu-btn"]');
      await page.click('[data-testid="mobile-menu-close"]');
      await page.waitForTimeout(200);
    }

    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    // Memory increase should be reasonable on mobile
    if (initialMemory > 0 && finalMemory > 0) {
      expect(finalMemory).toBeLessThan(initialMemory * 1.8); // Allow 80% increase
    }
  });

  test('Mobile touch performance', async ({ page }) => {
    await page.goto('/dashboard');

    // Measure touch response time
    const touchTargets = await page.locator('button, [role="button"]').all();
    expect(touchTargets.length).toBeGreaterThan(0);

    for (const target of touchTargets.slice(0, 5)) { // Test first 5
      const startTime = await page.evaluate(() => performance.now());

      await target.click();
      await page.waitForTimeout(100); // Wait for response

      const endTime = await page.evaluate(() => performance.now());
      const responseTime = endTime - startTime;

      // Touch response should be quick (< 500ms)
      expect(responseTime).toBeLessThan(500);
    }
  });
});

test.describe('Mobile Responsiveness - Edge Cases', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
  });

  test('Very small viewport (320x480)', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 480 });
    await page.goto('/dashboard');

    // Should still be usable (even if cramped)
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    // Text should be readable (might require horizontal scroll for some content)
    const textElements = await page.locator('p, span, div').all();
    expect(textElements.length).toBeGreaterThan(0);
  });

  test('Portrait vs Landscape orientation', async ({ page }) => {
    // Start in portrait
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    // Switch to landscape
    await page.setViewportSize({ width: 667, height: 375 });
    await page.goto('/dashboard'); // Reload to apply new layout

    // Should adapt to landscape
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();

    // Landscape might show different layout
    // Check that content is still accessible
    await expect(page.locator('[data-testid="mastery-score"]')).toBeVisible();
  });

  test('Mobile with keyboard attached', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/code-editor');

    // Focus editor
    await page.click('[data-testid="monaco-editor"]');

    // Type using keyboard
    await page.keyboard.type('print("Keyboard test")');

    // Editor should handle keyboard input
    const editorContent = await page.locator('[data-testid="monaco-editor-content"]').textContent();
    expect(editorContent).toContain('Keyboard test');

    // Keyboard shouldn't obscure the editor
    const editorBounding = await page.locator('[data-testid="monaco-editor-container"]').boundingBox();
    if (editorBounding) {
      const viewportHeight = await page.evaluate(() => window.innerHeight);
      expect(editorBounding.y + editorBounding.height).toBeLessThan(viewportHeight);
    }
  });
});