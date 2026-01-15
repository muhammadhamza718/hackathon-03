# Verification Plan for Real-Time Frontend

**Milestone 5: Real-Time Frontend**
**Status:** Planning Phase
**Last Updated:** 2026-01-15
**Owner:** Frontend Team

---

## Executive Summary

This document defines the automated verification plan for the Real-Time Frontend milestone. The verification strategy focuses on performance metrics (editor load time <200ms, feedback latency <1s), functional correctness, and integration reliability. All checks will be implemented as automated scripts that can run in CI/CD pipelines.

---

## 1. Performance Verification

### 1.1 Monaco Editor Load Time (<200ms)

**Objective:** Verify Monaco Editor loads and initializes within 200ms from page load.

#### 1.1.1 Measurement Strategy
```javascript
// Performance marks for Monaco loading
performance.mark('monaco-start-load');
performance.mark('monaco-editor-ready');

// Calculate: editorLoadTime = monaco-editor-ready - monaco-start-load
```

#### 1.1.2 Automated Test Script
```javascript
// scripts/verify/editor-load-time.js
const { performance } = require('perf_hooks');
const puppeteer = require('puppeteer');

class EditorLoadTest {
  constructor() {
    this.threshold = 200; // ms
    this.samples = 10; // Run 10 times for consistency
  }

  async run() {
    const results = [];

    for (let i = 0; i < this.samples; i++) {
      const time = await this.measureLoadTime();
      results.push(time);

      // Cool down between runs
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    const stats = this.calculateStats(results);
    return this.validate(stats);
  }

  async measureLoadTime() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Enable performance metrics
    await page.tracing.start({ path: 'trace.json' });

    const loadTime = await page.evaluate(() => {
      return new Promise((resolve) => {
        performance.mark('monaco-start-load');

        // Dynamic import of Monaco
        import('/monaco-loader').then(() => {
          // Wait for editor to be fully initialized
          const checkReady = () => {
            if (window.monacoEditor && window.monacoEditor.getModel()) {
              performance.mark('monaco-editor-ready');
              const measure = performance.measure(
                'monaco-load',
                'monaco-start-load',
                'monaco-editor-ready'
              );
              resolve(measure.duration);
            } else {
              setTimeout(checkReady, 10);
            }
          };
          checkReady();
        });
      });
    });

    await browser.close();
    return loadTime;
  }

  calculateStats(times) {
    const sum = times.reduce((a, b) => a + b, 0);
    const avg = sum / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    return { times, avg, min, max };
  }

  validate(stats) {
    const passed = stats.avg < this.threshold;

    return {
      passed,
      threshold: this.threshold,
      actual: stats.avg,
      min: stats.min,
      max: stats.max,
      samples: this.samples,
      details: passed ? '✅ PASS' : '❌ FAIL'
    };
  }
}

module.exports = EditorLoadTest;
```

#### 1.1.3 CI/CD Integration
```yaml
# .github/workflows/verify-performance.yml
name: Performance Verification
on: [push, pull_request]

jobs:
  editor-load-time:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Start dev server
        run: npm run start &
        env:
          PORT: 3000

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run editor load test
        run: node scripts/verify/editor-load-time.js

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: editor-load-report
          path: reports/editor-load-*.json
```

### 1.2 End-to-End Feedback Latency (<1s)

**Objective:** Verify real-time feedback from submission to UI update occurs within 1 second.

#### 1.2.1 Measurement Strategy
```javascript
// Latency measurement points
const measurementPoints = {
  submit: 'feedback-submitted',           // User clicks submit
  request: 'feedback-request-sent',       // HTTP request sent
  response: 'feedback-response-received', // HTTP response received
  sse: 'feedback-sse-event',              // SSE event received
  ui: 'feedback-ui-updated'              // UI fully updated
};

// Total latency = ui - submit
// Breakdown: request + response + sse + ui
```

#### 1.2.2 Automated Test Script
```javascript
// scripts/verify/feedback-latency.js
const WebSocket = require('ws');
const axios = require('axios');

class FeedbackLatencyTest {
  constructor() {
    this.threshold = 1000; // 1 second
    this.backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    this.sseUrl = process.env.SSE_URL || 'http://localhost:8000/sse';
  }

  async run() {
    const testScenarios = [
      { type: 'simple-feedback', code: 'print("hello")' },
      { type: 'complex-analysis', code: 'def solve():\n    # Complex algorithm\n    pass' },
      { type: 'large-submission', code: '# Large file\n' + 'x = 1\n'.repeat(100) }
    ];

    const results = [];

    for (const scenario of testScenarios) {
      const result = await this.measureScenario(scenario);
      results.push(result);
    }

    return this.validateAll(results);
  }

  async measureScenario(scenario) {
    const timeline = {};

    // 1. Start SSE listener
    const ssePromise = this.listenForSSE(scenario.type);

    // 2. Record submission start
    timeline.submit = Date.now();

    // 3. Submit feedback request
    timeline.request = Date.now();
    const response = await axios.post(
      `${this.backendUrl}/api/feedback/analyze`,
      { code: scenario.code },
      { headers: { 'Authorization': `Bearer ${this.getTestToken()}` } }
    );
    timeline.response = Date.now();

    // 4. Wait for SSE event
    const sseEvent = await ssePromise;
    timeline.sse = Date.now();

    // 5. Simulate UI update completion
    timeline.ui = Date.now() + 100; // Add 100ms for React re-render

    // Calculate breakdown
    const breakdown = {
      request: timeline.request - timeline.submit,
      network: timeline.response - timeline.request,
      processing: timeline.sse - timeline.response,
      ui: timeline.ui - timeline.sse,
      total: timeline.ui - timeline.submit
    };

    return {
      scenario: scenario.type,
      timeline,
      breakdown,
      passed: breakdown.total < this.threshold
    };
  }

  listenForSSE(eventType) {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(this.sseUrl);

      const timeout = setTimeout(() => {
        eventSource.close();
        reject(new Error('SSE timeout'));
      }, 5000);

      eventSource.addEventListener(eventType, (event) => {
        clearTimeout(timeout);
        eventSource.close();
        resolve(JSON.parse(event.data));
      });

      eventSource.onerror = (error) => {
        clearTimeout(timeout);
        eventSource.close();
        reject(error);
      };
    });
  }

  getTestToken() {
    // Generate JWT for testing
    const jwt = require('jsonwebtoken');
    return jwt.sign(
      { sub: 'test-user', role: 'student' },
      process.env.JWT_SECRET || 'test-secret',
      { expiresIn: '1h' }
    );
  }

  validateAll(results) {
    const overallPassed = results.every(r => r.passed);
    const breakdowns = results.map(r => r.breakdown);

    return {
      passed: overallPassed,
      threshold: this.threshold,
      scenarios: results,
      averages: {
        total: breakdowns.reduce((sum, b) => sum + b.total, 0) / breakdowns.length,
        network: breakdowns.reduce((sum, b) => sum + b.network, 0) / breakdowns.length,
        processing: breakdowns.reduce((sum, b) => sum + b.processing, 0) / breakdowns.length,
        ui: breakdowns.reduce((sum, b) => sum + b.ui, 0) / breakdowns.length
      }
    };
  }
}

module.exports = FeedbackLatencyTest;
```

