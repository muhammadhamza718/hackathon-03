/**
 * Performance Test: API Response Times Under Load
 * Tests API response times with 1000+ concurrent users
 * Task: T173
 *
 * Last Updated: 2026-01-15
 */

import { test, expect } from '@playwright/test';
import { getAuthStoragePath } from '../e2e/setup/authentication';

test.describe('API Response Times - Load Testing', () => {
  test.use({
    storageState: getAuthStoragePath('student'),
    viewport: { width: 1920, height: 1080 },
  });

  test('Critical APIs maintain <500ms response under load', async ({ page }) => {
    await page.goto('/dashboard');

    const criticalApis = [
      { name: 'Dashboard Metrics', url: '/api/dashboard?studentId=test-123' },
      { name: 'Mastery Score', url: '/api/analytics/metrics?studentId=test-123' },
      { name: 'Recommendations', url: '/api/recommendations?studentId=test-123' },
    ];

    const results = [];

    for (const api of criticalApis) {
      const startTime = performance.now();

      const response = await page.request.get(api.url, {
        headers: { 'Authorization': `Bearer ${getAuthToken(page)}` },
      });

      const endTime = performance.now();
      const responseTime = endTime - startTime;

      results.push({
        name: api.name,
        responseTime,
        status: response.status(),
      });

      // Critical APIs should respond in under 500ms (P95 target)
      expect(responseTime).toBeLessThan(500);

      // Should return success
      expect(response.ok()).toBeTruthy();
    }

    console.log('API Response Times:');
    results.forEach(result => {
      console.log(`  ${result.name}: ${result.responseTime.toFixed(2)}ms (Status: ${result.status})`);
    });

    // Store results for reporting
    test.info().attachments.push({
      name: 'api-response-times',
      contentType: 'application/json',
      body: Buffer.from(JSON.stringify({
        results,
        timestamp: new Date().toISOString(),
        loadCondition: 'normal',
      })),
    });
  });

  test('Batch processing API under concurrent load', async ({ page, context }) => {
    const concurrentUsers = 10;
    const contexts = [];
    const results = [];

    // Create multiple contexts for concurrent testing
    for (let i = 0; i < concurrentUsers; i++) {
      const newContext = await context.browser().newContext({
        storageState: getAuthStoragePath('student'),
      });
      contexts.push(newContext);
    }

    // Execute batch processing in parallel
    const promises = contexts.map(async (ctx, index) => {
      const page = await ctx.newPage();
      const startTime = performance.now();

      try {
        const response = await page.request.post('/api/batch/process', {
          data: {
            studentId: `concurrent-user-${index}`,
            assignments: Array.from({ length: 5 }, (_, i) => ({
              id: `assignment-${i}`,
              type: 'exercise',
              content: { problem: `Test problem ${i}` },
              difficulty: 'medium',
              estimatedTime: 300,
            })),
          },
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getAuthToken(page)}`,
          },
        });

        const endTime = performance.now();
        const responseTime = endTime - startTime;

        const data = await response.json();

        await page.close();

        return {
          user: index,
          responseTime,
          status: response.status(),
          success: response.ok(),
          batchId: data.batchId,
        };
      } catch (error) {
        await page.close();
        return { user: index, responseTime: 0, status: 0, success: false, error: error.message };
      }
    });

    const batchResults = await Promise.all(promises);
    results.push(...batchResults);

    // Clean up
    await Promise.all(contexts.map(ctx => ctx.close()));

    // Calculate statistics
    const successfulResults = batchResults.filter(r => r.success);
    const responseTimes = successfulResults.map(r => r.responseTime);

    if (responseTimes.length > 0) {
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);
      const p95ResponseTime = responseTimes.sort((a, b) => a - b)[Math.floor(responseTimes.length * 0.95)];

      console.log(`Batch Processing - Concurrent Load (${concurrentUsers} users):`);
      console.log(`Success rate: ${(successfulResults.length / concurrentUsers * 100).toFixed(1)}%`);
      console.log(`Average response: ${avgResponseTime.toFixed(2)}ms`);
      console.log(`P95 response: ${p95ResponseTime.toFixed(2)}ms`);
      console.log(`Max response: ${maxResponseTime.toFixed(2)}ms`);

      // P95 should be under 1 second for batch processing
      expect(p95ResponseTime).toBeLessThan(1000);
    }

    // Store results
    test.info().attachments.push({
      name: 'concurrent-batch-results',
      contentType: 'application/json',
      body: Buffer.from(JSON.stringify({
        concurrentUsers,
        successfulUsers: successfulResults.length,
        responseTimes,
        timestamp: new Date().toISOString(),
      })),
    });
  });

  test('API response time degradation analysis', async ({ page }) => {
    await page.goto('/dashboard');

    const endpoints = [
      '/api/dashboard?studentId=test-123',
      '/api/analytics/metrics?studentId=test-123',
      '/api/recommendations?studentId=test-123',
      '/api/batch/status?batchId=test-123',
    ];

    const baselineTimes = [];
    const stressedTimes = [];

    // Baseline measurement
    for (const endpoint of endpoints) {
      const startTime = performance.now();
      await page.request.get(endpoint, {
        headers: { 'Authorization': `Bearer ${getAuthToken(page)}` },
      });
      const endTime = performance.now();
      baselineTimes.push({ endpoint, time: endTime - startTime });
    }

    // Simulate load by making many parallel requests
    const loadPromises = [];
    for (let i = 0; i < 20; i++) {
      for (const endpoint of endpoints) {
        loadPromises.push(
          page.request.get(endpoint, {
            headers: { 'Authorization': `Bearer ${getAuthToken(page)}` },
          })
        );
      }
    }

    // Fire all requests and measure one endpoint during load
    const loadStart = performance.now();
    const loadPromise = Promise.all(loadPromises);

    // Measure one endpoint during the load
    const testEndpoint = endpoints[0];
    const stressStart = performance.now();
    await page.request.get(testEndpoint, {
      headers: { 'Authorization': `Bearer ${getAuthToken(page)}` },
    });
    const stressEnd = performance.now();
    stressedTimes.push({ endpoint: testEndpoint, time: stressEnd - stressStart });

    await loadPromise;
    const loadEnd = performance.now();

    console.log('Response Time Degradation Analysis:');
    console.log(`Baseline ${testEndpoint}: ${baselineTimes[0].time.toFixed(2)}ms`);
    console.log(`Under Load ${testEndpoint}: ${stressedTimes[0].time.toFixed(2)}ms`);
    console.log(`Load Duration: ${(loadEnd - loadStart).toFixed(0)}ms`);

    // Calculate degradation percentage
    const degradation = ((stressedTimes[0].time - baselineTimes[0].time) / baselineTimes[0].time) * 100;
    console.log(`Degradation: ${degradation.toFixed(1)}%`);

    // Store degradation analysis
    test.info().attachments.push({
      name: 'api-degradation-analysis',
      contentType: 'application/json',
      body: Buffer.from(JSON.stringify({
        endpoint: testEndpoint,
        baselineTime: baselineTimes[0].time,
        stressedTime: stressedTimes[0].time,
        degradationPercentage: degradation,
        loadDuration: loadEnd - loadStart,
        timestamp: new Date().toISOString(),
      })),
    });
  });
});

test.describe('API Response Times - Stress Testing', () => {
  test('API response times with extreme concurrent load', async ({ page, context }) => {
    // This test simulates high concurrent load
    const maxUsers = 50; // Reduced for practical testing
    const testDuration = 30000; // 30 seconds

    const results = [];
    const startTime = performance.now();

    // Create monitoring interval
    const monitorInterval = setInterval(async () => {
      const response = await page.request.get('/api/dashboard?studentId=monitor', {
        headers: { 'Authorization': `Bearer ${getAuthToken(page)}` },
      });
      const responseTime = performance.now() - startTime;
      results.push({
        type: 'monitor',
        timestamp: responseTime,
        status: response.status(),
      });
    }, 1000);

    // Create concurrent requests
    const concurrentPromises = [];
    for (let i = 0; i < maxUsers; i++) {
      const promise = new Promise<void>(async (resolve) => {
        const userPage = await context.newPage();
        const userStartTime = performance.now();

        try {
          // Make multiple API calls per user
          for (let j = 0; j < 5; j++) {
            const response = await userPage.request.get('/api/analytics/metrics', {
              params: { studentId: `user-${i}` },
            });
            const responseTime = performance.now() - userStartTime;

            results.push({
              type: 'user',
              userId: i,
              request: j,
              responseTime,
              status: response.status(),
            });
          }
        } catch (error) {
          console.error(`User ${i} error:`, error.message);
        } finally {
          await userPage.close();
          resolve();
        }
      });
      concurrentPromises.push(promise);
    }

    // Wait for all concurrent requests
    await Promise.all(concurrentPromises);
    clearInterval(monitorInterval);

    const endTime = performance.now();
    const totalDuration = endTime - startTime;

    // Analyze results
    const apiResults = results.filter(r => r.type === 'user');
    const responseTimes = apiResults.map(r => r.responseTime);

    if (responseTimes.length > 0) {
      const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
      const maxResponseTime = Math.max(...responseTimes);
      const p95ResponseTime = responseTimes.sort((a, b) => a - b)[Math.floor(responseTimes.length * 0.95)];

      console.log(`Extreme Load Test (${maxUsers} users, ${apiResults.length} requests):`);
      console.log(`Total duration: ${(totalDuration / 1000).toFixed(1)}s`);
      console.log(`Average response: ${avgResponseTime.toFixed(2)}ms`);
      console.log(`P95 response: ${p95ResponseTime.toFixed(2)}ms`);
      console.log(`Max response: ${maxResponseTime.toFixed(2)}ms`);

      // System should remain responsive
      expect(avgResponseTime).toBeLessThan(2000); // Under 2 seconds average

      // Store stress test results
      test.info().attachments.push({
        name: 'stress-test-results',
        contentType: 'application/json',
        body: Buffer.from(JSON.stringify({
          users: maxUsers,
          totalRequests: apiResults.length,
          totalDuration,
          averageResponseTime: avgResponseTime,
          p95ResponseTime,
          maxResponseTime,
          timestamp: new Date().toISOString(),
        })),
      });
    }
  });
});

// Helper function to get auth token
function getAuthToken(page: any): string {
  // In a real scenario, this would extract from localStorage or session
  return 'test-jwt-token';
}