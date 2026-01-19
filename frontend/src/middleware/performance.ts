/**
 * Performance Monitoring Middleware
 * Tracks and monitors application performance metrics
 * Task: T135
 *
 * Last Updated: 2026-01-15
 */

import { NextRequest, NextResponse } from 'next/server';

export interface PerformanceMetrics {
  timestamp: number;
  url: string;
  method: string;
  statusCode: number;
  responseTime: number;
  resourceMetrics?: ResourceMetrics;
  userTiming?: UserTimingMetrics;
  networkTiming?: NetworkTimingMetrics;
}

export interface ResourceMetrics {
  fcp: number; // First Contentful Paint
  lcp: number; // Largest Contentful Paint
  cls: number; // Cumulative Layout Shift
  fid: number; // First Input Delay
  inp: number; // Interaction to Next Paint
  ttfb: number; // Time to First Byte
  dns: number; // DNS lookup time
  tcp: number; // TCP connection time
  ssl: number; // SSL/TLS time
}

export interface UserTimingMetrics {
  [key: string]: number;
}

export interface NetworkTimingMetrics {
  redirect: number;
  dns: number;
  tcp: number;
  ssl: number;
  ttfb: number;
  download: number;
}

// Performance thresholds (in milliseconds)
const PERFORMANCE_THRESHOLDS = {
  FCP: 1800, // First Contentful Paint
  LCP: 2500, // Largest Contentful Paint
  FID: 100,  // First Input Delay
  CLS: 0.1,  // Cumulative Layout Shift
  TTFB: 600, // Time to First Byte
  RESPONSE: 2000, // Total response time
};

// Store for aggregated metrics
const metricsStore: PerformanceMetrics[] = [];

/**
 * Performance monitoring utility
 */
class PerformanceMonitor {
  private startTime: number;
  private request: NextRequest;

  constructor(request: NextRequest) {
    this.startTime = performance.now();
    this.request = request;
  }

  /**
   * Measure response time
   */
  stop(response: NextResponse): PerformanceMetrics {
    const endTime = performance.now();
    const responseTime = endTime - this.startTime;

    const metrics: PerformanceMetrics = {
      timestamp: Date.now(),
      url: this.request.url,
      method: this.request.method,
      statusCode: response.status,
      responseTime,
    };

    // Add to store
    metricsStore.push(metrics);

    // Log if slow
    if (responseTime > PERFORMANCE_THRESHOLDS.RESPONSE) {
      console.warn(`[PERF] Slow response detected: ${responseTime.toFixed(2)}ms for ${this.request.url}`);
    }

    // Clean old metrics (keep last 1000)
    if (metricsStore.length > 1000) {
      metricsStore.shift();
    }

    return metrics;
  }

  /**
   * Extract performance entries from navigation timing
   */
  static extractNavigationTiming(): Partial<NetworkTimingMetrics> {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

    if (!navigation) {
      return {};
    }

    return {
      redirect: navigation.redirectEnd - navigation.redirectStart,
      dns: navigation.domainLookupEnd - navigation.domainLookupStart,
      tcp: navigation.connectEnd - navigation.connectStart,
      ssl: navigation.secureConnectionStart > 0 ? navigation.connectEnd - navigation.secureConnectionStart : 0,
      ttfb: navigation.responseStart - navigation.requestStart,
      download: navigation.responseEnd - navigation.responseStart,
    };
  }

  /**
   * Extract resource timing for specific resource type
   */
  static extractResourceTiming(resourceType?: string): Partial<ResourceMetrics> {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

    if (resourceType) {
      resources.filter(r => r.initiatorType === resourceType);
    }

    if (resources.length === 0) {
      return {};
    }

    const latest = resources[resources.length - 1];

    return {
      dns: latest.domainLookupEnd - latest.domainLookupStart,
      tcp: latest.connectEnd - latest.connectStart,
      ssl: latest.secureConnectionStart > 0 ? latest.connectEnd - latest.secureConnectionStart : 0,
      ttfb: latest.responseStart - latest.requestStart,
      download: latest.responseEnd - latest.responseStart,
    };
  }