#### 1.2.3 Synthetic Monitoring
```javascript
// scripts/monitor/synthetic-monitor.js
const cron = require('node-cron');
const { FeedbackLatencyTest } = require('./feedback-latency');

class SyntheticMonitor {
  constructor() {
    this.interval = '*/5 * * * *'; // Every 5 minutes
  }

  start() {
    cron.schedule(this.interval, async () => {
      console.log('Running synthetic latency monitor...');

      const test = new FeedbackLatencyTest();
      const result = await test.run();

      // Send metrics to monitoring system
      this.reportMetrics(result);

      // Alert if threshold breached
      if (!result.passed) {
        this.sendAlert(result);
      }
    });
  }

  reportMetrics(result) {
    // Send to Prometheus/Grafana
    const metrics = {
      feedback_latency_total: result.averages.total,
      feedback_latency_network: result.averages.network,
      feedback_latency_processing: result.averages.processing,
      feedback_latency_ui: result.averages.ui,
      feedback_latency_threshold: 1000,
      feedback_latency_passed: result.passed ? 1 : 0
    };

    // Push to Prometheus Pushgateway
    // curl -X POST --data-binary @metrics.txt http://pushgateway:9091/metrics/job/feedback-monitor
  }

  sendAlert(result) {
    // Send to Slack/Email/PagerDuty
    const message = `🚨 Feedback Latency Alert
    Threshold: ${result.threshold}ms
    Actual: ${result.averages.total}ms
    Scenarios Failed: ${result.scenarios.filter(s => !s.passed).length}/${result.scenarios.length}
    `;

    console.error(message);
    // Integrate with your alerting system
  }
}

module.exports = SyntheticMonitor;
```

---

## 2. Functional Verification

### 2.1 Monaco Editor Functionality

**Objective:** Verify Monaco Editor loads correctly and provides expected features.

#### 2.1.1 Core Functionality Tests
```javascript
// scripts/verify/monaco-functional.js
describe('Monaco Editor Functional Tests', () => {
  let page;

  beforeAll(async () => {
    page = await browser.newPage();
    await page.goto('http://localhost:3000');
  });

  test('Monaco Editor loads without errors', async () => {
    const errors = [];
    page.on('pageerror', error => errors.push(error));

    await page.waitForSelector('#monaco-editor', { timeout: 5000 });
    expect(errors).toHaveLength(0);
  });

  test('Python syntax highlighting works', async () => {
    const code = 'def hello():\n    print("world")';

    await page.evaluate((code) => {
      window.monacoEditor.setValue(code);
    }, code);

    // Check if tokens are properly highlighted
    const tokens = await page.evaluate(() => {
      const model = window.monacoEditor.getModel();
      const tokens = window.monaco.editor.tokenize(model.getValue(), 'python');
      return tokens;
    });

    expect(tokens.length).toBeGreaterThan(0);
  });

  test('Autocomplete suggestions appear', async () => {
    await page.evaluate(() => {
      window.monacoEditor.setValue('import math\nmath.');
    });

    // Trigger autocomplete
    await page.keyboard.type('s');
    await page.waitForTimeout(100);

    const suggestionsVisible = await page.evaluate(() => {
      const editor = window.monacoEditor;
      const position = editor.getPosition();
      const suggestions = editor.getContribution('editor.contrib.suggestController');
      return suggestions && suggestions.visible;
    });

    expect(suggestionsVisible).toBe(true);
  });

  test('Error linting works', async () => {
    const code = 'def broken():\n    x = undefined_variable\n    return x';

    await page.evaluate((code) => {
      window.monacoEditor.setValue(code);
    }, code);

    await page.waitForTimeout(500); // Wait for linting

    const markers = await page.evaluate(() => {
      const model = window.monacoEditor.getModel();
      return window.monaco.editor.getModelMarkers({ resource: model.uri });
    });

    expect(markers.length).toBeGreaterThan(0);
    expect(markers.some(m => m.severity === 8)).toBe(true); // Error severity
  });

  test('Formatting on type works', async () => {
    await page.evaluate(() => {
      window.monacoEditor.setValue('if True:\nprint("test")');
    });

    await page.keyboard.press('Enter');
    await page.waitForTimeout(100);

    const content = await page.evaluate(() => {
      return window.monacoEditor.getValue();
    });

    // Should be properly indented
    expect(content).toContain('    print');
  });
});
```

#### 2.1.2 Performance Benchmarks
```javascript
// scripts/benchmarks/monaco-benchmarks.js
const Benchmark = require('benchmark');

const benchmarks = {
  'editor-initialization': () => {
    const suite = new Benchmark.Suite();

    suite.add('Monaco#init', () => {
      // Measure editor initialization
      const start = performance.now();

      return new Promise((resolve) => {
        import('/monaco-loader').then(() => {
          const end = performance.now();
          resolve(end - start);
        });
      });
    });

    return suite;
  },

  'syntax-highlighting': () => {
    const codeSamples = [
      'print("hello")',
      'def func():\n    return 42',
      'class MyClass:\n    def __init__(self):\n        self.x = 1'
    ];

    const suite = new Benchmark.Suite();

    codeSamples.forEach((code, i) => {
      suite.add(`Highlighting#${i}`, () => {
        const start = performance.now();
        // Simulate highlighting
        const tokens = window.monaco.editor.tokenize(code, 'python');
        const end = performance.now();
        return end - start;
      });
    });

    return suite;
  }
};
```

### 2.2 Real-Time Event Processing

**Objective:** Verify SSE connection, event processing, and UI updates work correctly.

#### 2.2.1 SSE Connection Tests
```javascript
// scripts/verify/sse-connection.js
describe('SSE Connection Tests', () => {
  test('Establishes SSE connection', async () => {
    const sseEvents = [];

    await page.evaluate(() => {
      window.eventSource = new EventSource('/api/sse');
      window.eventSource.onmessage = (event) => {
        window.sseEvents = window.sseEvents || [];
        window.sseEvents.push(JSON.parse(event.data));
      };
    });

    // Trigger an event
    await page.evaluate(() => {
      fetch('/api/feedback/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: 'print("test")' })
      });
    });

    // Wait for SSE event
    await page.waitForFunction(
      () => window.sseEvents && window.sseEvents.length > 0,
      { timeout: 5000 }
    );

    const events = await page.evaluate(() => window.sseEvents);
    expect(events.length).toBeGreaterThan(0);
    expect(events[0].type).toBeDefined();
  });

  test('Reconnects on connection loss', async () => {
    // Simulate network disconnect
    await page.setOfflineMode(true);
    await page.waitForTimeout(1000);
    await page.setOfflineMode(false);

    // Should reconnect automatically
    const reconnected = await page.waitForFunction(
      () => window.eventSource.readyState === 1, // CONNECTING
      { timeout: 10000 }
    );

    expect(reconnected).toBe(true);
  });
});
```

---

## 3. Integration Verification

### 3.1 Backend Integration Tests

**Objective:** Verify frontend-backend communication works correctly.

#### 3.1.1 API Contract Tests
```yaml
# scripts/verify/api-contracts.yml
openapi: 3.0.0
info:
  title: Frontend API Contract Tests
  version: 1.0.0

