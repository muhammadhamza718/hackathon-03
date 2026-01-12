# Claude Agent Context for LearnFlow

**Generated**: 2026-01-12
**Branch**: 001-learnflow-architecture
**Milestone**: 2 - Triage Service

## Project Configuration

### Architecture
- **Framework**: FastAPI + OpenAI Agent SDK
- **Orchestration**: Dapr service mesh
- **Messaging**: Apache Kafka (events)
- **Auth**: Kong Gateway with JWT
- **Schema**: Pydantic v2 + JSON Schema

### Milestone 1 (Complete)
- ✅ Infrastructure deployed (Kafka, Dapr, PostgreSQL)
- ✅ Schemas generated (JSON + Avro)
- ✅ ADR-001: Infrastructure selection
- ✅ 91% token efficiency achieved

### Milestone 2 (In Progress)
- **Service**: Triage Service (FastAPI)
- **Skill**: triage-logic (intent classification)
- **Integration**: Dapr service invocation + Kong JWT

## Key Technology Stack

### New for Milestone 2
```python
# Core Dependencies
fastapi==0.109.0              # Web framework
openai==1.12.0                # Agent SDK for intent detection
dapr-sdk==1.12.0              # Service orchestration
pydantic==2.5.3              # Schema validation
python-jose==3.3.0           # JWT handling
```

### Intent Classification Approaches
1. **Function Calling**: OpenAI Agent SDK with structured output
2. **Keyword Matching**: Local script for token efficiency
3. **Pattern Recognition**: Regex + scoring system

### Dapr Resilience Patterns
```yaml
# Circuit Breaker
maxConsecutiveFailures: 5
timeout: 30s

# Retry Policy
maxAttempts: 3
backoff: exponential (100ms → 400ms)
```

### Kong Authentication
```yaml
Plugin: jwt
Claims: exp, iat, sub (student_id)
Key Claim: kid
Validation: At gateway edge
```

## Code Generation Patterns

### FastAPI Service Structure
```
src/
├── main.py                 # App entrypoint
├── api/routes.py          # /api/v1/triage endpoint
├── services/
│   ├── intent_detection.py   # OpenAI Agent SDK
│   ├── routing_logic.py      # Dapr invocation
│   └── schema_validator.py   # Pydantic v2
└── models/
    └── schemas.py         # Pydantic models
```

### Skill Pattern (Triage-Logic)
```python
#!/usr/bin/env python3
"""
Intent Classification Skill
Token Efficiency: 90% vs LLM implementation
"""

def classify_intent(query: str) -> Dict:
    # Keyword + pattern matching
    # Deterministic, fast, efficient
    return {"intent": "...", "confidence": 0.95}

def route_to_agent(intent: str) -> Dict:
    # Dapr service invocation logic
    # Circuit breaker integration
    return {"target": "agent-x", "metadata": {...}}
```

### Schema Validation
```python
from pydantic import BaseModel

class TriageRequest(BaseModel):
    query: str
    student_progress: StudentProgress  # From M1
    timestamp: str
```

## Configuration Examples

### Dapr Component (Triage Service)
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: triage-service
spec:
  type: service
  metadata:
    - name: app-id
      value: triage-service
```

### Kong Route Configuration
```bash
# Service
curl -X POST http://kong-admin:8001/services \
  --data name=triage-service \
  --data url=http://triage-service:80

# Route
curl -X POST http://kong-admin:8001/services/triage-service/routes \
  --data paths=/api/v1/triage

# JWT Plugin
curl -X POST http://kong-admin:8001/services/triage-service/plugins \
  --data name=jwt
```

## Testing Strategy

### Unit Tests (pytest)
- Intent classification accuracy (>95%)
- Schema validation speed (<1ms)
- Routing decision logic
- Circuit breaker behavior

### Integration Tests
- End-to-end triage flow
- Dapr service invocation
- Kong JWT validation
- Error handling scenarios

### Performance Tests
- 1000 RPS load test
- p95 latency <500ms
- Memory usage <4GB
- Circuit breaker chaos

## Key Commands

### Local Development
```bash
# Run with Dapr sidecar
dapr run --app-id triage-service --app-port 8000 \
  --resources-path ../dapr/components \
  -- uvicorn src.main:app --reload

# Test classification skill
python skills-library/triage-logic/intent-classifier.py
```

### Deployment
```bash
# Build and push
docker build -t learnflow/triage-service:1.0.0 .
docker push learnflow/triage-service:1.0.0

# Deploy to K8s
kubectl apply -f infrastructure/k8s/triage-service/
```

## Success Criteria

### Milestone 2 Complete When:
- [ ] Triage service deployed and healthy
- [ ] Intent classification >95% accuracy
- [ ] Dapr routing working with all 5 agents
- [ ] JWT authentication via Kong successful
- [ ] Circuit breaker triggers on failures
- [ ] Audit logs complete and searchable
- [ ] Load test passes 1000 RPS
- [ ] 90% token efficiency achieved

### Next Steps
1. Generate tasks.md via `/sp.tasks`
2. Execute tasks in phases
3. Verify each phase with tests
4. Document findings in ADRs

## Learning Objectives

This milestone teaches:
- **Dapr Service Invocation**: Request/response patterns
- **Resilience Engineering**: Circuit breakers and retries
- **Schema Governance**: Contract-first development
- **Token Optimization**: Skills vs LLM usage
- **Auth Integration**: Gateway-level security

## Pitfalls to Avoid

- ❌ Manual schema validation (use Pydantic)
- ❌ Direct service-to-service calls (use Dapr)
- ❌ LLM-based classification for simple queries
- ❌ Bypassing Kong (reinvent security wheel)
- ❌ Ignoring circuit breaker configuration

---

**Context Last Updated**: 2026-01-12
**Ready for**: Task generation and implementation