  /**
   * Calculate Core Web Vitals from stored metrics
   */
  static calculateCoreWebVitals(): Partial<ResourceMetrics> {
    const metrics = metricsStore.slice(-10); // Last 10 requests

    if (metrics.length === 0) {
      return {};
    }

    // Simple calculation - in production, use proper web-vitals library
    const fcp = metrics.reduce((sum, m) => sum + (m.resourceMetrics?.fcp || 0), 0) / metrics.length;
    const lcp = metrics.reduce((sum, m) => sum + (m.resourceMetrics?.lcp || 0), 0) / metrics.length;
    const cls = metrics.reduce((sum, m) => sum + (m.resourceMetrics?.cls || 0), 0) / metrics.length;
    const fid = metrics.reduce((sum, m) => sum + (m.resourceMetrics?.fid || 0), 0) / metrics.length;

    return { fcp, lcp, cls, fid };
  }
}

/**
 * Extract client hints from headers
 */
function extractClientHints(request: NextRequest): Partial<ResourceMetrics> {
  const hints: Partial<ResourceMetrics> = {};

  // Network Information API
  const saveData = request.headers.get('sec-ch-ua-data-saver') === 'true';
  const downlink = parseFloat(request.headers.get('sec-ch-ua-downlink') || '0');
  const ect = request.headers.get('sec-ch-ua-ect') || '';
  const rtt = parseInt(request.headers.get('sec-ch-ua-rtt') || '0', 10);

  // Device hints
  const dpr = parseFloat(request.headers.get('sec-ch-dpr') || '1');
  const width = parseInt(request.headers.get('sec-ch-viewport-width') || '0', 10);

  // Store as custom metrics
  (hints as any).saveData = saveData;
  (hints as any).downlink = downlink;
  (hints as any).ect = ect;
  (hints as any).rtt = rtt;
  (hints as any).dpr = dpr;
  (hints as any).viewportWidth = width;

  return hints;
}

/**
 * Performance analysis utility
 */
class PerformanceAnalyzer {
  static analyzeMetrics(metrics: PerformanceMetrics): {
    grade: 'A' | 'B' | 'C' | 'D' | 'F';
    issues: string[];
    recommendations: string[];
  } {
    const issues: string[] = [];
    const recommendations: string[] = [];

    // Check response time
    if (metrics.responseTime > PERFORMANCE_THRESHOLDS.RESPONSE) {
      issues.push(`Response time too slow: ${metrics.responseTime.toFixed(2)}ms`);
      recommendations.push('Enable caching, optimize database queries, consider CDN');
    }

    // Check TTFB
    if (metrics.resourceMetrics?.ttfb > PERFORMANCE_THRESHOLDS.TTFB) {
      issues.push(`Time to First Byte too slow: ${metrics.resourceMetrics.ttfb.toFixed(2)}ms`);
      recommendations.push('Optimize server response time, enable compression, use HTTP/2');
    }

    // Calculate grade
    let grade: 'A' | 'B' | 'C' | 'D' | 'F' = 'A';
    if (metrics.responseTime > 2000) grade = 'F';
    else if (metrics.responseTime > 1000) grade = 'D';
    else if (metrics.responseTime > 500) grade = 'C';
    else if (metrics.responseTime > 250) grade = 'B';

    return { grade, issues, recommendations };
  }

  static getSummary(): {
    totalRequests: number;
    averageResponseTime: number;
    slowRequests: number;
    byStatus: { [status: string]: number };
    byMethod: { [method: string]: number };
  } {
    const total = metricsStore.length;
    if (total === 0) {
      return {
        totalRequests: 0,
        averageResponseTime: 0,
        slowRequests: 0,
        byStatus: {},
        byMethod: {},
      };
    }

    const sumResponseTime = metricsStore.reduce((sum, m) => sum + m.responseTime, 0);
    const averageResponseTime = sumResponseTime / total;

    const slowRequests = metricsStore.filter(m => m.responseTime > PERFORMANCE_THRESHOLDS.RESPONSE).length;

    const byStatus = metricsStore.reduce((acc, m) => {
      acc[m.statusCode] = (acc[m.statusCode] || 0) + 1;
      return acc;
    }, {} as { [status: string]: number });

    const byMethod = metricsStore.reduce((acc, m) => {
      acc[m.method] = (acc[m.method] || 0) + 1;
      return acc;
    }, {} as { [method: string]: number });

    return {
      totalRequests: total,
      averageResponseTime,
      slowRequests,
      byStatus,
      byMethod,
    };
  }