paths:
  /api/feedback/analyze:
    post:
      x-test:
        description: Feedback analysis endpoint
        assertions:
          - status: 200
          - schema:
              type: object
              properties:
                analysis:
                  type: object
                  required: [score, suggestions, errors]
                latency:
                  type: number
                  maximum: 1000
        payload:
          code: "print('hello')"
        headers:
          Authorization: "Bearer ${TEST_TOKEN}"
```

#### 3.1.2 Dapr Pub/Sub Integration
```javascript
// scripts/verify/dapr-integration.js
const { DaprClient } = require('@dapr/dapr');

class DaprIntegrationTest {
  constructor() {
    this.client = new DaprClient({
      daprHost: process.env.DAPR_HOST || 'localhost',
      daprPort: process.env.DAPR_PORT || '3500'
    });
  }

  async testPubSub() {
    const testEvent = {
      type: 'mastery.updated',
      studentId: 'test-student',
      data: { score: 85 },
      timestamp: new Date().toISOString()
    };

    // Publish event
    await this.client.pubsub.publish(
      'mastery-pubsub',
      'mastery-updates',
      testEvent
    );

    // Subscribe and verify
    const received = await this.subscribeAndWait('mastery-updates', testEvent);

    return received !== null;
  }

  async subscribeAndWait(topic, expectedEvent) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Timeout')), 5000);

      this.client.pubsub.subscribe('mastery-pubsub', topic, (event) => {
        if (event.studentId === expectedEvent.studentId) {
          clearTimeout(timeout);
          resolve(event);
        }
      });
    });
  }
}
```

### 3.2 Kong Gateway Integration

**Objective:** Verify JWT validation and rate limiting work correctly.

#### 3.2.1 JWT Authentication Tests
```javascript
// scripts/verify/kong-jwt.js
const axios = require('axios');
const jwt = require('jsonwebtoken');

class KongJWTTest {
  constructor() {
    this.kongUrl = process.env.KONG_URL || 'http://localhost:8000';
  }

  async testValidJWT() {
    const token = this.generateValidJWT();

    const response = await axios.get(
      `${this.kongUrl}/api/frontend/protected`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );

    return response.status === 200;
  }

  async testInvalidJWT() {
    const invalidToken = 'invalid.token.here';

    try {
      await axios.get(
        `${this.kongUrl}/api/frontend/protected`,
        { headers: { 'Authorization': `Bearer ${invalidToken}` } }
      );
      return false; // Should have failed
    } catch (error) {
      return error.response.status === 401;
    }
  }

  async testRateLimiting() {
    const token = this.generateValidJWT();
    const requests = [];

    // Make 100 requests rapidly
    for (let i = 0; i < 100; i++) {
      requests.push(
        axios.get(`${this.kongUrl}/api/frontend/protected`, {
          headers: { 'Authorization': `Bearer ${token}` },
          validateStatus: () => true // Accept any status
        })
      );
    }

    const responses = await Promise.all(requests);
    const rateLimited = responses.filter(r => r.status === 429).length;

    return rateLimited > 0; // Should have some 429 responses
  }

  generateValidJWT() {
    return jwt.sign(
      {
        sub: 'test-user',
        role: 'student',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600
      },
      process.env.JWT_SECRET || 'test-secret'
    );
  }
}
```

---

## 4. Security Verification

### 4.1 XSS Prevention Tests

**Objective:** Verify user input is properly sanitized.

```javascript
// scripts/verify/security-xss.js
describe('XSS Prevention Tests', () => {
  const xssPayloads = [
    '<script>alert("xss")</script>',
    '<img src=x onerror=alert("xss")>',
    'javascript:alert("xss")',
    '<svg onload=alert("xss")>'
  ];

  test.each(xssPayloads)('Sanitizes XSS payload: %s', async (payload) => {
    await page.evaluate((code) => {
      window.monacoEditor.setValue(code);
    }, payload);

    // Submit for analysis
    await page.click('#submit-button');
    await page.waitForTimeout(500);

    // Check that no alert dialogs were triggered
    const alertsTriggered = await page.evaluate(() => {
      return window.alertTriggered || false;
    });

    expect(alertsTriggered).toBe(false);

    // Check that output is sanitized
    const output = await page.evaluate(() => {
      return document.querySelector('.analysis-output')?.textContent || '';
    });

    expect(output).not.toContain('<script>');
    expect(output).not.toContain('onerror=');
  });
});
```

### 4.2 SQL Injection Prevention

**Objective:** Verify backend properly handles SQL injection attempts.

```javascript
// scripts/verify/security-sql.js
describe('SQL Injection Prevention', () => {
  const sqlPayloads = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    '1; SELECT * FROM users --',
    '1 UNION SELECT NULL,NULL --'
  ];

  test.each(sqlPayloads)('Blocks SQL injection: %s', async (payload) => {
    const response = await axios.post(
      'http://localhost:8000/api/feedback/analyze',
      { code: payload },
      {
        headers: { 'Authorization': `Bearer ${getTestToken()}` },
        validateStatus: () => true
      }
    );

    // Should return 400 or 422, not 200
    expect([400, 422]).toContain(response.status);
  });
});
```

---

## 5. End-to-End User Scenarios

### 5.1 Complete User Journey Test

**Objective:** Test the complete workflow from login to receiving feedback.

```javascript
// scripts/verify/e2e-user-journey.js
describe('Complete User Journey', () => {
  test('Student completes full workflow', async () => {
    // 1. Login
    await page.goto('http://localhost:3000/login');
    await page.type('#username', 'test-student');
    await page.type('#password', 'test-pass');
    await page.click('#login-button');
    await page.waitForNavigation();

    // 2. Navigate to editor
    await page.click('#editor-link');
    await page.waitForSelector('#monaco-editor');

    // 3. Write code
    const testCode = `def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))`;

    await page.evaluate((code) => {
      window.monacoEditor.setValue(code);
    }, testCode);

    // 4. Submit for analysis
    const submitTime = Date.now();
    await page.click('#analyze-button');

    // 5. Wait for real-time feedback
    await page.waitForFunction(
      () => {
        const feedback = document.querySelector('.feedback-panel');
        return feedback && feedback.textContent.includes('Analysis Complete');
      },
      { timeout: 10000 }
    );

    const receiveTime = Date.now();
    const latency = receiveTime - submitTime;

    // 6. Verify latency requirement
    expect(latency).toBeLessThan(1000);

    // 7. Verify feedback content
    const feedback = await page.evaluate(() => {
      const panel = document.querySelector('.feedback-panel');
      return panel ? panel.textContent : '';
    });

    expect(feedback).toContain('score');
    expect(feedback).toContain('suggestions');
  });
});
```

### 5.2 Multi-Session Collaboration Test

**Objective:** Verify multiple students can work simultaneously.

```javascript
// scripts/verify/collaboration.js
describe('Multi-Session Collaboration', () => {
  test('Two students work on same assignment', async () => {
    // Student A
    const browserA = await puppeteer.launch();
    const pageA = await browserA.newPage();

    // Student B
    const browserB = await puppeteer.launch();
    const pageB = await browserB.newPage();

    // Both log in
    await login(pageA, 'student-a');
    await login(pageB, 'student-b');

    // Both open same assignment
    await pageA.goto('http://localhost:3000/assignment/123');
    await pageB.goto('http://localhost:3000/assignment/123');

    // Student A makes changes
    await pageA.evaluate(() => {
      window.monacoEditor.setValue('print("hello from A")');
    });

    // Student B should see real-time update (if shared editing enabled)
    if (process.env.ENABLE_COLLABORATION) {
      const contentB = await pageB.evaluate(() => {
        return window.monacoEditor.getValue();
      });

      expect(contentB).toContain('hello from A');
    }

    await browserA.close();
    await browserB.close();
  });
});
```

---

## 6. Performance Budgets

### 6.1 Web Vitals Integration

```javascript
// scripts/monitor/web-vitals.js
import { getCLS, getFID, getLCP, getFCP, getTTFB } from 'web-vitals';

