"""
Load Testing Script with Locust
Tests performance under load conditions
Task: T170

Last Updated: 2026-01-15
"""

from locust import HttpUser, task, between, tag
import random
import json
import time
from typing import Dict, List, Any


class FrontendLoadTest(HttpUser):
    """Frontend application load testing with Locust"""

    # Wait between tasks (1-3 seconds)
    wait_time = between(1, 3)

    # Test user credentials
    test_users = [
        {"email": "test-student@example.com", "password": "TestStudent123!", "studentId": "student-123"},
        {"email": "advanced-student@example.com", "password": "AdvancedStudent123!", "studentId": "student-456"},
    ]

    # Common headers
    common_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def on_start(self):
        """Setup before each user starts testing"""
        self.current_user = random.choice(self.test_users)
        self.jwt_token = None
        self.student_id = self.current_user["studentId"]

        # Perform login
        self.login()

    def login(self):
        """Authenticate user and obtain JWT token"""
        payload = {
            "email": self.current_user["email"],
            "password": self.current_user["password"]
        }

        with self.client.post(
            "/api/auth/login",
            json=payload,
            headers=self.common_headers,
            catch_response=True,
            name="Login"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("token")
                self.common_headers["Authorization"] = f"Bearer {self.jwt_token}"
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with JWT token"""
        headers = self.common_headers.copy()
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers

    @tag('critical')
    @task(10)
    def dashboard_access(self):
        """Test dashboard loading (most critical path)"""
        with self.client.get(
            f"/api/dashboard?studentId={self.student_id}",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Dashboard Access"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Validate key metrics exist
                required_fields = ["masteryScore", "streak", "totalAssignments", "recentActivity"]
                for field in required_fields:
                    if field not in data:
                        response.failure(f"Missing field: {field}")
                        return
                response.success()
            else:
                response.failure(f"Dashboard access failed: {response.status_code}")

    @tag('critical')
    @task(8)
    def code_editor_access(self):
        """Test code editor loading"""
        with self.client.get(
            "/api/editor/config",
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Editor Access"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "language" not in data or "theme" not in data:
                    response.failure("Missing editor configuration")
                response.success()
            else:
                response.failure(f"Editor access failed: {response.status_code}")

    @tag('critical')
    @task(6)
    def execute_code(self):
        """Test code execution endpoint"""
        python_code = f'''
def hello_world():
    print("Hello, Load Test!")
    return "Success"

result = hello_world()
print(f"Student: {self.student_id}")
print(f"Result: {{result}}")
'''

        payload = {
            "code": python_code,
            "language": "python",
            "studentId": self.student_id,
        }

        with self.client.post(
            "/api/code/execute",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Code Execution"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "output" not in data and "error" not in data:
                    response.failure("Missing output or error field")
                response.success()
            else:
                response.failure(f"Code execution failed: {response.status_code}")

    @tag('api')
    @task(5)
    def mastery_calculation(self):
        """Test mastery calculation endpoint"""
        payload = {
            "studentId": self.student_id,
            "topic": random.choice(["python-functions", "data-structures", "algorithms", "web-dev"]),
            "timeSpent": random.randint(300, 3600),  # 5-60 minutes
            "attempts": random.randint(1, 10),
            "difficulty": random.choice(["easy", "medium", "hard"])
        }

        with self.client.post(
            "/api/mastery/calculate",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Mastery Calculation"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Validate response structure
                expected_fields = ["currentScore", "confidence", "trend", "recommendations"]
                for field in expected_fields:
                    if field not in data:
                        response.failure(f"Missing field: {field}")
                        return
                response.success()
            else:
                response.failure(f"Mastery calculation failed: {response.status_code}")

    @tag('api')
    @task(4)
    def batch_processing(self):
        """Test batch processing endpoint"""
        assignments = []
        for i in range(random.randint(1, 5)):
            assignments.append({
                "id": f"assignment-{i}",
                "type": random.choice(["exercise", "quiz", "challenge"]),
                "content": {"problem": f"Test problem {i}"},
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "estimatedTime": random.randint(300, 1800)
            })

        payload = {
            "studentId": self.student_id,
            "assignments": assignments
        }

        with self.client.post(
            "/api/batch/process",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Batch Processing"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "batchId" not in data:
                    response.failure("Missing batchId")
                response.success()
            else:
                response.failure(f"Batch processing failed: {response.status_code}")

    @tag('api')
    @task(4)
    def predictive_analytics(self):
        """Test predictive analytics endpoint"""
        params = {
            "studentId": self.student_id,
            "timeframe": random.choice(["7d", "30d", "90d"]),
            "includeConfidence": "true"
        }

        with self.client.get(
            "/api/analytics/predictions",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Predictive Analytics"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "predictions" not in data:
                    response.failure("Missing predictions")
                response.success()
            else:
                response.failure(f"Analytics request failed: {response.status_code}")

    @tag('api')
    @task(3)
    def cohort_comparison(self):
        """Test cohort comparison endpoint"""
        cohort_id = random.choice(["cohort-1", "cohort-2", "cohort-3"])

        params = {
            "studentId": self.student_id,
            "cohortId": cohort_id,
            "timeframe": "30d",
            "metrics": "mastery,engagement",
            "type": "peer"
        }

        with self.client.get(
            "/api/analytics/cohort-comparison",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Cohort Comparison"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                required = ["studentPerformance", "cohortAverage", "percentileRanks"]
                for field in required:
                    if field not in data:
                        response.failure(f"Missing field: {field}")
                        return
                response.success()
            else:
                response.failure(f"Cohort comparison failed: {response.status_code}")

    @tag('api')
    @task(3)
    def recommendation_generation(self):
        """Test recommendation generation endpoint"""
        payload = {
            "studentId": self.student_id,
            "context": {
                "recentTopics": ["python-functions", "data-structures"],
                "strugglingTopics": ["algorithms"],
                "timeAvailability": random.randint(300, 1800),
                "learningStyle": random.choice(["visual", "auditory", "kinesthetic"]),
                "difficultyPreference": random.choice(["easy", "medium", "hard"])
            },
            "filters": {
                "maxRecommendations": 5,
                "includeTypes": ["exercise", "quiz"]
            }
        }

        with self.client.post(
            "/api/recommendations/generate",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Recommendation Generation"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recommendations" not in data:
                    response.failure("Missing recommendations")
                response.success()
            else:
                response.failure(f"Recommendation generation failed: {response.status_code}")

    @tag('dapr')
    @task(3)
    def dapr_subscription(self):
        """Test Dapr subscription management"""
        payload = {
            "studentId": self.student_id,
            "topics": ["mastery-updated", "feedback-received", "recommendation"],
            "metadata": {"priority": "high"}
        }

        with self.client.post(
            "/api/dapr/subscribe",
            json=payload,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Dapr Subscription"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                if "subscriptionId" not in data:
                    response.failure("Missing subscriptionId")
                response.success()
            else:
                response.failure(f"Dapr subscription failed: {response.status_code}")

    @tag('sse')
    @task(2)
    def sse_connection(self):
        """Test SSE connection stability"""
        # Note: SSE testing with Locust is limited, but we can test the endpoint
        params = {
            "studentId": self.student_id,
            "topics": "mastery-updated,recommendation"
        }

        with self.client.get(
            "/api/dapr/events/stream",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="SSE Connection",
            stream=True  # This won't fully test SSE but checks endpoint accessibility
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"SSE connection failed: {response.status_code}")

    @tag('api')
    @task(2)
    def historical_analytics(self):
        """Test historical analytics endpoint"""
        params = {
            "studentId": self.student_id,
            "timeframe": random.choice(["7d", "30d", "90d"]),
            "granularity": "day",
            "metrics": "mastery,engagement",
            "groupBy": "topic"
        }

        with self.client.post(
            "/api/analytics/historical",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True,
            name="Historical Analytics"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                required = ["data", "summary", "trends"]
                for field in required:
                    if field not in data:
                        response.failure(f"Missing field: {field}")
                        return
                response.success()
            else:
                response.failure(f"Historical analytics failed: {response.status_code}")

    @tag('critical')
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get(
            "/api/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class HighLoadTest(HttpUser):
    """High load testing for critical endpoints"""

    wait_time = between(0.1, 0.5)  # Very short wait for high load

    def on_start(self):
        self.common_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @task(10)
    def stress_test_dashboard(self):
        """Stress test dashboard endpoint with high frequency"""
        self.client.get(
            "/api/dashboard?studentId=stress-test",
            headers=self.common_headers,
            name="Stress - Dashboard"
        )

    @task(5)
    def stress_test_code_execution(self):
        """Stress test code execution"""
        payload = {
            "code": "print('Stress test')",
            "language": "python",
            "studentId": "stress-test"
        }

        self.client.post(
            "/api/code/execute",
            json=payload,
            headers=self.common_headers,
            name="Stress - Code Execution"
        )


class LargeDataLoadTest(HttpUser):
    """Test endpoints with large data payloads"""

    wait_time = between(2, 5)

    def on_start(self):
        self.jwt_token = None
        self.student_id = "large-data-test"
        self.common_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @task(3)
    def large_batch_processing(self):
        """Test batch processing with large number of assignments"""
        assignments = []
        for i in range(20):  # Large batch
            assignments.append({
                "id": f"large-assignment-{i}",
                "type": "exercise",
                "content": {
                    "problem": f"Large test problem {i}",
                    "description": "This is a large test problem with detailed description and instructions",
                    "requirements": ["Requirement 1", "Requirement 2", "Requirement 3"],
                    "hints": ["Hint 1", "Hint 2", "Hint 3"]
                },
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "estimatedTime": random.randint(300, 3600)
            })

        payload = {
            "studentId": self.student_id,
            "assignments": assignments
        }

        with self.client.post(
            "/api/batch/process",
            json=payload,
            headers=self.common_headers,
            catch_response=True,
            name="Large Batch Processing"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "batchId" in data:
                    response.success()
                else:
                    response.failure("Missing batchId")
            else:
                response.failure(f"Large batch failed: {response.status_code}")

    @task(2)
    def complex_analytics_query(self):
        """Test analytics with complex query parameters"""
        params = {
            "studentId": self.student_id,
            "timeframe": "90d",
            "granularity": "hour",
            "metrics": "mastery,engagement,efficiency,resilience,accuracy",
            "groupBy": "topic,difficulty,type",
            "includeConfidence": "true",
            "includePercentiles": "true"
        }

        with self.client.post(
            "/api/analytics/historical",
            params=params,
            headers=self.common_headers,
            catch_response=True,
            name="Complex Analytics Query"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify large data response
                if "data" in data and len(data["data"]) > 0:
                    response.success()
                else:
                    response.failure("No data returned")
            else:
                response.failure(f"Complex query failed: {response.status_code}")

    @task(1)
    def heavy_recommendation_generation(self):
        """Test recommendation generation with complex context"""
        payload = {
            "studentId": self.student_id,
            "context": {
                "recentTopics": ["topic-1", "topic-2", "topic-3", "topic-4", "topic-5"],
                "strugglingTopics": ["topic-6", "topic-7"],
                "completedTopics": ["topic-8", "topic-9", "topic-10"],
                "timeAvailability": 3600,
                "learningStyle": "visual",
                "difficultyPreference": "medium",
                "preferredFormat": "interactive",
                "historicalPerformance": {
                    "averageScore": 0.75,
                    "consistency": 0.8,
                    "improvementRate": 0.15
                }
            },
            "filters": {
                "maxRecommendations": 10,
                "includeTypes": ["exercise", "quiz", "challenge", "project"],
                "difficultyRange": ["easy", "medium", "hard"],
                "timeRange": [300, 3600],
                "excludedTopics": ["topic-11"]
            },
            "metadata": {
                "priority": "high",
                "urgency": "normal",
                "source": "dashboard"
            }
        }

        with self.client.post(
            "/api/recommendations/generate",
            json=payload,
            headers=self.common_headers,
            catch_response=True,
            name="Heavy Recommendation Generation"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recommendations" in data and len(data["recommendations"]) > 0:
                    response.success()
                else:
                    response.failure("No recommendations generated")
            else:
                response.failure(f"Heavy recommendation failed: {response.status_code}")


class ConcurrentUsersLoadTest(HttpUser):
    """Simulate concurrent user behavior"""

    wait_time = between(1, 2)

    def on_start(self):
        self.user_id = f"user-{random.randint(1, 1000)}"
        self.common_headers = {"Content-Type": "application/json"}

    @task(8)
    def concurrent_dashboard_access(self):
        """Simulate multiple users accessing dashboard concurrently"""
        self.client.get(
            f"/api/dashboard?studentId={self.user_id}",
            headers=self.common_headers,
            name="Concurrent - Dashboard"
        )

    @task(6)
    def concurrent_code_execution(self):
        """Simulate concurrent code executions"""
        payload = {
            "code": f"# User {self.user_id}\nprint('Concurrent execution')",
            "language": "python",
            "studentId": self.user_id
        }

        self.client.post(
            "/api/code/execute",
            json=payload,
            headers=self.common_headers,
            name="Concurrent - Code Execution"
        )

    @task(4)
    def concurrent_api_calls(self):
        """Simulate mixed API usage patterns"""
        endpoints = [
            ("GET", "/api/analytics/metrics", {"studentId": self.user_id}),
            ("GET", "/api/recommendations", {"studentId": self.user_id}),
            ("GET", "/api/batch/status", {"batchId": "batch-123"}),
        ]

        method, endpoint, params = random.choice(endpoints)

        if method == "GET":
            self.client.get(
                endpoint,
                params=params,
                headers=self.common_headers,
                name=f"Concurrent - {endpoint}"
            )