  static reset(): void {
    metricsStore.length = 0;
  }
}

/**
 * Performance headers middleware
 */
export function addPerformanceHeaders(
  request: NextRequest,
  response: NextResponse
): NextResponse {
  const url = new URL(request.url);

  // Add timing headers for debugging
  if (process.env.NODE_ENV === 'development') {
    response.headers.set('x-response-time', `${Date.now()}`);
  }

  // Add server-timing header
  const serverTiming = response.headers.get('server-timing');
  if (serverTiming) {
    response.headers.set(
      'server-timing',
      `${serverTiming}, total;dur=${Date.now()}`
    );
  } else {
    response.headers.set('server-timing', `total;dur=${Date.now()}`);
  }

  // Add resource hints for critical assets
  if (url.pathname.includes('_next')) {
    response.headers.set(
      'link',
      '</_next/static/css/main.css>; rel=preload; as=style, </_next/static/js/main.js>; rel=preload; as=script'
    );
  }

  return response;
}

/**
 * Resource timing middleware
 */
export async function trackResourceTiming(
  request: NextRequest,
  response: NextResponse
): Promise<NextResponse> {
  const url = new URL(request.url);
  const path = url.pathname;

  // Only track for HTML pages and API routes
  const isPage = !path.startsWith('/_next') && !path.startsWith('/api');
  const isApi = path.startsWith('/api');

  if (!isPage && !isApi) {
    return response;
  }

  // Add performance budget headers
  if (isPage) {
    // Critical resources
    const criticalCss = '/_next/static/css/main.css';
    const criticalJs = '/_next/static/js/main.js';

    response.headers.set(
      'link',
      `<${criticalCss}>; rel=preload; as=style, <${criticalJs}>; rel=preload; as=script`
    );

    // Preconnect to external resources
    response.headers.set(
      'link',
      `<https://fonts.googleapis.com>; rel=preconnect, <https://fonts.gstatic.com>; rel=preconnect`
    );
  }

  return response;
}

/**
 * Main Performance Middleware
 */
export async function performanceMiddleware(
  request: NextRequest
): Promise<NextResponse> {
  const monitor = new PerformanceMonitor(request);

  // Get client hints
  const clientHints = extractClientHints(request);

  // Create response (this would normally be done by your route handlers)
  const response = NextResponse.next();

  // Add performance headers
  const responseWithHeaders = addPerformanceHeaders(request, response);

  // Track resource timing
  const responseWithTracking = await trackResourceTiming(request, responseWithHeaders);

  // Stop monitoring and get metrics
  const metrics = monitor.stop(responseWithTracking);

  // Add client hints to metrics
  metrics.resourceMetrics = {
    ...(metrics.resourceMetrics || {}),
    ...clientHints,
  } as ResourceMetrics;

  // Add to response headers for debugging
  if (process.env.NODE_ENV === 'development') {
    const analysis = PerformanceAnalyzer.analyzeMetrics(metrics);
    responseWithTracking.headers.set('x-performance-grade', analysis.grade);
    if (analysis.issues.length > 0) {
      responseWithTracking.headers.set('x-performance-issues', analysis.issues.join('; '));
    }
  }

  return responseWithTracking;
}

/**
 * Performance Monitoring API Route Handler
 * This would be used in /api/performance/route.ts
 */
export async function handlePerformanceRequest(request: NextRequest) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  // Get action from query params
  const action = searchParams.get('action') || 'summary';

  switch (action) {
    case 'summary': {
      const summary = PerformanceAnalyzer.getSummary();
      return NextResponse.json(summary);
    }

    case 'details': {
      const limit = parseInt(searchParams.get('limit') || '50', 10);
      const recent = metricsStore.slice(-limit);
      return NextResponse.json(recent);
    }

    case 'vitals': {
      const vitals = PerformanceAnalyzer.calculateCoreWebVitals();
      return NextResponse.json(vitals);
    }

    case 'analyze': {
      const since = parseInt(searchParams.get('since') || '0', 10);
      const filtered = metricsStore.filter(m => m.timestamp >= since);

      const analysis = filtered.map(m => ({
        ...m,
        analysis: PerformanceAnalyzer.analyzeMetrics(m),
      }));

      return NextResponse.json(analysis);
    }

    case 'reset': {
      PerformanceAnalyzer.reset();
      return NextResponse.json({ success: true, message: 'Metrics reset' });
    }

    default:
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
  }
}