const thresholds = {
  CLS: 0.1,      // Cumulative Layout Shift
  FID: 100,      // First Input Delay (ms)
  LCP: 2500,     // Largest Contentful Paint (ms)
  FCP: 1800,     // First Contentful Paint (ms)
  TTFB: 600      // Time to First Byte (ms)
};

function sendToAnalytics(metric) {
  const body = JSON.stringify({
    metric: metric.name,
    value: metric.value,
    rating: metric.rating, // 'good', 'needs-improvement', 'poor'
    threshold: thresholds[metric.name]
  });

  // Send to monitoring endpoint
  fetch('/api/vitals', {
    method: 'POST',
    body,
    headers: { 'Content-Type': 'application/json' }
  });
}

// Attach to all pages
getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getLCP(sendToAnalytics);
getFCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### 6.2 Resource Budgets

```javascript
// scripts/monitor/resource-budgets.js
const budgets = {
  javascript: 500 * 1024,    // 500KB
  css: 100 * 1024,          // 100KB
  images: 300 * 1024,       // 300KB
  total: 1000 * 1024,       // 1MB
  chunks: 5                 // Max 5 JS chunks
};

function checkResourceBudgets() {
  const resources = performance.getEntriesByType('resource');

  const totals = {
    javascript: 0,
    css: 0,
    images: 0,
    total: 0,
    chunks: 0
  };

  resources.forEach(resource => {
    const size = resource.transferSize;
    totals.total += size;

    if (resource.name.endsWith('.js')) {
      totals.javascript += size;
      totals.chunks++;
    } else if (resource.name.endsWith('.css')) {
      totals.css += size;
    } else if (resource.name.match(/\.(png|jpg|jpeg|gif|svg)$/)) {
      totals.images += size;
    }
  });

  // Check budgets
  const results = Object.entries(budgets).map(([key, budget]) => {
    const actual = totals[key];
    return {
      resource: key,
      budget,
      actual,
      passed: actual <= budget,
      overage: actual > budget ? actual - budget : 0
    };
  });

  return results;
}
```

---

## 7. Test Execution & CI/CD Integration

### 7.1 Test Pyramid Structure

```
specs/004-realtime-frontend/
├── tests/
│   ├── unit/                    # Unit tests (70%)
│   │   ├── monaco/
│   │   ├── sse/
│   │   └── components/
│   ├── integration/            # Integration tests (20%)
│   │   ├── api/
│   │   ├── dapr/
│   │   └── kong/
│   └── e2e/                     # End-to-end tests (10%)
│       ├── user-journeys/
│       └── performance/
└── scripts/
    ├── verify/                 # Verification scripts
    ├── monitor/                # Synthetic monitoring
    └── benchmarks/             # Performance benchmarks
```

### 7.2 CI/CD Pipeline Configuration

```yaml
# .github/workflows/verification.yml
name: Comprehensive Verification
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
      dapr:
        image: daprio/daprd:latest
        ports: ['3500:3500', '3501:3501']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Install dependencies
        run: npm ci

      - name: Start backend services
        run: docker-compose -f docker-compose.test.yml up -d

      - name: Wait for services
        run: npx wait-on http://localhost:8000 http://localhost:3500

      - name: Run integration tests
        run: npm run test:integration
        env:
          BACKEND_URL: http://localhost:8000
          DAPR_HOST: localhost

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Build application
        run: npm run build

      - name: Start application
        run: npm start &
        env:
          PORT: 3000

      - name: Wait for app
        run: npx wait-on http://localhost:3000

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: e2e-test-results
          path: |
            test-results/
            playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Install dependencies
        run: npm ci

      - name: Build and start app
        run: |
          npm run build
          npm start &

      - name: Wait for app
        run: npx wait-on http://localhost:3000

      - name: Run editor load test
        run: node scripts/verify/editor-load-time.js

      - name: Run feedback latency test
        run: node scripts/verify/feedback-latency.js

      - name: Check performance budgets
        run: node scripts/monitor/resource-budgets.js

      - name: Upload performance reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: reports/performance-*.json

  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Install dependencies
        run: npm ci

      - name: Run security audit
        run: npm audit --audit-level moderate

      - name: Run XSS tests
        run: npm run test:security:xss

      - name: Run SQL injection tests
        run: npm run test:security:sql

      - name: Run dependency vulnerability scan
        uses: anchore/scan-action@v3
        with:
          fail-build: true

  lighthouse-ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Install dependencies
        run: npm ci

      - name: Build and start app
        run: |
          npm run build
          npm start &

      - name: Wait for app
        run: npx wait-on http://localhost:3000

      - name: Run Lighthouse CI
        run: npx lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}

  generate-report:
    needs: [unit-tests, integration-tests, e2e-tests, performance-tests, security-tests]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - uses: actions/checkout@v3

      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Generate verification report
        run: node scripts/generate-verification-report.js

      - name: Upload verification report
        uses: actions/upload-artifact@v3
        with:
          name: verification-report
          path: reports/verification-report.md
```

### 7.3 Local Development Verification

```bash
#!/bin/bash
# scripts/verify/local.sh

echo "🔍 Running Local Verification Suite"
echo "==================================="

# Check dependencies
echo "📦 Checking dependencies..."
npm ls --depth=0 || exit 1

# Run unit tests
echo "🧪 Running unit tests..."
npm run test:unit -- --passWithNoTests

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.dev.yml up -d
npx wait-on http://localhost:8000 http://localhost:3000

# Run integration tests
echo "🔗 Running integration tests..."
npm run test:integration

# Run performance tests
echo "⚡ Running performance tests..."
node scripts/verify/editor-load-time.js
node scripts/verify/feedback-latency.js

# Run security tests
echo "🔒 Running security tests..."
npm run test:security:xss
npm run test:security:sql

echo "✅ Local verification complete!"
```

---

## 8. Monitoring & Alerting

### 8.1 Real-Time Monitoring Dashboard

