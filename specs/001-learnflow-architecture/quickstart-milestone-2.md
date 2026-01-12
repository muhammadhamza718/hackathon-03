# Quickstart Guide: Milestone 2 - Triage Service

**Feature**: `001-learnflow-architecture`
**Milestone**: 2 - Routing Core (Triage Service)
**Generated**: 2026-01-12

## Prerequisites

- ✅ Milestone 1 infrastructure deployed (Kafka, Dapr, PostgreSQL)
- ✅ Kong Gateway configured with JWT plugin
- ✅ Python 3.11+ environment
- ✅ Docker/Kubernetes cluster (Minikube for development)
- ✅ OpenAI API key for Agent SDK

## 1. Local Development Setup

### 1.1 Directory Structure
```bash
cd learnflow-app/backend/triage-service
```

### 1.2 Environment Variables
```bash
# .env
OPENAI_API_KEY=sk-...
KONG_GATEWAY=https://kong-api:8443
DAPR_HTTP_ENDPOINT=http://localhost:3500
DAPR_GRPC_ENDPOINT=localhost:50001
KAFKA_BROKERS=kafka:9092
POSTGRES_URL=postgresql://learnflow_user:password@localhost:5432/learnflow
LOG_LEVEL=INFO
```

### 1.3 Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

**requirements.txt**:
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
openai==1.12.0
dapr-sdk==1.12.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
asyncpg==0.29.0
kafka-python==2.0.2
prometheus-client==0.19.0
```

### 1.4 Run Locally (Dapr)
```bash
# Terminal 1: Run triage-service with Dapr sidecar
dapr run --app-id triage-service --app-port 8000 --dapr-http-port 3500 --dapr-grpc-port 50001 \
  --resources-path ../dapr/components -- uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Test with sample request
curl -X POST http://localhost:3500/v1.0/invoke/triage-service/method/api/v1/triage \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TEST_JWT" \
  -d '{
    "query": "What is polymorphism?",
    "student_progress": {
      "student_id": "student_12345678-1234-1234-1234-123456789012",
      "exercise_id": "ex_oop_basics",
      "completion_score": 0.5,
      "timestamp": "2026-01-12T10:30:00Z",
      "agent_source": "concepts"
    },
    "timestamp": "2026-01-12T10:30:05Z"
  }'
```

## 2. Kubernetes Deployment

### 2.1 Build Container
```bash
docker build -t learnflow/triage-service:1.0.0 -f Dockerfile .
docker push learnflow/triage-service:1.0.0
```

### 2.2 Deploy to Kubernetes
```bash
kubectl apply -f infrastructure/k8s/triage-service/namespace.yaml
kubectl apply -f infrastructure/k8s/triage-service/deployment.yaml
kubectl apply -f infrastructure/k8s/triage-service/service.yaml
kubectl apply -f infrastructure/k8s/triage-service/dapr-config.yaml
```

### 2.3 Verify Deployment
```bash
# Check pods
kubectl get pods -n learnflow -l app=triage-service

# Check Dapr components
kubectl get components -n learnflow

# Check service health
kubectl port-forward svc/triage-service 8000:80 -n learnflow
curl http://localhost:8000/health
```

## 3. Kong Gateway Integration

### 3.1 Configure Service
```bash
# Create Kong service for triage-service
curl -X POST http://kong-admin:8001/services \
  --data name=triage-service \
  --data url=http://triage-service.learnflow.svc.cluster.local:80

# Create route
curl -X POST http://kong-admin:8001/services/triage-service/routes \
  --data name=triage-route \
  --data paths=/api/v1/triage \
  --data methods=POST

# Add JWT plugin
curl -X POST http://kong-admin:8001/services/triage-service/plugins \
  --data name=jwt \
  --data config.key_claim_name=kid \
  --data config.secret_is_base64=false
```

### 3.2 Test Authentication
```bash
# Generate test JWT token
export TEST_JWT=$(python scripts/generate_test_jwt.py --student-id student_12345678-1234-1234-1234-123456789012)

# Test through Kong
curl -X POST https://kong-api:8443/api/v1/triage \
  -H "Authorization: Bearer $TEST_JWT" \
  -H "Content-Type: application/json" \
  -d '{"query": "help with error", "student_progress": {...}}'
```

## 4. Triage Skill Setup

### 4.1 Skill Directory Structure
```bash
skills-library/triage-logic/
├── skill-manifest.yaml
├── intent-classifier.py
├── routing-orchestrator.py
├── schema-validator.py
└── training_data/
    ├── patterns.json
    └── examples.json
```

### 4.2 Skill Manifest
```yaml
# skill-manifest.yaml
name: triage-logic
version: 1.0.0
description: Intent classification and routing logic for triage service
type: python-script
entrypoints:
  classify: intent-classifier.py
  route: routing-orchestrator.py
  validate: schema-validator.py