/**
 * Performance budget checker
 */
export class PerformanceBudget {
  static budgets = {
    MAX_RESPONSE_TIME: 2000, // ms
    MAX_TTFB: 600, // ms
    MAX_FCP: 1800, // ms
    MAX_LCP: 2500, // ms
    MAX_CLS: 0.1, // score
  };

  static checkBudget(metrics: PerformanceMetrics): {
    withinBudget: boolean;
    violations: string[];
  } {
    const violations: string[] = [];

    if (metrics.responseTime > this.budgets.MAX_RESPONSE_TIME) {
      violations.push(`Response time ${metrics.responseTime.toFixed(0)}ms exceeds ${this.budgets.MAX_RESPONSE_TIME}ms budget`);
    }

    if (metrics.resourceMetrics?.ttfb > this.budgets.MAX_TTFB) {
      violations.push(`TTFB ${metrics.resourceMetrics.ttfb.toFixed(0)}ms exceeds ${this.budgets.MAX_TTFB}ms budget`);
    }

    if (metrics.resourceMetrics?.fcp > this.budgets.MAX_FCP) {
      violations.push(`FCP ${metrics.resourceMetrics.fcp.toFixed(0)}ms exceeds ${this.budgets.MAX_FCP}ms budget`);
    }

    if (metrics.resourceMetrics?.lcp > this.budgets.MAX_LCP) {
      violations.push(`LCP ${metrics.resourceMetrics.lcp.toFixed(0)}ms exceeds ${this.budgets.MAX_LCP}ms budget`);
    }

    if (metrics.resourceMetrics?.cls > this.budgets.MAX_CLS) {
      violations.push(`CLS ${metrics.resourceMetrics.cls.toFixed(3)} exceeds ${this.budgets.MAX_CLS} budget`);
    }

    return {
      withinBudget: violations.length === 0,
      violations,
    };
  }

  static alertOnViolation(metrics: PerformanceMetrics): void {
    const check = this.checkBudget(metrics);

    if (!check.withinBudget) {
      console.error('🚨 Performance budget violation:', {
        url: metrics.url,
        violations: check.violations,
        metrics,
      });

      // In production, send to monitoring service
      // Sentry.captureMessage('Performance budget violation', 'warning');
    }
  }
}

/**
 * Performance trend analyzer
 */
export class PerformanceTrends {
  static getTrend(timeWindow: number = 3600000): { // 1 hour default
    trend: 'improving' | 'degrading' | 'stable';
    change: number;
    baseline: number;
    current: number;
  } {
    const now = Date.now();
    const cutoff = now - timeWindow;

    const recent = metricsStore.filter(m => m.timestamp >= cutoff);
    const previous = metricsStore.filter(m => m.timestamp >= cutoff - timeWindow && m.timestamp < cutoff);

    if (recent.length < 10 || previous.length < 10) {
      return {
        trend: 'stable',
        change: 0,
        baseline: 0,
        current: 0,
      };
    }

    const recentAvg = recent.reduce((sum, m) => sum + m.responseTime, 0) / recent.length;
    const previousAvg = previous.reduce((sum, m) => sum + m.responseTime, 0) / previous.length;

    const change = ((recentAvg - previousAvg) / previousAvg) * 100;

    return {
      trend: change < -5 ? 'improving' : change > 5 ? 'degrading' : 'stable',
      change,
      baseline: previousAvg,
      current: recentAvg,
    };
  }
}

/**
 * Helper function to generate performance report
 */
export function generatePerformanceReport(): {
  summary: ReturnType<typeof PerformanceAnalyzer.getSummary>;
  trends: ReturnType<typeof PerformanceTrends.getTrend>;
  vitals: ReturnType<typeof PerformanceAnalyzer.calculateCoreWebVitals>;
  timestamp: number;
} {
  return {
    summary: PerformanceAnalyzer.getSummary(),
    trends: PerformanceTrends.getTrend(),
    vitals: PerformanceAnalyzer.calculateCoreWebVitals(),
    timestamp: Date.now(),
  };
}