```javascript
// scripts/monitor/dashboard.js
const WebSocket = require('ws');
const express = require('express');

class VerificationDashboard {
  constructor() {
    this.app = express();
    this.wss = new WebSocket.Server({ port: 8080 });
    this.metrics = new Map();
  }

  start() {
    this.setupRoutes();
    this.setupWebSocket();
    this.startMetricsCollection();

    this.app.listen(3001, () => {
      console.log('Verification dashboard on http://localhost:3001');
    });
  }

  setupRoutes() {
    this.app.get('/api/metrics', (req, res) => {
      res.json(Object.fromEntries(this.metrics));
    });

    this.app.get('/api/alerts', (req, res) => {
      const alerts = this.getAlerts();
      res.json(alerts);
    });
  }

  setupWebSocket() {
    this.wss.on('connection', (ws) => {
      ws.on('message', (message) => {
        const data = JSON.parse(message);
        this.handleMetric(data);
      });
    });
  }

  handleMetric(metric) {
    const { name, value, timestamp } = metric;

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }

    const series = this.metrics.get(name);
    series.push({ value, timestamp });

    // Keep only last 1000 points
    if (series.length > 1000) {
      series.shift();
    }

    // Check thresholds
    this.checkThresholds(name, value);
  }

  checkThresholds(name, value) {
    const thresholds = {
      'editor-load-time': 200,
      'feedback-latency': 1000,
      'api-response-time': 500,
      'bundle-size': 1000 * 1024 // 1MB
    };

    if (thresholds[name] && value > thresholds[name]) {
      this.triggerAlert(name, value, thresholds[name]);
    }
  }

  triggerAlert(metric, value, threshold) {
    const alert = {
      metric,
      value,
      threshold,
      timestamp: new Date().toISOString(),
      severity: 'warning'
    };

    // Send to WebSocket clients
    this.wss.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({ type: 'alert', data: alert }));
      }
    });

    // Log alert
    console.warn(`🚨 Alert: ${metric} = ${value} (threshold: ${threshold})`);
  }

  getAlerts() {
    // Return recent alerts
    return Array.from(this.metrics.entries())
      .filter(([name, series]) => {
        const latest = series[series.length - 1];
        const threshold = {
          'editor-load-time': 200,
          'feedback-latency': 1000
        }[name];
        return latest && threshold && latest.value > threshold;
      })
      .map(([name, series]) => {
        const latest = series[series.length - 1];
        return {
          metric: name,
          value: latest.value,
          timestamp: latest.timestamp
        };
      });
  }

  startMetricsCollection() {
    // Collect metrics from test runs
    setInterval(() => {
      // Simulate metric collection
      this.handleMetric({
        name: 'editor-load-time',
        value: Math.random() * 250, // Random between 0-250ms
        timestamp: Date.now()
      });

      this.handleMetric({
        name: 'feedback-latency',
        value: Math.random() * 1500, // Random between 0-1500ms
        timestamp: Date.now()
      });
    }, 5000);
  }
}
```

### 8.2 Alert Rules

```yaml
# scripts/monitor/alert-rules.yml
groups:
  - name: frontend-performance
    rules:
      - alert: MonacoEditorLoadTimeExceeded
        expr: editor_load_time_seconds > 0.2
        for: 5m
        labels:
          severity: warning
          team: frontend
        annotations:
          summary: "Monaco Editor load time exceeded 200ms"
          description: "Current load time: {{ $value }}ms"

      - alert: FeedbackLatencyExceeded
        expr: feedback_latency_seconds > 1
        for: 2m
        labels:
          severity: critical
          team: frontend
        annotations:
          summary: "Feedback latency exceeded 1 second"
          description: "Current latency: {{ $value }}s"

      - alert: BundleSizeExceeded
        expr: bundle_size_bytes > 1000000
        for: 0m
        labels:
          severity: warning
          team: frontend
        annotations:
          summary: "Bundle size exceeded 1MB"
          description: "Current size: {{ $value }} bytes"
```

---

## 9. Acceptance Criteria & Definition of Done

### 9.1 Performance Requirements

- [ ] **Editor Load Time**: Average < 200ms over 10 consecutive loads
- [ ] **Feedback Latency**: 95th percentile < 1s for all user scenarios
- [ ] **Bundle Size**: Total < 1MB, JS chunks < 5
- [ ] **Web Vitals**: All metrics in "good" range per Lighthouse
- [ ] **API Response**: 95th percentile < 500ms

### 9.2 Functional Requirements

- [ ] **Monaco Editor**: Loads without errors, syntax highlighting works
- [ ] **Autocomplete**: Suggestions appear for Python code
- [ ] **Linting**: Error detection works for common Python mistakes
- [ ] **Formatting**: Auto-formatting on type works
- [ ] **Real-time Events**: SSE connection established, events received
- [ ] **UI Updates**: Feedback appears within latency budget
- [ ] **Error Handling**: Graceful degradation on network failures

### 9.3 Security Requirements

- [ ] **XSS Prevention**: All user input sanitized, no script execution
- [ ] **SQL Injection**: Backend blocks all injection attempts
- [ ] **JWT Validation**: Invalid tokens rejected by Kong
- [ ] **Rate Limiting**: API protects against abuse
- [ ] **CORS**: Properly configured for production

### 9.4 Integration Requirements

- [ ] **Backend API**: All endpoints respond correctly
- [ ] **Dapr Pub/Sub**: Events flow from backend to frontend
- [ ] **Kong Gateway**: JWT auth and rate limiting work
- [ ] **Database**: User sessions persist correctly
- [ ] **Redis**: Cache invalidation works as expected

### 9.5 User Experience Requirements

- [ ] **Login Flow**: Authentication works end-to-end
- [ ] **Editor Experience**: Smooth typing, no lag
- [ ] **Feedback Presentation**: Clear, actionable feedback
- [ ] **Real-time Updates**: Events appear without manual refresh
- [ ] **Error Messages**: User-friendly error handling

---

## 10. Test Data & Fixtures

### 10.1 Mock Data Generation

```javascript
// scripts/test-data/generate-fixtures.js
class TestDataGenerator {
  generateStudentProfile() {
    return {
      id: `student_${Math.random().toString(36).substr(2, 9)}`,
      username: `user_${Date.now()}`,
      email: `test+${Date.now()}@example.com`,
      role: 'student',
      createdAt: new Date().toISOString(),
      preferences: {
        theme: 'dark',
        fontSize: 14,
        autoSave: true
      }
    };
  }

  generateCodeSubmission() {
    const templates = [
      {
        name: 'simple-function',
        code: 'def add(a, b):\n    return a + b'
      },
      {
        name: 'class-definition',
        code: 'class Calculator:\n    def __init__(self):\n        self.value = 0\n    \n    def add(self, x):\n        self.value += x\n        return self.value'
      },
      {
        name: 'algorithm',
        code: 'def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    \n    while left <= right:\n        mid = (left + right) // 2\n        \n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    \n    return -1'
      }
    ];

    return templates[Math.floor(Math.random() * templates.length)];
  }

  generateFeedbackEvent() {
    return {
      type: 'feedback.received',
      studentId: `student_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      data: {
        score: Math.floor(Math.random() * 40) + 60, // 60-100
        suggestions: [
          'Consider adding type hints',
          'Add docstring for better documentation',
          'Variable naming could be more descriptive'
        ],
        errors: [],
        complexity: {
          cyclomatic: Math.floor(Math.random() * 10) + 1,
          lines: Math.floor(Math.random() * 50) + 10
        }
      }
    };
  }

  generatePerformanceMetrics() {
    return {
      timestamp: new Date().toISOString(),
      metrics: {
        editorLoadTime: Math.random() * 300, // 0-300ms
        feedbackLatency: Math.random() * 1500, // 0-1500ms
        apiResponseTime: Math.random() * 800, // 0-800ms
        bundleSize: Math.random() * 1.5 * 1024 * 1024, // 0-1.5MB
        memoryUsage: Math.random() * 100 * 1024 * 1024 // 0-100MB
      }
    };
  }

  // Generate test dataset for load testing
  generateLoadTestData(count = 1000) {
    const data = [];
    for (let i = 0; i < count; i++) {
      data.push({
        userId: `user_${i}`,
        action: ['submit_code', 'get_feedback', 'view_history'][Math.floor(Math.random() * 3)],
        timestamp: Date.now() - Math.random() * 3600000, // Last hour
        payload: this.generateCodeSubmission()
      });
    }
    return data;
  }
}

