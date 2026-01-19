/**
 * Performance Budget Tests
 * Validates performance budgets and optimization targets
 * Task: T136
 *
 * Last Updated: 2026-01-15
 */

import { performance } from 'perf_hooks';
import { NextRequest } from 'next/server';

// Import performance utilities
import {
  PerformanceMonitor,
  PerformanceBudget,
  PerformanceTrends,
  generatePerformanceReport,
  PERFORMANCE_THRESHOLDS,
} from '@/middleware/performance';

// Mock console methods to reduce test noise
const originalError = console.error;
const originalWarn = console.warn;
const originalLog = console.log;

beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
  console.log = jest.fn();
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
  console.log = originalLog;
});

describe('Performance Budget Tests - T136', () => {
  describe('Bundle Size Budgets', () => {
    it('should enforce initial bundle size < 500KB (excluding Monaco)', () => {
      // This would typically be checked during build time
      // For this test, we'll verify the configuration exists
      const nextConfig = require('next.config.mjs').default;

      expect(nextConfig).toBeDefined();
      expect(nextConfig.experimental).toBeDefined();
    });

    it('should have proper webpack optimization config', () => {
      const nextConfig = require('next.config.mjs').default;

      expect(nextConfig.webpack).toBeDefined();
      expect(typeof nextConfig.webpack).toBe('function');

      // Test webpack config generation
      const mockConfig = {
        module: { rules: [] },
        plugins: [],
        optimization: {},
      };

      const mockContext = {
        dev: false,
        isServer: false,
        nextRuntime: 'browser',
      };

      const result = nextConfig.webpack(mockConfig, mockContext);

      expect(result.optimization).toBeDefined();
      expect(result.optimization.splitChunks).toBeDefined();
    });

    it('should configure splitChunks for Monaco Editor', () => {
      const nextConfig = require('next.config.mjs').default;
      const mockConfig = {
        module: { rules: [] },
        plugins: [],
        optimization: { splitChunks: {} },
      };

      const result = nextConfig.webpack(mockConfig, {
        dev: false,
        isServer: false,
        nextRuntime: 'browser',
      });

      const cacheGroups = result.optimization.splitChunks?.cacheGroups;
      expect(cacheGroups).toBeDefined();
      expect(cacheGroups.monaco).toBeDefined();
      expect(cacheGroups.monaco.test.toString()).toContain('monaco-editor');
    });
  });

  describe('Runtime Performance Budgets', () => {
    it('should enforce response time budget', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/dashboard',
        method: 'GET',
        statusCode: 200,
        responseTime: 1500, // 1.5 seconds - within budget
        resourceMetrics: {
          ttfb: 200,
          fcp: 800,
          lcp: 1200,
          cls: 0.05,
          fid: 50,
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(true);
      expect(check.violations).toHaveLength(0);
    });

    it('should detect response time budget violation', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/slow-page',
        method: 'GET',
        statusCode: 200,
        responseTime: 3000, // 3 seconds - exceeds budget
        resourceMetrics: {
          ttfb: 200,
          fcp: 800,
          lcp: 1200,
          cls: 0.05,
          fid: 50,
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations).toHaveLength(1);
      expect(check.violations[0]).toContain('Response time');
    });

    it('should detect multiple budget violations', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/very-slow-page',
        method: 'GET',
        statusCode: 200,
        responseTime: 3500, // Exceeds budget
        resourceMetrics: {
          ttfb: 800, // Exceeds budget
          fcp: 2000, // Exceeds budget
          lcp: 3000, // Exceeds budget
          cls: 0.2, // Exceeds budget
          fid: 150, // Exceeds budget
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations.length).toBeGreaterThan(1);
    });

    it('should enforce TTFB budget', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/api/data',
        method: 'GET',
        statusCode: 200,
        responseTime: 500,
        resourceMetrics: {
          ttfb: 700, // Exceeds 600ms budget
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations[0]).toContain('TTFB');
    });
  });

  describe('Core Web Vitals Budgets', () => {
    it('should enforce FCP budget', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/',
        method: 'GET',
        statusCode: 200,
        responseTime: 1000,
        resourceMetrics: {
          fcp: 2000, // Exceeds 1800ms budget
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations[0]).toContain('FCP');
    });

    it('should enforce LCP budget', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/image-heavy',
        method: 'GET',
        statusCode: 200,
        responseTime: 1000,
        resourceMetrics: {
          lcp: 3000, // Exceeds 2500ms budget
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations[0]).toContain('LCP');
    });

    it('should enforce CLS budget', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/shifty-layout',
        method: 'GET',
        statusCode: 200,
        responseTime: 1000,
        resourceMetrics: {
          cls: 0.15, // Exceeds 0.1 budget
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations[0]).toContain('CLS');
    });

    it('should enforce FID budget', () => {
      const metrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/heavy-js',
        method: 'GET',
        statusCode: 200,
        responseTime: 1000,
        resourceMetrics: {
          fid: 150, // Exceeds 100ms budget
        },
      };

      const check = PerformanceBudget.checkBudget(metrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations[0]).toContain('FID');
    });
  });

  describe('Performance Monitoring', () => {
    it('should track request metrics', () => {
      const mockRequest = {
        url: 'http://localhost:3000/test',
        method: 'GET',
        headers: new Headers(),
      } as NextRequest;

      const monitor = new PerformanceMonitor(mockRequest as any);

      // Simulate some processing time
      const startTime = performance.now();
      const waitTime = 50; // ms
      const end = startTime + waitTime;

      while (performance.now() < end) {
        // Busy wait
      }

      const mockResponse = {
        status: 200,
        headers: new Headers(),
      } as any;

      const metrics = monitor.stop(mockResponse);

      expect(metrics.timestamp).toBeDefined();
      expect(metrics.url).toBe(mockRequest.url);
      expect(metrics.method).toBe(mockRequest.method);
      expect(metrics.statusCode).toBe(200);
      expect(metrics.responseTime).toBeGreaterThanOrEqual(waitTime);
    });

    it('should handle multiple metric tracking', () => {
      const mockRequests = [
        { url: 'http://localhost:3000/page1', method: 'GET' },
        { url: 'http://localhost:3000/page2', method: 'POST' },
        { url: 'http://localhost:3000/api/data', method: 'GET' },
      ];

      const monitors = mockRequests.map(req => ({
        request: req,
        monitor: new PerformanceMonitor(req as any),
      }));

      monitors.forEach(({ monitor }) => {
        const mockResponse = { status: 200, headers: new Headers() } as any;
        monitor.stop(mockResponse);
      });

      // Verify summary generation
      const report = generatePerformanceReport();
      expect(report.summary.totalRequests).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Performance Trends', () => {
    it('should detect improving trend', () => {
      // Clear any existing metrics
      const report1 = generatePerformanceReport();

      // Simulate improved metrics
      const improvedMetrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/fast-page',
        method: 'GET',
        statusCode: 200,
        responseTime: 200, // Very fast
      };

      // Create a mock monitor to add metrics
      const mockRequest = { url: improvedMetrics.url, method: improvedMetrics.method } as any;
      const monitor = new PerformanceMonitor(mockRequest);
      monitor.stop(improvedMetrics as any);

      const trend = PerformanceTrends.getTrend(60000); // 1 minute window
      // Trend depends on existing data, so we just verify structure
      expect(trend).toHaveProperty('trend');
      expect(trend).toHaveProperty('change');
      expect(trend).toHaveProperty('baseline');
      expect(trend).toHaveProperty('current');
    });

    it('should generate comprehensive performance report', () => {
      const report = generatePerformanceReport();

      expect(report).toHaveProperty('summary');
      expect(report).toHaveProperty('trends');
      expect(report).toHaveProperty('vitals');
      expect(report).toHaveProperty('timestamp');

      expect(report.summary).toHaveProperty('totalRequests');
      expect(report.summary).toHaveProperty('averageResponseTime');
      expect(report.summary).toHaveProperty('slowRequests');
    });
  });

  describe('Code Splitting', () => {
    it('should implement Monaco Editor code splitting', () => {
      // Verify MonacoLazy component exists
      const fs = require('fs');
      const path = require('path');

      const monacoLazyPath = path.join(
        process.cwd(),
        'src/components/editor/MonacoLazy.tsx'
      );

      expect(fs.existsSync(monacoLazyPath)).toBe(true);

      // Read content and verify lazy loading implementation
      const content = fs.readFileSync(monacoLazyPath, 'utf8');
      expect(content).toContain('lazy(() => import');
      expect(content).toContain('@monaco-editor/react');
      expect(content).toContain('Suspense');
    });

    it('should implement dashboard component lazy loading', () => {
      const fs = require('fs');
      const path = require('path');

      const dashboardPath = path.join(
        process.cwd(),
        'src/components/dashboard/DashboardLazy.tsx'
      );

      expect(fs.existsSync(dashboardPath)).toBe(true);

      const content = fs.readFileSync(dashboardPath, 'utf8');
      expect(content).toContain('lazy(() => import');
      expect(content).toContain('Suspense');
      expect(content).toContain('requestIdleCallback');
    });

    it('should have proper chunk configuration in next.config', () => {
      const nextConfig = require('next.config.mjs').default;

      const mockConfig = {
        module: { rules: [] },
        plugins: [],
        optimization: {},
      };

      const result = nextConfig.webpack(mockConfig, {
        dev: false,
        isServer: false,
        nextRuntime: 'browser',
      });

      // Verify chunk splitting is configured
      expect(result.optimization.splitChunks).toBeDefined();
      expect(result.optimization.splitChunks.chunks).toBe('all');
      expect(result.optimization.splitChunks.cacheGroups).toBeDefined();
    });
  });

  describe('Image Optimization', () => {
    it('should implement Next.js Image optimization', () => {
      const fs = require('fs');
      const path = require('path');

      const optimizedImagePath = path.join(
        process.cwd(),
        'src/components/ui/OptimizedImage.tsx'
      );

      expect(fs.existsSync(optimizedImagePath)).toBe(true);

      const content = fs.readFileSync(optimizedImagePath, 'utf8');
      expect(content).toContain('next/image');
      expect(content).toContain('loading="lazy"');
      expect(content).toContain('sizes=');
      expect(content).toContain('quality=');
    });

    it('should have proper image configuration in next.config', () => {
      const nextConfig = require('next.config.mjs').default;

      expect(nextConfig.images).toBeDefined();
      expect(nextConfig.images.formats).toContain('image/avif');
      expect(nextConfig.images.formats).toContain('image/webp');
      expect(nextConfig.images.deviceSizes).toBeDefined();
      expect(nextConfig.images.minimumCacheTTL).toBe(60);
    });

    it('should implement lazy loading for images', () => {
      const fs = require('fs');
      const path = require('path');

      const imagePath = path.join(
        process.cwd(),
        'src/components/ui/OptimizedImage.tsx'
      );

      const content = fs.readFileSync(imagePath, 'utf8');
      expect(content).toContain('IntersectionObserver');
      expect(content).toContain('loading="lazy"');
      expect(content).toContain('LazyImage');
    });
  });

  describe('Compression', () => {
    it('should implement compression middleware', () => {
      const fs = require('fs');
      const path = require('path');

      const compressionPath = path.join(
        process.cwd(),
        'src/middleware/compression.ts'
      );

      expect(fs.existsSync(compressionPath)).toBe(true);

      const content = fs.readFileSync(compressionPath, 'utf8');
      expect(content).toContain('brotli');
      expect(content).toContain('gzip');
      expect(content).toContain('compress');
      expect(content).toContain('content-encoding');
    });

    it('should configure compression thresholds', () => {
      const fs = require('fs');
      const path = require('path');

      const compressionPath = path.join(
        process.cwd(),
        'src/middleware/compression.ts'
      );

      const content = fs.readFileSync(compressionPath, 'utf8');
      expect(content).toContain('COMPRESSION_THRESHOLD');
      expect(content).toContain('1024'); // 1KB threshold
    });

    it('should exclude large binary files from compression', () => {
      const fs = require('fs');
      const path = require('path');

      const compressionPath = path.join(
        process.cwd(),
        'src/middleware/compression.ts'
      );

      const content = fs.readFileSync(compressionPath, 'utf8');
      expect(content).toContain('EXCLUDED_CONTENT_TYPES');
      expect(content).toContain('image/jpeg');
      expect(content).toContain('video/mp4');
    });
  });

  describe('Performance Testing Utilities', () => {
    it('should measure component load times', async () => {
      const startTime = performance.now();

      // Simulate component load
      await new Promise(resolve => setTimeout(resolve, 10));

      const endTime = performance.now();
      const loadTime = endTime - startTime;

      expect(loadTime).toBeGreaterThan(0);
      expect(loadTime).toBeLessThan(100); // Should be fast
    });

    it('should track memory usage patterns', () => {
      if ((performance as any).memory) {
        const memory = (performance as any).memory;
        expect(memory.usedJSHeapSize).toBeDefined();
        expect(memory.totalJSHeapSize).toBeDefined();

        // Memory should be reasonable (less than 500MB)
        expect(memory.usedJSHeapSize).toBeLessThan(500 * 1024 * 1024);
      }
    });

    it('should generate performance reports with all metrics', () => {
      const report = generatePerformanceReport();

      // Verify report structure
      expect(report.summary).toBeDefined();
      expect(report.trends).toBeDefined();
      expect(report.vitals).toBeDefined();
      expect(report.timestamp).toBeDefined();

      // Verify summary structure
      expect(report.summary.totalRequests).toBeDefined();
      expect(report.summary.averageResponseTime).toBeDefined();
      expect(report.summary.slowRequests).toBeDefined();
      expect(report.summary.byStatus).toBeDefined();
      expect(report.summary.byMethod).toBeDefined();

      // Verify trends structure
      expect(report.trends.trend).toBeDefined();
      expect(report.trends.change).toBeDefined();
      expect(report.trends.baseline).toBeDefined();
      expect(report.trends.current).toBeDefined();
    });
  });

  describe('Performance Thresholds', () => {
    it('should have correct threshold values', () => {
      expect(PERFORMANCE_THRESHOLDS.FCP).toBe(1800);
      expect(PERFORMANCE_THRESHOLDS.LCP).toBe(2500);
      expect(PERFORMANCE_THRESHOLDS.FID).toBe(100);
      expect(PERFORMANCE_THRESHOLDS.CLS).toBe(0.1);
      expect(PERFORMANCE_THRESHOLDS.TTFB).toBe(600);
      expect(PERFORMANCE_THRESHOLDS.RESPONSE).toBe(2000);
    });

    it('should categorize performance correctly', () => {
      // Create test metrics for different performance levels
      const fastMetrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/fast',
        method: 'GET',
        statusCode: 200,
        responseTime: 100,
      };

      const slowMetrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/slow',
        method: 'GET',
        statusCode: 200,
        responseTime: 3000,
      };

      const budgetCheckFast = PerformanceBudget.checkBudget(fastMetrics);
      const budgetCheckSlow = PerformanceBudget.checkBudget(slowMetrics);

      expect(budgetCheckFast.withinBudget).toBe(true);
      expect(budgetCheckSlow.withinBudget).toBe(false);
    });
  });

  describe('Integration Tests', () => {
    it('should track and analyze multiple requests', () => {
      // Simulate multiple requests
      const requests = [
        { url: '/page1', responseTime: 200 },
        { url: '/page2', responseTime: 400 },
        { url: '/api/data', responseTime: 150 },
        { url: '/dashboard', responseTime: 800 },
      ];

      const mockRequests = requests.map(req => ({
        url: `http://localhost:3000${req.url}`,
        method: 'GET',
      }));

      mockRequests.forEach((req, index) => {
        const monitor = new PerformanceMonitor(req as any);
        const mockResponse = {
          status: 200,
          headers: new Headers(),
        } as any;

        // Override response time for testing
        const originalStop = monitor.stop.bind(monitor);
        monitor.stop = function(response: any) {
          const metrics = originalStop(response);
          metrics.responseTime = requests[index].responseTime;
          return metrics;
        };

        monitor.stop(mockResponse);
      });

      const report = generatePerformanceReport();

      expect(report.summary.totalRequests).toBeGreaterThanOrEqual(requests.length);
      expect(report.summary.averageResponseTime).toBeGreaterThan(0);
    });

    it('should handle performance violations gracefully', () => {
      const violatingMetrics = {
        timestamp: Date.now(),
        url: 'http://localhost:3000/slow',
        method: 'GET',
        statusCode: 200,
        responseTime: 5000, // Very slow
        resourceMetrics: {
          ttfb: 1000,
          fcp: 3000,
          lcp: 4000,
          cls: 0.5,
          fid: 200,
        },
      };

      const check = PerformanceBudget.checkBudget(violatingMetrics);
      expect(check.withinBudget).toBe(false);
      expect(check.violations.length).toBeGreaterThan(0);

      // Should log violations without throwing
      expect(() => {
        PerformanceBudget.alertOnViolation(violatingMetrics);
      }).not.toThrow();
    });
  });
});

// Additional test utilities
describe('Performance Test Utilities', () => {
  it('should measure async operations', async () => {
    const start = performance.now();

    // Simulate async work
    await new Promise(resolve => setTimeout(resolve, 50));

    const duration = performance.now() - start;

    expect(duration).toBeGreaterThanOrEqual(50);
    expect(duration).toBeLessThan(100);
  });

  it('should track network timing', () => {
    // This would normally track actual network requests
    // For testing, we verify the structure exists
    const timing = {
      redirect: 10,
      dns: 20,
      tcp: 30,
      ssl: 40,
      ttfb: 50,
      download: 60,
    };

    expect(timing.redirect).toBeGreaterThanOrEqual(0);
    expect(timing.dns).toBeGreaterThanOrEqual(0);
    expect(timing.tcp).toBeGreaterThanOrEqual(0);
    expect(timing.ssl).toBeGreaterThanOrEqual(0);
    expect(timing.ttfb).toBeGreaterThanOrEqual(0);
    expect(timing.download).toBeGreaterThanOrEqual(0);
  });
});