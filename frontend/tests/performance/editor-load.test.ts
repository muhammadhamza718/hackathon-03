/**
 * Performance Test: Monaco Editor Load Time
 * Tests editor load performance under various conditions
 * Task: T171
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath, verifyAuth } from '../e2e/setup/authentication';

test.describe('Editor Load Performance', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 1920, height: 1080 },
  });

  test('Monaco Editor loads in <200ms under normal conditions', async ({ page }) => {
    const startTime = performance.now();

    await page.goto('/code-editor');

    // Wait for editor container to be visible
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    // Wait for editor to be fully loaded (monaco editor ready)
    await page.waitForSelector('[data-testid="monaco-editor"]', { state: 'visible' });

    const endTime = performance.now();
    const loadTime = endTime - startTime;

    // Should load in under 200ms (P95 target)
    expect(loadTime).toBeLessThan(200);

    // Log performance metric
    console.log(`Editor load time: ${loadTime.toFixed(2)}ms`);

    // Store metric for reporting
    test.info().attachments.push({
      name: 'editor-load-time',
      contentType: 'application/json',
      body: Buffer.from(JSON.stringify({ loadTime, timestamp: new Date().toISOString() })),
    });
  });

  test('Editor load performance with large initial code', async ({ page }) => {
    const largeCode = Array.from({ length: 1000 }, (_, i) => `// Line ${i + 1}\nconst x${i} = ${i};\n`).join('');

    // Pre-load code in localStorage
    await page.addInitScript((code) => {
      localStorage.setItem('editor-initial-code', code);
    }, largeCode);

    const startTime = performance.now();

    await page.goto('/code-editor');

    // Wait for editor to load with large code
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    const endTime = performance.now();
    const loadTime = endTime - startTime;

    // Should still load reasonably fast with large code
    expect(loadTime).toBeLessThan(500); // Allow more time for large code

    console.log(`Editor load time (large code): ${loadTime.toFixed(2)}ms`);
  });

  test('Editor load performance under concurrent loads', async ({ page, context }) => {
    // Create multiple browser contexts to simulate concurrent users
    const contexts = [];
    const loadTimes = [];

    for (let i = 0; i < 5; i++) {
      const newContext = await context.browser().newContext({
        storageState: getAuthStoragePath('student'),
        viewport: { width: 1920, height: 1080 },
      });
      contexts.push(newContext);

      const newPage = await newContext.newPage();
      const startTime = performance.now();

      await newPage.goto('/code-editor');
      await expect(newPage.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

      const endTime = performance.now();
      loadTimes.push(endTime - startTime);

      await newPage.close();
    }

    // Clean up contexts
    await Promise.all(contexts.map(ctx => ctx.close()));

    // Calculate statistics
    const avgLoadTime = loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length;
    const maxLoadTime = Math.max(...loadTimes);

    console.log(`Concurrent load times: ${loadTimes.map(t => t.toFixed(2)).join(', ')}ms`);
    console.log(`Average: ${avgLoadTime.toFixed(2)}ms, Max: ${maxLoadTime.toFixed(2)}ms`);

    // Average should still be reasonable
    expect(avgLoadTime).toBeLessThan(500);
    expect(maxLoadTime).toBeLessThan(1000);
  });

  test('Memory usage during editor load', async ({ page }) => {
    // Clear memory before test
    await page.evaluate(() => {
      if (window.gc) {
        window.gc();
      }
    });

    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    await page.goto('/code-editor');
    await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

    const loadedMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0;
    });

    const memoryIncrease = loadedMemory - initialMemory;

    if (initialMemory > 0 && loadedMemory > 0) {
      // Memory increase should be reasonable (< 50MB for editor load)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // 50MB in bytes

      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`);
    }
  });

  test('Editor load with different themes', async ({ page }) => {
    const themes = ['dark', 'light', 'hc'];
    const loadTimes = [];

    for (const theme of themes) {
      await page.addInitScript((t) => {
        localStorage.setItem('editor-theme', t);
      }, theme);

      const startTime = performance.now();

      await page.goto('/code-editor');
      await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

      const endTime = performance.now();
      loadTimes.push({ theme, loadTime: endTime - startTime });

      await page.reload(); // Reset for next theme
    }

    console.log('Theme load times:', loadTimes);

    // All themes should load within acceptable time
    for (const { theme, loadTime } of loadTimes) {
      expect(loadTime).toBeLessThan(300);
    }
  });
});

test.describe('Editor Load - Stress Testing', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 1920, height: 1080 },
  });

  test('Editor load with maximum concurrent users', async ({ page, context }) => {
    const maxConcurrentUsers = 20;
    const contexts = [];
    const loadTimes = [];

    // Create multiple contexts (simulating concurrent users)
    for (let i = 0; i < maxConcurrentUsers; i++) {
      const newContext = await context.browser().newContext({
        storageState: getAuthStoragePath('student'),
        viewport: { width: 1920, height: 1080 },
      });
      contexts.push(newContext);
    }

    // Start all loads simultaneously
    const loadPromises = contexts.map(async (ctx, index) => {
      const newPage = await ctx.newPage();
      const startTime = performance.now();

      await newPage.goto('/code-editor');
      await expect(newPage.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

      const endTime = performance.now();
      const loadTime = endTime - startTime;

      await newPage.close();

      return { user: index + 1, loadTime };
    });

    // Wait for all loads to complete
    const results = await Promise.all(loadPromises);
    loadTimes.push(...results.map(r => r.loadTime));

    // Clean up
    await Promise.all(contexts.map(ctx => ctx.close()));

    // Calculate statistics
    const avgLoadTime = loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length;
    const p95LoadTime = loadTimes.sort((a, b) => a - b)[Math.floor(loadTimes.length * 0.95)];
    const maxLoadTime = Math.max(...loadTimes);

    console.log(`Stress test results (${maxConcurrentUsers} users):`);
    console.log(`Average: ${avgLoadTime.toFixed(2)}ms`);
    console.log(`P95: ${p95LoadTime.toFixed(2)}ms`);
    console.log(`Max: ${maxLoadTime.toFixed(2)}ms`);

    // P95 should be under 200ms even with 20 concurrent users
    expect(p95LoadTime).toBeLessThan(200);

    // Store results for reporting
    test.info().attachments.push({
      name: 'stress-test-results',
      contentType: 'application/json',
      body: Buffer.from(JSON.stringify({
        concurrentUsers: maxConcurrentUsers,
        averageLoadTime: avgLoadTime,
        p95LoadTime,
        maxLoadTime,
        timestamp: new Date().toISOString(),
      })),
    });
  });

  test('Memory leak detection during repeated editor loads', async ({ page }) => {
    const iterations = 50;
    const memorySnapshots = [];

    for (let i = 0; i < iterations; i++) {
      await page.goto('/code-editor');
      await expect(page.locator('[data-testid="monaco-editor-container"]')).toBeVisible();

      // Take memory snapshot every 5 iterations
      if (i % 5 === 0) {
        const memory = await page.evaluate(() => {
          return (performance as any).memory?.usedJSHeapSize || 0;
        });
        memorySnapshots.push({ iteration: i, memory });
      }

      // Clear and reload
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
    }

    // Check for memory leaks
    if (memorySnapshots.length >= 2) {
      const initialMemory = memorySnapshots[0].memory;
      const finalMemory = memorySnapshots[memorySnapshots.length - 1].memory;

      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        const increasePercentage = (memoryIncrease / initialMemory) * 100;

        console.log(`Memory change after ${iterations} loads: ${increasePercentage.toFixed(1)}%`);

        // Memory should not increase more than 50% after 50 loads
        expect(increasePercentage).toBeLessThan(50);
      }
    }
  });
});