module.exports = TestDataGenerator;
```

---

## 11. Continuous Improvement

### 11.1 Test Coverage Tracking

```javascript
// scripts/monitor/test-coverage.js
const fs = require('fs');
const path = require('path');

class TestCoverageTracker {
  constructor() {
    this.coverageReports = [];
    this.thresholds = {
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80
    };
  }

  async generateReport() {
    const coverage = await this.collectCoverage();
    const report = {
      timestamp: new Date().toISOString(),
      overall: this.calculateOverall(coverage),
      files: coverage,
      thresholds: this.thresholds,
      passed: this.checkThresholds(coverage)
    };

    this.saveReport(report);
    return report;
  }

  async collectCoverage() {
    // Collect from Jest, Cypress, etc.
    const files = [
      'coverage/coverage-summary.json',
      'cypress/coverage/coverage-summary.json'
    ];

    const coverage = {};

    for (const file of files) {
      if (fs.existsSync(file)) {
        const data = JSON.parse(fs.readFileSync(file, 'utf8'));
        Object.assign(coverage, data);
      }
    }

    return coverage;
  }

  calculateOverall(coverage) {
    const totals = { statements: 0, branches: 0, functions: 0, lines: 0 };
    const counts = { statements: 0, branches: 0, functions: 0, lines: 0 };

    Object.values(coverage).forEach(file => {
      totals.statements += file.statements.total;
      counts.statements += file.statements.covered;
      totals.branches += file.branches.total;
      counts.branches += file.branches.covered;
      totals.functions += file.functions.total;
      counts.functions += file.functions.covered;
      totals.lines += file.lines.total;
      counts.lines += file.lines.covered;
    });

    return {
      statements: (counts.statements / totals.statements * 100).toFixed(2),
      branches: (counts.branches / totals.branches * 100).toFixed(2),
      functions: (counts.functions / totals.functions * 100).toFixed(2),
      lines: (counts.lines / totals.lines * 100).toFixed(2)
    };
  }

  checkThresholds(coverage) {
    const overall = this.calculateOverall(coverage);
    return Object.entries(this.thresholds).every(([key, threshold]) => {
      return parseFloat(overall[key]) >= threshold;
    });
  }

  saveReport(report) {
    const dir = 'reports/coverage';
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const filename = `${dir}/coverage-${Date.now()}.json`;
    fs.writeFileSync(filename, JSON.stringify(report, null, 2));
  }
}
```

### 11.2 Benchmarking Baselines

```javascript
// scripts/benchmarks/baseline-manager.js
class BaselineManager {
  constructor() {
    this.baselines = this.loadBaselines();
  }

  loadBaselines() {
    try {
      const data = fs.readFileSync('benchmarks/baselines.json', 'utf8');
      return JSON.parse(data);
    } catch (error) {
      return this.createInitialBaselines();
    }
  }

  createInitialBaselines() {
    return {
      editorLoadTime: { target: 200, current: 250, trend: 'stable' },
      feedbackLatency: { target: 1000, current: 1200, trend: 'stable' },
      bundleSize: { target: 1000000, current: 1100000, trend: 'stable' },
      apiResponse: { target: 500, current: 600, trend: 'stable' }
    };
  }

  updateBaseline(metric, actualValue) {
    if (!this.baselines[metric]) {
      this.baselines[metric] = { target: actualValue, current: actualValue, trend: 'stable' };
    }

    const baseline = this.baselines[metric];
    const previous = baseline.current;

    // Update with moving average (80% old, 20% new)
    baseline.current = (previous * 0.8 + actualValue * 0.2);

    // Determine trend
    const change = baseline.current - previous;
    if (Math.abs(change) > baseline.target * 0.1) {
      baseline.trend = change > 0 ? 'worsening' : 'improving';
    } else {
      baseline.trend = 'stable';
    }

    this.saveBaselines();
    return baseline;
  }

  saveBaselines() {
    fs.writeFileSync(
      'benchmarks/baselines.json',
      JSON.stringify(this.baselines, null, 2)
    );
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      baselines: this.baselines,
      summary: this.generateSummary()
    };

    fs.writeFileSync(
      `benchmarks/reports/baseline-${Date.now()}.json`,
      JSON.stringify(report, null, 2)
    );

    return report;
  }

  generateSummary() {
    const metrics = Object.keys(this.baselines);
    const improving = metrics.filter(m => this.baselines[m].trend === 'improving').length;
    const worsening = metrics.filter(m => this.baselines[m].trend === 'worsening').length;
    const stable = metrics.filter(m => this.baselines[m].trend === 'stable').length;

    return {
      total: metrics.length,
      improving,
      worsening,
      stable,
      health: worsening === 0 ? 'healthy' : 'needs-attention'
    };
  }
}
```

---

## 12. Risk Mitigation & Rollback

### 12.1 Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Monaco Editor fails to load | High | Low | Fallback to basic textarea, lazy loading |
| SSE connection drops | Medium | Medium | Auto-reconnect with exponential backoff |
| Performance regression | High | Medium | Automated rollback on threshold breach |
| Security vulnerability | Critical | Low | Regular security audits, WAF |
| Backend API changes | Medium | High | API contract testing, versioning |

### 12.2 Rollback Procedures

```bash
#!/bin/bash
# scripts/deploy/rollback.sh

echo "🔄 Rollback Procedure"
echo "==================="

