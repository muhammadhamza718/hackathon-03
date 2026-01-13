/**
 * k6 Load Test Script for Triage Service
 * Elite Implementation Standard v2.0.0
 *
 * Tests performance under concurrent load
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const successRate = new Rate('successful_requests');
const triageDuration = new Trend('triage_duration', true);
const tokenEfficiency = new Trend('token_efficiency');

// Test configuration
export const options = {
    stages: [
        { duration: '30s', target: 10 },   // Ramp up to 10 VUs
        { duration: '60s', target: 10 },   // Steady state at 10 VUs
        { duration: '30s', target: 50 },   // Ramp up to 50 VUs
        { duration: '60s', target: 50 },   // Steady state at 50 VUs
        { duration: '30s', target: 0 },    // Ramp down
    ],
    thresholds: {
        'successful_requests': ['rate>0.95'],      // 95% success rate
        'triage_duration': ['p(95)<200'],          // P95 latency under 200ms
        'http_req_duration': ['p(95)<150'],        // P95 under 150ms
        'http_req_failed': ['rate<0.05'],          // Less than 5% failures
    },
};

const BASE_URL = __ENV.TRIAGE_SERVICE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-key';

// Test data
const testQueries = [
    {
        query: "Help me debug this Python syntax error in my for loop",
        user_id: "student-1001",
        context: { language: "python", error_type: "syntax" }
    },
    {
        query: "Explain the concept of recursion in simple terms with examples",
        user_id: "student-1002",
        context: { topic: "recursion", complexity: "beginner" }
    },
    {
        query: "Create practice exercises for array manipulation algorithms",
        user_id: "student-1003",
        context: { topic: "algorithms", type: "practice" }
    },
    {
        query: "Show my learning progress this week on data structures",
        user_id: "student-1004",
        context: { timeframe: "week", topic: "data_structures" }
    },
    {
        query: "Review my submitted code for optimization improvements",
        user_id: "student-1005",
        context: { action: "review", focus: "optimization" }
    }
];

// JWT token generator (mock)
function generateJWT(userId) {
    const header = { alg: "HS256", typ: "JWT" };
    const payload = {
        sub: userId,
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600,
        role: "student"
    };
    // Mock token - in real test this would be a valid JWT
    return `mock.${btoa(JSON.stringify(header))}.${btoa(JSON.stringify(payload))}`;
}

export default function () {
    // Select random query
    const testData = testQueries[Math.floor(Math.random() * testQueries.length)];

    // Generate headers
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${generateJWT(testData.user_id)}`,
        'X-Consumer-Username': testData.user_id,
    };

    // Make request
    const start = Date.now();
    const response = http.post(
        `${BASE_URL}/api/v1/triage`,
        JSON.stringify(testData),
        { headers: headers }
    );
    const duration = Date.now() - start;

    // Check response
    const success = check(response, {
        'status is 200': (r) => r.status === 200,
        'has routing decision': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.routing_decision && body.routing_decision.target_agent;
            } catch (e) {
                return false;
            }
        },
        'has metrics': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.metrics && body.metrics.tokens_used;
            } catch (e) {
                return false;
            }
        },
        'efficiency achieved': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.metrics && body.metrics.efficiency_percentage >= 98.7;
            } catch (e) {
                return false;
            }
        }
    });

    // Record metrics
    if (success) {
        successRate.add(1);
        triageDuration.add(duration);

        try {
            const body = JSON.parse(response.body);
            if (body.metrics) {
                tokenEfficiency.add(body.metrics.efficiency_percentage);
            }
        } catch (e) {}
    } else {
        successRate.add(0);
    }

    // Extract and log X headers if present
    if (response.headers['X-Token-Usage']) {
        // Performance data available
    }

    // Sleep between requests (think time)
    sleep(0.5);
}

// Setup function - runs once before test
export function setup() {
    console.log(`Load testing triage service at: ${BASE_URL}`);
    console.log('Test configuration:');
    console.log(`- Target throughput: 50 concurrent requests`);
    console.log(`- Expected P95 latency: <200ms`);
    console.log(`- Expected efficiency: >98.7%`);

    return { timestamp: new Date().toISOString() };
}

// Teardown function - runs once after test
export function teardown(data) {
    console.log('Load test completed');
    console.log(`Test started at: ${data.timestamp}`);
}