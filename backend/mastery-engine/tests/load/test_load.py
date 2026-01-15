"""
Mastery Engine Load Testing Script
==================================

Locust load testing script for Mastery Engine API endpoints.
Tests performance under realistic workloads and concurrent users.

Usage:
    locust -f tests/load/test_load.py --host=http://localhost:8005 --users=50 --spawn-rate=5 --run-time=10m

Requirements:
    pip install locust
"""

import os
import time
import json
import random
from typing import Dict, Any, List
from locust import HttpUser, task, between, events, tag
from locust.env import Environment
from locust.log import setup_logging


# Test Configuration
TEST_CONFIG = {
    # User data for testing (use test credentials)
    "test_users": [
        {"student_id": "student_001", "token": os.getenv("TEST_JWT_TOKEN", "test-token-001")},
        {"student_id": "student_002", "token": os.getenv("TEST_JWT_TOKEN", "test-token-002")},
        {"student_id": "student_003", "token": os.getenv("TEST_JWT_TOKEN", "test-token-003")},
        {"student_id": "student_004", "token": os.getenv("TEST_JWT_TOKEN", "test-token-004")},
        {"student_id": "student_005", "token": os.getenv("TEST_JWT_TOKEN", "test-token-005")},
    ],

    # Batch test data
    "batch_sizes": [10, 25, 50, 100],

    # Component score patterns for realistic data
    "component_patterns": [
        {"completion": 0.8, "quiz": 0.7, "quality": 0.85, "consistency": 0.75},
        {"completion": 0.95, "quiz": 0.9, "quality": 0.92, "consistency": 0.88},
        {"completion": 0.6, "quiz": 0.5, "quality": 0.7, "consistency": 0.65},
    ],

    # Test scenario weights
    "scenario_weights": {
        "health_check": 0.15,      # 15% of requests
        "mastery_query": 0.25,     # 25% of requests
        "mastery_calc": 0.20,      # 20% of requests
        "prediction": 0.15,        # 15% of requests
        "recommendation": 0.10,    # 10% of requests
        "batch": 0.08,             # 8% of requests
        "analytics": 0.07,         # 7% of requests
    }
}