# 1. Detect issues
if [ "$1" = "performance" ]; then
    echo "Performance rollback triggered"

    # Check metrics
    LATEST_PERF=$(curl -s http://monitoring/api/metrics/latest)
    EDITOR_LOAD=$(echo $LATEST_PERF | jq '.editorLoadTime')
    FEEDBACK_LATENCY=$(echo $LATEST_PERF | jq '.feedbackLatency')

    if [ $EDITOR_LOAD -gt 200 ] || [ $FEEDBACK_LATENCY -gt 1000 ]; then
        echo "❌ Performance thresholds breached"
        echo "📉 Rolling back to previous version..."

        # Rollback deployment
        kubectl rollout undo deployment/frontend

        # Wait for rollback
        kubectl rollout status deployment/frontend

        echo "✅ Rollback complete"

        # Send alert
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Performance rollback executed"}' \
            $SLACK_WEBHOOK
    fi
fi

# 2. Database rollback (if needed)
if [ "$1" = "data" ]; then
    echo "Data migration rollback..."

    # Restore backup
    pg_restore -d $DATABASE_URL backups/pre-deployment.dump

    # Update migrations
    npm run db:rollback
fi

# 3. Feature flag disable
if [ "$1" = "feature" ]; then
    echo "Disabling feature flags..."

    curl -X POST http://feature-flags/api/disable \
        -H "Authorization: Bearer $FF_TOKEN" \
        -d '{"feature": "monaco-new-editor"}'
fi
```

### 12.3 Feature Flags

```javascript
// config/feature-flags.js
const flags = {
  // Performance optimizations
  MONACO_LAZY_LOADING: {
    default: true,
    description: 'Lazy load Monaco Editor on demand'
  },

  BUNDLE_SPLITTING: {
    default: true,
    description: 'Split vendor bundles for better caching'
  },

  // Features
  REAL_TIME_COLLABORATION: {
    default: false,
    description: 'Multi-user collaborative editing',
    rollout: 0.1 // 10% of users
  },

  ADVANCED_LINTING: {
    default: true,
    description: 'Enhanced Python linting with mypy'
  },

  // Rollout controls
  NEW_FEEDBACK_UI: {
    default: false,
    description: 'New feedback presentation UI',
    rollout: 0.05, // 5% of users
    groups: ['beta-testers']
  }
};

class FeatureFlagManager {
  constructor() {
    this.flags = flags;
    this.userOverrides = new Map();
  }

  isEnabled(flagName, user = null) {
    const flag = this.flags[flagName];
    if (!flag) return false;

    // Check user override
    if (user && this.userOverrides.has(`${flagName}:${user.id}`)) {
      return this.userOverrides.get(`${flagName}:${user.id}`);
    }

    // Check rollout
    if (flag.rollout && user) {
      const hash = this.hashUser(user.id);
      return hash % 100 < (flag.rollout * 100);
    }

    // Check group membership
    if (flag.groups && user) {
      return flag.groups.some(group => user.groups?.includes(group));
    }

    return flag.default;
  }

  hashUser(userId) {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = ((hash << 5) - hash) + userId.charCodeAt(i);
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  setOverride(flagName, userId, value) {
    this.userOverrides.set(`${flagName}:${userId}`, value);
  }

  getActiveFlags(user = null) {
    return Object.keys(this.flags).reduce((acc, flagName) => {
      acc[flagName] = this.isEnabled(flagName, user);
      return acc;
    }, {});
  }
}
```

---

## 13. Documentation & Runbooks

### 13.1 Test Runbooks

```markdown
# Runbook: Debug Performance Issue

## Issue: Editor load time > 200ms

### Symptoms
- Monaco Editor takes longer than 200ms to initialize
- Users report "editor lag" on page load
- Lighthouse score for FCP is poor

### Investigation Steps

1. **Check Web Vitals**
   ```bash
   curl http://monitoring/api/webvitals/latest
   ```

2. **Analyze Bundle Size**
   ```bash
   npm run analyze
   # Look for large dependencies
   ```

3. **Profile Monaco Loading**
   - Open Chrome DevTools
   - Go to Performance tab
   - Reload page with profiling enabled
   - Look for long tasks in Monaco initialization

4. **Check CDN Performance**
   ```bash
   curl -w "@curl-format.txt" https://cdn.example.com/monaco-vs.min.js
   ```

### Common Fixes

1. **Enable Lazy Loading**
   ```javascript
   const MonacoEditor = dynamic(() => import('./MonacoEditor'), {
     ssr: false,
     loading: () => <Spinner />
   });
   ```

2. **Reduce Bundle Size**
   - Use Monaco Webpack plugin
   - Include only needed languages
   - Tree-shake unused features

3. **Improve CDN**
   - Use faster CDN (Cloudflare, Fastly)
   - Enable HTTP/2 and compression
   - Set proper cache headers

### Escalation
- If issue persists after 30 minutes: Page on-call engineer
- If affecting > 10% of users: Initiate rollback procedure
```

### 13.2 Post-Mortem Template

```markdown
# Post-Mortem: [Incident Title]

## Summary
- **Date**: [Date]
- **Duration**: [Start] to [End] ([Total Time])
- **Impact**: [Affected Users/Metrics]
- **Severity**: [P0/P1/P2/P3]

## Timeline
| Time | Event |
|------|-------|
| HH:MM | Initial detection |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Fix implemented |
| HH:MM | Resolution confirmed |

## Root Cause
[Detailed technical explanation]

## Impact Assessment
- Users affected: [Number]
- Performance impact: [Metrics]
- Business impact: [Revenue/Reputation]

## Response
- What went well: [List]
- What could be improved: [List]

## Action Items
| Item | Owner | Due Date | Status |
|------|-------|----------|--------|
| [Action] | [Name] | [Date] | [Pending] |

## Prevention
- [ ] Add monitoring for [metric]
- [ ] Update runbooks
- [ ] Conduct team training
- [ ] Implement automated testing
```

---

## 14. Success Metrics & KPIs

### 14.1 Key Performance Indicators

```javascript
// scripts/monitor/kpis.js
const KPIs = {
  // Performance KPIs
  performance: {
    editorLoadTime: {
      target: 200,
      unit: 'ms',
      weight: 0.25,
      measurement: 'p95'
    },
    feedbackLatency: {
      target: 1000,
      unit: 'ms',
      weight: 0.35,
      measurement: 'p95'
    },
    bundleSize: {
      target: 1000000,
      unit: 'bytes',
      weight: 0.15,
      measurement: 'max'
    }
  },

  // User Experience KPIs
  userExperience: {
    userSatisfaction: {
      target: 4.5,
      unit: 'rating',
      weight: 0.10,
      measurement: 'avg'
    },
    taskCompletion: {
      target: 0.95,
      unit: 'ratio',
      weight: 0.10,
      measurement: 'avg'
    },
    errorRate: {
      target: 0.01,
      unit: 'ratio',
      weight: 0.05,
      measurement: 'p95'
    }
  },

  // Business KPIs
  business: {
    activeUsers: {
      target: 1000,
      unit: 'users',
      weight: 0.00,
      measurement: 'total'
    },
    codeSubmissions: {
      target: 5000,
      unit: 'submissions/day',
      weight: 0.00,
      measurement: 'total'
    }
  }
};

class KPIReporter {
  calculateScore(metrics) {
    let totalScore = 0;
    let totalWeight = 0;

    Object.entries(KPIs).forEach(([category, categoryKPIs]) => {
      Object.entries(categoryKPIs).forEach(([name, kpi]) => {
        const actual = metrics[name];
        if (actual !== undefined) {
          const score = this.calculateMetricScore(actual, kpi.target);
          totalScore += score * kpi.weight;
          totalWeight += kpi.weight;
        }
      });
    });

    return totalWeight > 0 ? (totalScore / totalWeight) * 100 : 0;
  }

  calculateMetricScore(actual, target) {
    if (actual <= target) return 1;
    if (actual >= target * 2) return 0;
    return 1 - (actual - target) / target;
  }

  generateReport(metrics) {
    const score = this.calculateScore(metrics);

    return {
      timestamp: new Date().toISOString(),
      overallScore: score.toFixed(2),
      grade: this.getGrade(score),
      breakdown: this.getBreakdown(metrics),
      recommendations: this.getRecommendations(metrics)
    };
  }

  getGrade(score) {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  getBreakdown(metrics) {
    const breakdown = {};

    Object.entries(KPIs).forEach(([category, categoryKPIs]) => {
      breakdown[category] = {};
      Object.entries(categoryKPIs).forEach(([name, kpi]) => {
        const actual = metrics[name];
        if (actual !== undefined) {
          breakdown[category][name] = {
            actual,
            target: kpi.target,
            score: this.calculateMetricScore(actual, kpi.target)
          };
        }
      });
    });

    return breakdown;
  }

  getRecommendations(metrics) {
    const recommendations = [];

    if (metrics.editorLoadTime > 200) {
      recommendations.push('Enable Monaco lazy loading');
      recommendations.push('Reduce bundle size with code splitting');
    }

    if (metrics.feedbackLatency > 1000) {
      recommendations.push('Optimize backend API response times');
      recommendations.push('Enable SSE connection pooling');
    }

    if (metrics.bundleSize > 1000000) {
      recommendations.push('Implement better bundle splitting');
      recommendations.push('Remove unused dependencies');
    }

    return recommendations;
  }
}
```

### 14.2 Executive Dashboard

```javascript
// scripts/dashboard/executive.js
class ExecutiveDashboard {
  constructor() {
    this.metrics = new Map();
  }

  async generateReport() {
    const data = await this.collectMetrics();
    const report = {
      timestamp: new Date().toISOString(),
      health: this.calculateHealth(data),
      priorities: this.getPriorities(data),
      trends: this.analyzeTrends(data)
    };

    return this.formatReport(report);
  }

  async collectMetrics() {
    return {
      // Performance
      editorLoadTime: await this.getMetric('editor-load-time', 'p95'),
      feedbackLatency: await this.getMetric('feedback-latency', 'p95'),
      apiResponseTime: await this.getMetric('api-response', 'p95'),

      // Reliability
      uptime: await this.getMetric('uptime', 'percentage'),
      errorRate: await this.getMetric('error-rate', 'percentage'),

      // User Experience
      userSatisfaction: await this.getMetric('satisfaction', 'rating'),
      activeUsers: await this.getMetric('active-users', 'count'),

      // Business
      submissions: await this.getMetric('submissions', 'daily'),
      revenue: await this.getMetric('revenue', 'monthly')
    };
  }

  calculateHealth(data) {
    const checks = [
      { metric: 'editorLoadTime', max: 200, weight: 0.25 },
      { metric: 'feedbackLatency', max: 1000, weight: 0.35 },
      { metric: 'uptime', min: 99.9, weight: 0.20 },
      { metric: 'errorRate', max: 1, weight: 0.20 }
    ];

    let score = 0;
    checks.forEach(check => {
      const value = data[check.metric];
      if (value !== undefined) {
        if (check.max !== undefined && value <= check.max) {
          score += check.weight;
        } else if (check.min !== undefined && value >= check.min) {
          score += check.weight;
        }
      }
    });

    return {
      score: (score * 100).toFixed(1),
      status: score > 0.8 ? 'healthy' : score > 0.6 ? 'degraded' : 'critical'
    };
  }

  getPriorities(data) {
    const priorities = [];

    if (data.editorLoadTime > 200) {
      priorities.push({
        issue: 'Editor load time exceeded threshold',
        impact: 'High',
        action: 'Enable lazy loading, optimize bundle',
        owner: 'Frontend Team'
      });
    }

    if (data.feedbackLatency > 1000) {
      priorities.push({
        issue: 'Feedback latency too high',
        impact: 'Critical',
        action: 'Optimize backend, implement caching',
        owner: 'Backend Team'
      });
    }

    return priorities;
  }

  analyzeTrends(data) {
    // Analyze historical data for trends
    return {
      improving: ['editorLoadTime'], // Example
      worsening: [],
      stable: ['uptime', 'errorRate']
    };
  }

  formatReport(report) {
    return `
🚀 Real-Time Frontend - Executive Dashboard
===========================================

📊 Health: ${report.health.status.toUpperCase()} (Score: ${report.health.score}/100)

📈 Trends:
${report.trends.improving.map(m => `  ✅ ${m}: Improving`).join('\n')}
${report.trends.worsening.map(m => `  ❌ ${m}: Worsening`).join('\n')}
${report.trends.stable.map(m => `  ⚪ ${m}: Stable`).join('\n')}

⚠️  Priorities:
${report.priorities.map(p => `  • ${p.issue} [${p.impact}] - ${p.owner}`).join('\n')}

📅 Generated: ${report.timestamp}
    `;
  }
}
```

---

## 15. Summary & Next Steps

### 15.1 Verification Roadmap

**Week 1-2: Foundation**
- [ ] Set up CI/CD pipeline with verification jobs
- [ ] Create performance test infrastructure
- [ ] Implement basic functional tests
- [ ] Set up monitoring dashboard

**Week 3-4: Integration**
- [ ] Complete API contract testing
- [ ] Implement Dapr integration tests
- [ ] Add Kong JWT validation tests
- [ ] Create security test suite

**Week 5-6: Performance**
- [ ] Implement Monaco load time tests
- [ ] Add feedback latency monitoring
- [ ] Create synthetic monitoring
- [ ] Set up alerting rules

**Week 7-8: E2E & Polish**
- [ ] Complete user journey tests
- [ ] Run load testing
- [ ] Generate final verification report
- [ ] Document runbooks

### 15.2 Resource Requirements

| Resource | Count | Purpose |
|----------|-------|---------|
| CI/CD Minutes | 5000/month | Test execution |
| Storage | 50GB | Test artifacts, reports |
| Monitoring | 1 instance | Dashboard & alerting |
| Test Environments | 3 | Dev, Staging, Load test |

### 15.3 Success Criteria

**Minimum Viable Verification:**
- ✅ All critical paths tested
- ✅ Performance budgets met
- ✅ Security tests pass
- ✅ Integration tests pass
- ✅ CI/CD pipeline operational

**Target Verification:**
- ✅ 80%+ test coverage
- ✅ All performance thresholds met
- ✅ Zero critical security vulnerabilities
- ✅ Sub-100ms p95 editor load time
- ✅ Sub-500ms p95 feedback latency

---

## 16. Appendix

### 16.1 Reference Links

- [Monaco Editor Documentation](https://microsoft.github.io/monaco-editor/)
- [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Dapr Pub/Sub Documentation](https://docs.dapr.io/developing-applications/building-blocks/pubsub/)
- [Kong JWT Plugin](https://docs.konghq.com/hub/kong-inc/jwt/)
- [Playwright Documentation](https://playwright.dev/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)

### 16.2 Tools & Scripts

All verification scripts are located in `specs/004-realtime-frontend/scripts/`:
- `verify/` - Automated verification tests
- `monitor/` - Synthetic monitoring
- `benchmarks/` - Performance benchmarks
- `test-data/` - Test data generators

### 16.3 Contact & Support

- **Frontend Team**: #frontend-channel
- **Performance Issues**: #performance-channel
- **Security Issues**: #security-channel (PAGERDUTY)
- **Architecture**: #architecture-channel

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-15
**Owner**: Frontend Team Lead
**Status**: Planning Phase