token_efficiency: 0.90  # 90% reduction vs LLM
license: MIT
```

### 4.3 Intent Classification Script
```python
# intent-classifier.py
#!/usr/bin/env python3
"""
Triage Skill: Intent Classification
Token Efficiency: 90% vs LLM-based classification
"""

import json
import re
from typing import Dict, List, Tuple

def classify_intent(query: str, context: Dict = None) -> Dict:
    """
    Fast deterministic intent classification using keyword matching
    and pattern recognition.
    """
    query_lower = query.lower()

    # Pattern definitions
    patterns = {
        "syntax_help": [
            r"\berror\b", r"\bbug\b", r"\bfix\b", r"\bdoesn'?t work\b",
            r"\bsyntax\b", r"\btraceback\b", r"\bexception\b"
        ],
        "concept_explanation": [
            r"\bwhat is\b", r"\bexplain\b", r"\bhow does\b", r"\bwhy\b",
            r"\bdefine\b", r"\btell me about\b", r"\bconcept of\b"
        ],
        "exercise_request": [
            r"\bexercise\b", r"\bproblem\b", r"\bchallenge\b", r"\bquiz\b",
            r"\bpractice\b", r"\bassignment\b", r"\btask\b"
        ],
        "progress_check": [
            r"\bprogress\b", r"\bmastery\b", r"\bscore\b", r"\blevel\b",
            r"\bstatus\b", r"\bhow am i doing\b", r"\bcurrent\b"
        ]
    }

    scores = {intent: 0 for intent in patterns}
    keywords = []

    # Score each intent type
    for intent, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, query_lower):
                scores[intent] += 1
                keywords.append(pattern)

    # Determine best intent
    best_intent = max(scores, key=scores.get)
    confidence = min(scores[best_intent] / 3, 1.0)  # Normalize

    # Fallback for low confidence
    if confidence < 0.6:
        best_intent = "review"
        confidence = 0.4

    return {
        "intent": best_intent,
        "confidence": confidence,
        "keywords": list(set(keywords))[:5],
        "model_version": "triage-v1.0"
    }

def route_to_agent(intent: str, confidence: float) -> Dict:
    """Map intent to target agent with routing metadata."""
    routing_map = {
        "syntax_help": {"agent": "debug-agent", "priority": "high"},
        "concept_explanation": {"agent": "concepts-agent", "priority": "medium"},
        "exercise_request": {"agent": "exercise-agent", "priority": "medium"},
        "progress_check": {"agent": "progress-agent", "priority": "low"},
        "review": {"agent": "review-agent", "priority": "low"}
    }

    route = routing_map.get(intent, routing_map["review"])
    return {
        "target_agent": route["agent"],
        "dapr_app_id": route["agent"],
        "priority": route["priority"],
        "confidence": confidence
    }

if __name__ == "__main__":
    # Test the skill
    test_query = "What is polymorphism in programming?"
    result = classify_intent(test_query)
    print(json.dumps(result, indent=2))
```

### 4.4 Execute Skill
```bash
# Test classification
python skills-library/triage-logic/intent-classifier.py

# Use in service
dapr run --app-id triage-service -- python src/main.py
```

## 5. Testing & Validation

### 5.1 Unit Tests
```bash
# Run unit tests
pytest tests/unit/ -v

# Test coverage
pytest --cov=src --cov-report=html
```

**Sample Test Cases**:
```python
# test_intent_classification.py
def test_syntax_help_classification():
    result = classify_intent("I'm getting a TypeError")
    assert result["intent"] == "syntax_help"
    assert result["confidence"] > 0.8

def test_low_confidence_fallback():
    result = classify_intent("maybe")
    assert result["intent"] == "review"
    assert result["confidence"] < 0.6
```

### 5.2 Integration Tests
```bash
# Start test infrastructure
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Chaos testing
pytest tests/chaos/ -v
```

### 5.3 Performance Tests
```bash
# Load testing with k6
k6 run tests/performance/load.js

# Benchmark classification
python scripts/benchmark.py --iterations 1000
```

**Expected Results**:
- Classification: 150ms p95
- Full triage flow: 500ms p95
- Throughput: 1000 RPS sustained

### 5.4 Security Tests
```bash
# Test JWT validation
pytest tests/security/test_auth.py

# Test injection attacks
python scripts/security_audit.py
```

## 6. Monitoring & Observability

### 6.1 Health Endpoints
```bash
# Service health
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics

# Readiness probe (Dapr)
curl http://localhost:3500/v1.0/healthz
```

### 6.2 Key Metrics to Monitor

**Application Metrics**:
```
triage_requests_total{intent_type, status} - Counter
triage_latency_seconds_bucket - Histogram
classification_confidence_score - Gauge
circuit_breaker_events_total{state} - Counter
```

**Dapr Metrics**:
```
dapr_service_invocation_total{target, status} - Counter
dapr_circuit_breaker_state{target} - Gauge
dapr_retry_attempts_total{target} - Counter
```

**Infrastructure Metrics**:
- CPU/Memory usage per pod
- Kong gateway latency
- Kafka consumer lag
- PostgreSQL connection pool

### 6.3 Alerting Rules

**Critical**:
- P95 latency > 1s for 5 minutes
- Circuit breaker open for any agent
- Authentication failure rate > 5%

**Warning**:
- Classification confidence < 0.7 average
- Retry rate > 10%
- Resource usage > 80%

## 7. Troubleshooting

### 7.1 Common Issues

**Issue**: Circuit breaker stays open
```bash
# Check Dapr component status
kubectl get components -n learnflow

# Check circuit breaker metrics
kubectl logs -n learnflow -l app=triage-service | grep circuit_breaker

# Reset circuit breaker (test only)
curl -X POST http://localhost:3500/v1.0/circuit-breaker/reset
```

**Issue**: Intent classification returning low confidence
```bash
# Check keyword patterns
python scripts/debug_classification.py --query "your test query"

# Review training data
cat skills-library/triage-logic/training_data/patterns.json

# Update patterns if needed
```

**Issue**: JWT validation failures
```bash
# Check Kong plugin config
curl http://kong-admin:8001/services/triage-service/plugins

# Test token generation
python scripts/generate_test_jwt.py --debug

# Verify token claims
python scripts/decode_jwt.py --token $JWT
```

### 7.2 Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=DEBUG dapr run --app-id triage-service -- python src/main.py

# Enable verbose classification
INTENT_DEBUG=1 python skills-library/triage-logic/intent-classifier.py
```

### 7.3 Log Queries
```bash
# View triage decisions
kubectl logs -n learnflow -l app=triage-service --tail=100 | grep "routing_decision"

# View circuit breaker events
kubectl logs -n learnflow -l app=triage-service --tail=100 | grep "circuit_breaker"

# View authentication failures
kubectl logs -n learnflow -l app=triage-service --tail=100 | grep "auth_failure"
```

## 8. Next Steps After Setup

### 8.1 Validation Checkpoints
- [ ] All unit tests passing (>95% coverage)
- [ ] Integration tests successful with real Dapr
- [ ] JWT authentication working via Kong
- [ ] Circuit breaker triggers on agent failures
- [ ] Intent classification >90% accuracy
- [ ] Load test passes 1000 RPS
- [ ] Audit logs complete and queryable

### 8.2 Production Readiness
- [ ] Resource limits configured
- [ ] Monitoring dashboards deployed
- [ ] Alerting rules tested
- [ ] Backup and restore procedures documented
- [ ] Disaster recovery plan in place
- [ ] Security audit completed

### 8.3 Scale Testing
- [ ] 1000 concurrent students
- [ ] 50 RPS sustained load
- [ ] 1000 RPS peak burst
- [ ] Circuit breaker chaos testing
- [ ] Network partition scenarios

## 9. Quick Test Script

Save as `test_triage.py`:

```python
#!/usr/bin/env python3
"""
Quick test of complete triage flow
"""

import requests
import json

def test_triage_flow():
    # Generate test JWT (requires jose library)
    from jose import jwt

    secret = "test-secret"
    token = jwt.encode(
        {
            "sub": "student_12345678-1234-1234-1234-123456789012",
            "role": "student",
            "exp": 9999999999
        },
        secret
    )

    # Test request
    response = requests.post(
        "http://localhost:8000/api/v1/triage",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "query": "I need help with my function",
            "student_progress": {
                "student_id": "student_12345678-1234-1234-1234-123456789012",
                "exercise_id": "ex_test",
                "completion_score": 0.5,
                "timestamp": "2026-01-12T10:30:00Z",
                "agent_source": "exercise"
            },
            "timestamp": "2026-01-12T10:30:05Z"
        }
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_triage_flow()
```

Run: `python test_triage.py`

---

## Success Criteria

✅ **Setup Complete** when:
- Triage service responds on `/health`
- JWT authentication works via Kong
- Intent classification returns valid results
- Dapr service invocation succeeds
- Audit logs are generated
- All tests pass

**Estimated Time**: 30-60 minutes for complete setup
**Difficulty**: Medium (requires Docker/K8s experience)

**Need Help?**: Check `specs/001-learnflow-architecture/research-milestone-2.md` for architectural decisions and troubleshooting details.