class MasteryEngineUser(HttpUser):
    """
    Simulates a user interacting with Mastery Engine API
    """

    # Wait between 1-3 seconds between tasks (simulates realistic user behavior)
    wait_time = between(1, 3)

    # Host must be provided via --host flag
    host = os.getenv("LOCUST_HOST", "http://localhost:8005")

    def on_start(self):
        """Initialize user session"""
        # Select a test user
        self.test_user = random.choice(TEST_CONFIG["test_users"])
        self.student_id = self.test_user["student_id"]
        self.auth_token = self.test_user["token"]

        # Track user session metrics
        self.session_requests = 0
        self.session_errors = 0
        self.session_start_time = time.time()

        # Store recent batch job IDs for status checks
        self.recent_batches = []

        print(f"User {self.student_id} started session")

    def on_stop(self):
        """Clean up user session"""
        session_duration = time.time() - self.session_start_time
        print(f"User {self.student_id} session ended: {self.session_requests} requests, {self.session_errors} errors, {session_duration:.2f}s duration")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "X-Request-ID": f"load-test-{self.student_id}-{int(time.time()*1000)}",
            "User-Agent": "Locust-Load-Test/1.0"
        }

    def get_headers(self) -> Dict[str, str]:
        """Get headers without authentication (for public endpoints)"""
        return {
            "Content-Type": "application/json",
            "X-Request-ID": f"load-test-{self.student_id}-{int(time.time()*1000)}",
            "User-Agent": "Locust-Load-Test/1.0"
        }

    @task(weight=3)  # Higher weight for health checks
    @tag('health', 'basic')
    def health_check(self):
        """Basic health check endpoints"""
        # Health
        with self.client.get("/health", name="/health", catch_response=True) as response:
            if response.status_code == 200:
                self._record_success()
            else:
                self._record_error(f"Health check failed: {response.status_code}")

        # Readiness (occasional)
        if random.random() < 0.2:  # 20% chance
            with self.client.get("/ready", name="/ready", catch_response=True) as response:
                if response.status_code == 200:
                    self._record_success()
                else:
                    self._record_error(f"Readiness check failed: {response.status_code}")

    @task(weight=4)
    @tag('mastery', 'core')
    def mastery_query(self):
        """Query current mastery status"""
        payload = {"student_id": self.student_id}

        with self.client.post(
            "/api/v1/mastery/query",
            name="/api/v1/mastery/query",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:

            if response.status_code == 200:
                self._record_success()

                # Validate response structure
                try:
                    data = response.json()
                    if "mastery_score" not in data:
                        response.failure("Missing mastery_score in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                self._record_error(f"Mastery query failed: {response.status_code}")

    @task(weight=3)
    @tag('mastery', 'core')
    def mastery_calculation(self):
        """Calculate mastery from component scores"""
        # Use one of the predefined patterns
        pattern = random.choice(TEST_CONFIG["component_patterns"])

        payload = {
            "student_id": self.student_id,
            "components": {
                "completion": pattern["completion"],
                "quiz": pattern["quiz"],
                "quality": pattern["quality"],
                "consistency": pattern["consistency"]
            }
        }

        with self.client.post(
            "/api/v1/mastery/calculate",
            name="/api/v1/mastery/calculate",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:

            if response.status_code == 200:
                self._record_success()

                # Validate calculation result
                try:
                    data = response.json()
                    if "mastery_score" in data:
                        score = data["mastery_score"]
                        if not (0 <= score <= 1):
                            response.failure(f"Invalid mastery score: {score}")
                except:
                    response.failure("Invalid JSON response")
            else:
                self._record_error(f"Calculation failed: {response.status_code}")

    @task(weight=2)
    @tag('prediction', 'advanced')
    def prediction(self):
        """Get mastery prediction"""
        payload = {
            "student_id": self.student_id,
            "days": 7
        }

        with self.client.post(
            "/api/v1/predictions/next-week",
            name="/api/v1/predictions/next-week",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:

            if response.status_code == 200:
                self._record_success()
            else:
                self._record_error(f"Prediction failed: {response.status_code}")

    @task(weight=1)
    @tag('recommendation', 'advanced')
    def recommendation(self):
        """Get adaptive recommendations"""
        payload = {
            "student_id": self.student_id,
            "limit": 3
        }

        with self.client.post(
            "/api/v1/recommendations/adaptive",
            name="/api/v1/recommendations/adaptive",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:

            if response.status_code == 200:
                self._record_success()

                # Validate recommendations structure
                try:
                    data = response.json()
                    if isinstance(data, list):
                        for rec in data:
                            if "priority" not in rec or "action" not in rec:
                                response.failure("Invalid recommendation format")
                                break
                except:
                    response.failure("Invalid JSON response")
            else:
                self._record_error(f"Recommendation failed: {response.status_code}")

    @task(weight=1)
    @tag('batch', 'heavy')
    def batch_processing(self):
        """Submit batch processing job"""
        # Random batch size within reasonable limits
        batch_size = random.choice(TEST_CONFIG["batch_sizes"])

        # Generate multiple student IDs for batch
        student_ids = [f"batch_student_{i}" for i in range(batch_size)]

        payload = {
            "student_ids": student_ids,
            "priority": random.choice(["low", "normal", "high"])
        }

        with self.client.post(
            "/api/v1/batch/mastery",
            name="/api/v1/batch/mastery",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:

            if response.status_code == 200:
                self._record_success()

                # Store batch ID for status checking
                try:
                    data = response.json()
                    if "batch_id" in data:
                        self.recent_batches.append(data["batch_id"])
                        # Keep only last 5 batch IDs
                        self.recent_batches = self.recent_batches[-5:]
                except:
                    pass
            else:
                self._record_error(f"Batch submission failed: {response.status_code}")

        # Occasionally check batch status (20% chance if we have recent batches)
        if random.random() < 0.2 and self.recent_batches:
            batch_id = random.choice(self.recent_batches)
            with self.client.get(
                f"/api/v1/batch/status/{batch_id}",
                name="/api/v1/batch/status/{batch_id}",
                headers=self.get_auth_headers(),
                catch_response=True
            ) as status_response:
                if status_response.status_code == 200:
                    self._record_success()
                else:
                    self._record_error(f"Batch status failed: {status_response.status_code}")

    @task(weight=1)
    @tag('analytics', 'advanced')
    def analytics_history(self):
        """Get historical analytics"""
        payload = {
            "student_id": self.student_id,
            "days": random.choice([7, 14, 30]),
            "aggregation": random.choice(["daily", "weekly", "monthly"])
        }

        with self.client.post(
            "/api/v1/analytics/history",
            name="/api/v1/analytics/history",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:

            if response.status_code == 200:
                self._record_success()
            else:
                self._record_error(f"Analytics failed: {response.status_code}")

    def _record_success(self):
        """Record successful request"""
        self.session_requests += 1

    def _record_error(self, error_message: str):
        """Record failed request"""
        self.session_requests += 1
        self.session_errors += 1
        print(f"Error for user {self.student_id}: {error_message}")


@events.test_stop.add_listener
def on_test_stop(environment: Environment, **kwargs):
    """
    Called when the load test completes
    """
    print("\n" + "="*60)
    print("LOAD TEST SUMMARY")
    print("="*60)

    stats = environment.stats

    # Overall statistics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    total_time = stats.total.total_response_time / 1000  # Convert to seconds

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100
        avg_response_time = stats.total.avg_response_time
        p95_response_time = stats.total.get_response_time_percentile(0.95)
        p99_response_time = stats.total.get_response_time_percentile(0.99)

        print(f"Total Requests: {total_requests:,}")
        print(f"Total Failures: {total_failures:,} ({failure_rate:.2f}%)")
        print(f"Total Duration: {total_time:.2f}s")
        print(f"Average Response Time: {avg_response_time:.2f}ms")
        print(f"P95 Response Time: {p95_response_time:.2f}ms")
        print(f"P99 Response Time: {p99_response_time:.2f}ms")

        # Calculate requests per second
        rps = total_requests / total_time if total_time > 0 else 0
        print(f"Requests per Second: {rps:.2f}")

        # Success/Failure
        if failure_rate < 1.0:
            print(f"✅ SUCCESS: Failure rate ({failure_rate:.2f}%) is below 1% threshold")
        else:
            print(f"❌ FAILURE: Failure rate ({failure_rate:.2f}%) exceeds 1% threshold")

        # Performance thresholds
        if avg_response_time < 200:
            print(f"✅ PERFORMANCE: Average response time ({avg_response_time:.2f}ms) is under 200ms threshold")
        else:
            print(f"⚠️ PERFORMANCE: Average response time ({avg_response_time:.2f}ms) exceeds 200ms threshold")

        if p95_response_time < 500:
            print(f"✅ LATENCY: P95 latency ({p95_response_time:.2f}ms) is under 500ms threshold")
        else:
            print(f"⚠️ LATENCY: P95 latency ({p95_response_time:.2f}ms) exceeds 500ms threshold")

    # Per-endpoint statistics
    print("\nEndpoint Breakdown:")
    print("-" * 60)
    for endpoint, stat in stats.entries.items():
        if stat.num_requests > 0:
            endpoint_failure_rate = (stat.num_failures / stat.num_requests) * 100
            print(f"{endpoint:40} | Requests: {stat.num_requests:5} | "
                  f"Failures: {endpoint_failure_rate:5.2f}% | "
                  f"Avg: {stat.avg_response_time:6.1f}ms | "
                  f"P95: {stat.get_response_time_percentile(0.95):6.1f}ms")

    print("\n" + "="*60)

    # Recommendations
    if total_failures == 0 and avg_response_time < 200 and p95_response_time < 500:
        print("🎉 EXCELLENT: All tests passed with optimal performance!")
    elif total_failures / total_requests < 0.01 and avg_response_time < 500:
        print("✅ GOOD: Tests passed with acceptable performance")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Review failures and performance metrics")

    print("="*60 + "\n")


class QuickStartUser(HttpUser):
    """
    Simplified user for quick smoke tests
    Tests only core functionality with minimal wait time
    """

    wait_time = between(0.5, 1.5)  # Faster-paced for quick tests
    host = os.getenv("LOCUST_HOST", "http://localhost:8005")

    def on_start(self):
        self.test_user = random.choice(TEST_CONFIG["test_users"])
        self.auth_headers = {
            "Authorization": f"Bearer {self.test_user['token']}",
            "Content-Type": "application/json"
        }

    @task
    def quick_mastery_test(self):
        """Quick mastery query and calculation"""
        # Query
        self.client.post(
            "/api/v1/mastery/query",
            json={"student_id": self.test_user["student_id"]},
            headers=self.auth_headers,
            name="quick_mastery_query"
        )

        # Occasionally calculate
        if random.random() < 0.3:
            pattern = TEST_CONFIG["component_patterns"][0]
            self.client.post(
                "/api/v1/mastery/calculate",
                json={
                    "student_id": self.test_user["student_id"],
                    "components": pattern
                },
                headers=self.auth_headers,
                name="quick_mastery_calc"
            )


if __name__ == "__main__":
    # Quick usage instructions
    print("Mastery Engine Load Testing Script")
    print("="*40)
    print("\nUsage:")
    print("1. Install locust: pip install locust")
    print("2. Set host: export LOCUST_HOST=http://localhost:8005")
    print("3. Set test token: export TEST_JWT_TOKEN=your-test-token")
    print("4. Run: locust -f test_load.py --host=$LOCUST_HOST")
    print("\nWeb UI: http://localhost:8089")
    print("\nCLI example:")
    print("locust -f test_load.py --host=$LOCUST_HOST --users=50 --spawn-rate=5 --run-time=10m --headless")
    print("\nFor smoke test (quick):")
    print("locust -f test_load.py --host=$LOCUST_HOST --users=10 --spawn-rate=2 --run-time=2m --tags quick --headless")
    print("\nFor full load test:")
    print("locust -f test_load.py --host=$LOCUST_HOST --users=100 --spawn-rate=10 --run-time=15m --tags core --headless")
