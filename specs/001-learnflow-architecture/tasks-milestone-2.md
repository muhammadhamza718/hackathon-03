# Task Breakdown: Milestone 2 - Triage Service Implementation

**Feature**: `001-learnflow-architecture`
**Milestone**: 2 - Routing Core (Triage Service)
**Generated**: 2026-01-12
**Status**: Ready for Execution
**Branch**: `001-learnflow-architecture`

## Executive Summary

This tasks.md contains **67 executable tasks** organized across 5 phases to build the Triage Service with all 5 architectural mandates integrated. Each task follows Senior Engineer constraints:

- **Skills-First**: 80-98% token efficiency via triage-logic skill library
- **Test-Driven**: Verification after each phase
- **Atomic**: One specific action per task
- **Referenced**: Exact file paths from existing artifacts
- **ADR-Ready**: Architecture decisions flagged for documentation

## Project Structure (Source Code)

```text
learnflow-app/
├── backend/
│   ├── triage-service/           # New service
│   │   ├── src/
│   │   │   ├── main.py          # FastAPI entrypoint
│   │   │   ├── api/
│   │   │   │   ├── routes.py    # /api/v1/triage
│   │   │   │   └── middleware/  # JWT validation
│   │   │   ├── services/
│   │   │   │   ├── intent_detection.py  # OpenAI Agent SDK
│   │   │   │   ├── routing_logic.py     # Dapr + resilience
│   │   │   │   └── schema_validator.py  # Pydantic v2
│   │   │   └── models/
│   │   │       ├── schemas.py   # Pydantic models
│   │   │       └── errors.py    # Custom errors
│   │   ├── skills/
│   │   │   └── triage-logic/    # Skill library
│   │   │       ├── intent-classifier.py  # 90% token efficiency
│   │   │       ├── routing-orchestrator.py
│   │   │       ├── schema-validator.py
│   │   │       ├── skill-manifest.yaml
│   │   │       └── training_data/
│   │   ├── tests/
│   │   │   ├── unit/           # 95% coverage
│   │   │   ├── integration/    # Dapr + OpenAI
│   │   │   └── contract/       # Schema validation
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── skills-library/           # Updated
│       └── triage-logic/        # Skill references
├── infrastructure/
│   ├── k8s/
│   │   ├── triage-service/      # Deployment manifests
│   │   └── kong/               # JWT plugin config
│   └── dapr/
│       └── components/         # Triage service config
└── docs/
    └── architecture/
        └── triage-service.md   # ADRs
```

---

## Phase 0: Skills Library (Token Efficiency Foundation)

**Goal**: Create triage-logic skill library for 90% token reduction vs LLM-based classification

### 0.1 Skill Foundation (Tasks 0.1-0.5) [P1] [US: 8]
- [ ] **[0.1]** Create skill directory structure: `skills-library/triage-logic/`
  **Files**: `skills-library/triage-logic/` (directory)
  **Verification**: Directory exists with correct permissions
- [ ] **[0.2]** Create skill manifest: `skills-library/triage-logic/skill-manifest.yaml`
  **Files**: `skills-library/triage-logic/skill-manifest.yaml`
  **Verification**: `cat skills-library/triage-logic/skill-manifest.yaml | grep -E "name:|version:|token_efficiency: 0.90"`
- [ ] **[0.3]** Create intent classifier script: `skills-library/triage-logic/intent-classifier.py`
  **Files**: `skills-library/triage-logic/intent-classifier.py`
  **Verification**: `python skills-library/triage-logic/intent-classifier.py` returns valid JSON with intent, confidence, keywords
- [ ] **[0.4]** Create pattern training data: `skills-library/triage-logic/training_data/patterns.json`
  **Files**: `skills-library/triage-logic/training_data/patterns.json`
  **Verification**: File contains patterns for all 4 intent types (syntax_help, concept_explanation, exercise_request, progress_check)
- [ ] **[0.5]** Create routing orchestrator: `skills-library/triage-logic/routing-orchestrator.py`
  **Files**: `skills-library/triage-logic/routing-orchestrator.py`
  **Verification**: Script maps intent → agent with Dapr app_id

### 0.2 Skill Testing & Optimization (Tasks 0.6-0.10) [P1] [US: 5]
- [ ] **[0.6]** Create unit tests for intent classification: `tests/unit/test_intent_classification.py`
  **Files**: `backend/triage-service/tests/unit/test_intent_classification.py`
  **Verification**: `pytest tests/unit/test_intent_classification.py -v` passes
- [ ] **[0.7]** Create token efficiency benchmark: `scripts/benchmark_token_usage.py`
  **Files**: `backend/triage-service/scripts/benchmark_token_usage.py`
  **Verification**: Script reports <1000 tokens per classification
- [ ] **[0.8]** Optimize classification algorithm for speed: Update `skills-library/triage-logic/intent-classifier.py`
  **Files**: `skills-library/triage-logic/intent-classifier.py`
  **Verification**: `python scripts/benchmark_token_usage.py` shows <150ms classification time
- [ ] **[0.9]** Create skill integration test: `tests/integration/test_skill_integration.py`
  **Files**: `backend/triage-service/tests/integration/test_skill_integration.py`
  **Verification**: `pytest tests/integration/test_skill_integration.py -v` passes
- [ ] **[0.10]** Verify 90% token efficiency target: Document in `skills-library/triage-logic/skill-manifest.yaml`
  **Files**: `skills-library/triage-logic/skill-manifest.yaml`
  **Verification**: Manifest shows `token_efficiency: 0.90`

**🎯 Phase 0 Verification**:
- **Success Criteria**: Skill library achieves 90% token reduction vs LLM-based classification
- **Test Command**: `python skills-library/triage-logic/intent-classifier.py && pytest tests/unit/ -v`
- **ADR Suggestion**: 📋 **Token Efficiency Architecture**: "Using deterministic skill library vs LLM for intent classification"
  **Action**: Run `/sp.adr token-efficiency-skill-library` if approved

---

## Phase 1: Service Core (FastAPI + Models)

**Goal**: Create FastAPI service with Pydantic models from existing contracts

### 1.1 Project Setup (Tasks 1.1-1.5) [P1] [US: 6]
- [ ] **[1.1]** Create triage-service directory: `backend/triage-service/`
  **Files**: `backend/triage-service/` (directory)
  **Verification**: Directory structure matches plan-milestone-2.md
- [ ] **[1.2]** Generate requirements.txt: `backend/triage-service/requirements.txt`
  **Files**: `backend/triage-service/requirements.txt`
  **Verification**: Contains all dependencies from quickstart-milestone-2.md
- [ ] **[1.3]** Create FastAPI main entrypoint: `backend/triage-service/src/main.py`
  **Files**: `backend/triage-service/src/main.py`
  **Verification**: `python -m uvicorn src.main:app --reload` starts without errors
- [ ] **[1.4]** Create Pydantic schemas: `backend/triage-service/src/models/schemas.py`
  **Files**: `backend/triage-service/src/models/schemas.py`
  **Verification**: All models from data-model-milestone-2.md are implemented (TriageRequest, IntentClassification, RoutingDecision, TriageAudit)
- [ ] **[1.5]** Create custom error types: `backend/triage-service/src/models/errors.py`
  **Files**: `backend/triage-service/src/models/errors.py`
  **Verification**: Contains custom exceptions for validation, auth, routing failures

### 1.2 API Layer (Tasks 1.6-1.10) [P1] [US: 7]
- [ ] **[1.6]** Create main API routes: `backend/triage-service/src/api/routes.py`
  **Files**: `backend/triage-service/src/api/routes.py`
  **Verification**: Implements `POST /api/v1/triage` endpoint from openapi/triage-service.yaml
- [ ] **[1.7]** Create JWT validation middleware: `backend/triage-service/src/api/middleware/auth.py`
  **Files**: `backend/triage-service/src/api/middleware/auth.py`
  **Verification**: Middleware extracts student_id from Kong header `X-Consumer-Username`
- [ ] **[1.8]** Register middleware in main.py: Update `backend/triage-service/src/main.py`
  **Files**: `backend/triage-service/src/main.py`
  **Verification**: Middleware added to FastAPI app
- [ ] **[1.9]** Create health check endpoint: Add to `backend/triage-service/src/api/routes.py`
  **Files**: `backend/triage-service/src/api/routes.py`
  **Verification**: `curl http://localhost:8000/health` returns 200
- [ ] **[1.10]** Create metrics endpoint: Add to `backend/triage-service/src/api/routes.py`
  **Files**: `backend/triage-service/src/api/routes.py`
  **Verification**: `curl http://localhost:8000/metrics` returns Prometheus format

### 1.3 Schema Validation Service (Tasks 1.11-1.15) [P1] [US: 5]
- [ ] **[1.11]** Create schema validator service: `backend/triage-service/src/services/schema_validator.py`
  **Files**: `backend/triage-service/src/services/schema_validator.py`
  **Verification**: Uses Pydantic v2 for <1ms validation from research-milestone-2.md
- [ ] **[1.12]** Validate TriageRequest input: Implement in `schema_validator.py`
  **Files**: `backend/triage-service/src/services/schema_validator.py`
  **Verification**: Validates against StudentProgress schema from M1
- [ ] **[1.13]** Validate RoutingDecision output: Implement in `schema_validator.py`
  **Files**: `backend/triage-service/src/services/schema_validator.py`
  **Verification**: Validates all 5 required fields from data-model-milestone-2.md
- [ ] **[1.14]** Create validation unit tests: `tests/unit/test_schema_validation.py`
  **Files**: `backend/triage-service/tests/unit/test_schema_validation.py`
  **Verification**: `pytest tests/unit/test_schema_validation.py -v` passes
- [ ] **[1.15]** Benchmark validation performance: Update `scripts/benchmark_token_usage.py`
  **Files**: `backend/triage-service/scripts/benchmark_token_usage.py`
  **Verification**: Reports <1ms average validation time

**🎯 Phase 1 Verification**:
- **Success Criteria**: FastAPI service running with all Pydantic models validated
- **Test Command**: `python -m uvicorn src.main:app --port 8000` + `curl http://localhost:8000/health`
- **ADR Suggestion**: 📋 **Pydantic v2 Performance**: "Using Pydantic v2 for <1ms schema validation overhead"
  **Action**: Run `/sp.adr pydantic-v2-performance` if approved

---

## Phase 2: Integration (Dapr + OpenAI SDK)

**Goal**: Integrate intent detection, Dapr service invocation, and resilience patterns

### 2.1 Intent Detection (Tasks 2.1-2.5) [P1] [US: 10]
- [ ] **[2.1]** Create intent detection service: `backend/triage-service/src/services/intent_detection.py`
  **Files**: `backend/triage-service/src/services/intent_detection.py`
  **Verification**: Integrates OpenAI Agent SDK per research-milestone-2.md
- [ ] **[2.2]** Configure OpenAI Agent SDK: Add function-calling pattern
  **Files**: `backend/triage-service/src/services/intent_detection.py`
  **Verification**: Implements `classify_intent` function with 4 intent types
- [ ] **[2.3]** Connect skill library to service: Update `intent_detection.py`
  **Files**: `backend/triage-service/src/services/intent_detection.py`
  **Verification**: Service calls `skills-library/triage-logic/intent-classifier.py`
- [ ] **[2.4]** Create OpenAI integration tests: `tests/integration/test_openai_integration.py`
  **Files**: `backend/triage-service/tests/integration/test_openai_integration.py`
  **Verification**: Tests mock OpenAI responses, validates structured output
- [ ] **[2.5]** Add fallback to skill library: Implement in `intent_detection.py`
  **Files**: `backend/triage-service/src/services/intent_detection.py`
  **Verification**: If OpenAI fails, falls back to deterministic skill classification

### 2.2 Dapr Service Invocation (Tasks 2.6-2.10) [P1] [US: 12]
- [ ] **[2.6]** Create routing logic service: `backend/triage-service/src/services/routing_logic.py`
  **Files**: `backend/triage-service/src/services/routing_logic.py`
  **Verification**: Implements intent → agent mapping from data-model-milestone-2.md
- [ ] **[2.7]** Implement Dapr client: Use Dapr SDK in `routing_logic.py`
  **Files**: `backend/triage-service/src/services/routing_logic.py`
  **Verification**: Uses `DaprClient` for service invocation
- [ ] **[2.8]** Create circuit breaker configuration: `infrastructure/dapr/components/resiliency.yaml`
  **Files**: `infrastructure/dapr/components/resiliency.yaml`
  **Verification**: Matches research-milestone-2.md config (5 failures → 30s open)
- [ ] **[2.9]** Implement retry policy: Add to `routing_logic.py`
  **Files**: `backend/triage-service/src/services/routing_logic.py`
  **Verification**: 3 attempts, exponential backoff (100ms → 400ms)
- [ ] **[2.10]** Create Dapr integration tests: `tests/integration/test_dapr_routing.py`
  **Files**: `backend/triage-service/tests/integration/test_dapr_routing.py`
  **Verification**: Tests circuit breaker, retry logic, and agent routing

### 2.3 Integration Layer (Tasks 2.11-2.15) [P1] [US: 8]
- [ ] **[2.11]** Connect API route to intent detection: Update `routes.py`
  **Files**: `backend/triage-service/src/api/routes.py`
  **Verification**: `/api/v1/triage` calls `intent_detection.classify_intent()`
- [ ] **[2.12]** Connect intent to routing logic: Update `routes.py`
  **Files**: `backend/triage-service/src/api/routes.py`
  **Verification**: Intent result passed to `routing_logic.route_to_agent()`
- [ ] **[2.13]** Implement audit logging: `backend/triage-service/src/services/audit_logger.py`
  **Files**: `backend/triage-service/src/services/audit_logger.py`
  **Verification**: Creates TriageAudit records, publishes to Kafka
- [ ] **[2.14]** Add error handling middleware: Update `backend/triage-service/src/api/middleware/`
  **Files**: `backend/triage-service/src/api/middleware/error_handler.py`
  **Verification**: Handles circuit breaker, auth, validation errors per openapi spec
- [ ] **[2.15]** Complete end-to-end flow test: `tests/integration/test_end_to_end.py`
  **Files**: `backend/triage-service/tests/integration/test_end_to_end.py`
  **Verification**: Full triage flow from request → classification → routing → response

**🎯 Phase 2 Verification**:
- **Success Criteria**: End-to-end triage flow working with Dapr circuit breakers
- **Test Command**: `pytest tests/integration/ -v` + manual Dapr invocation test
- **ADR Suggestion**: 📋 **Dapr Resilience Architecture**: "Circuit breaker patterns for educational service reliability"
  **Action**: Run `/sp.adr dapr-resilience-patterns` if approved

---

## Phase 3: Security (Kong JWT + Middleware)

**Goal**: Integrate Kong JWT validation and secure the triage endpoint

### 3.1 JWT Configuration (Tasks 3.1-3.5) [P1] [US: 7]
- [ ] **[3.1]** Create Kong JWT plugin config: `infrastructure/kong/plugins/jwt-config.yaml`
  **Files**: `infrastructure/kong/plugins/jwt-config.yaml`
  **Verification**: Matches research-milestone-2.md JWT structure
- [ ] **[3.2]** Create Kong service definition: `infrastructure/kong/services/triage-service.yaml`
  **Files**: `infrastructure/kong/services/triage-service.yaml`
  **Verification**: Service routes to triage-service with JWT plugin
- [ ] **[3.3]** Create Kong route config: `infrastructure/kong/services/triage-route.yaml`
  **Files**: `infrastructure/kong/services/triage-route.yaml`
  **Verification**: Route matches `/api/v1/triage` path
- [ ] **[3.4]** Create test JWT generation script: `scripts/generate_test_jwt.py`
  **Files**: `backend/triage-service/scripts/generate_test_jwt.py`
  **Verification**: Script generates valid JWT with student_id in `sub` claim
- [ ] **[3.5]** Verify Kong integration: `tests/integration/test_kong_jwt.py`
  **Files**: `backend/triage-service/tests/integration/test_kong_jwt.py`
  **Verification**: Tests pass with valid JWT, fail without

### 3.2 Middleware & Auth (Tasks 3.6-3.10) [P1] [US: 6]
- [ ] **[3.6]** Enhance JWT middleware: Update `backend/triage-service/src/api/middleware/auth.py`
  **Files**: `backend/triage-service/src/api/middleware/auth.py`
  **Verification**: Extracts `X-Consumer-Username` header, validates format
- [ ] **[3.7]** Add student_id to request context: Update middleware
  **Files**: `backend/triage-service/src/api/middleware/auth.py`
  **Verification**: Sets `request.state.student_id` for audit logging
- [ ] **[3.8]** Create authorization middleware: `backend/triage-service/src/api/middleware/authorization.py`
  **Files**: `backend/triage-service/src/api/middleware/authorization.py`
  **Verification**: Validates student permissions for triage endpoint
- [ ] **[3.9]** Add security tests: `tests/security/test_jwt_validation.py`
  **Files**: `backend/triage-service/tests/security/test_jwt_validation.py`
  **Verification**: Tests token expiration, invalid signatures, missing headers
- [ ] **[3.10]** Implement rate limiting: `backend/triage-service/src/api/middleware/rate_limiter.py`
  **Files**: `backend/triage-service/src/api/middleware/rate_limiter.py`
  **Verification**: 100 requests/minute per student (from openapi spec)

### 3.3 Security Testing (Tasks 3.11-3.15) [P1] [US: 5]
- [ ] **[3.11]** Create security audit script: `scripts/security_audit.py`
  **Files**: `backend/triage-service/scripts/security_audit.py`
  **Verification**: Tests injection attacks, JWT bypass attempts
- [ ] **[3.12]** Test injection prevention: `tests/security/test_input_validation.py`
  **Files**: `backend/triage-service/tests/security/test_input_validation.py`
  **Verification**: SQL injection, XSS attempts are blocked
- [ ] **[3.13]** Verify Kong ↔ Service auth contract: Update integration tests
  **Files**: `backend/triage-service/tests/integration/test_kong_jwt.py`
  **Verification**: Headers properly passed, student_id extracted
- [ ] **[3.14]** Create security compliance report: `docs/security/compliance.md`
  **Files**: `backend/triage-service/docs/security/compliance.md`
  **Verification**: Documents GDPR, data classification from data-model-milestone-2.md
- [ ] **[3.15]** Run security penetration test: Manual verification
  **Verification**: Attempt unauthorized access, validate all security controls

**🎯 Phase 3 Verification**:
- **Success Criteria**: All triage requests require valid JWT, student_id properly extracted
- **Test Command**: `pytest tests/security/ -v` + `curl` with/without JWT
- **ADR Suggestion**: 📋 **Gateway Auth Architecture**: "Kong JWT validation at edge vs service-level auth"
  **Action**: Run `/sp.adr kong-jwt-edge-auth` if approved

---

## Phase 4: Testing & Optimization

**Goal**: Achieve 95% test coverage and verify performance targets

### 4.1 Unit Testing (Tasks 4.1-4.5) [P2] [US: 8]
- [ ] **[4.1]** Create comprehensive unit test suite: `tests/unit/`
  **Files**: `backend/triage-service/tests/unit/`
  **Verification**: `pytest tests/unit/ --cov=src --cov-report=html` shows >95% coverage
- [ ] **[4.2]** Test skill library components: `tests/unit/test_skill_library.py`
  **Files**: `backend/triage-service/tests/unit/test_skill_library.py`
  **Verification**: All 4 intent types classified correctly
- [ ] **[4.3]** Test Pydantic models: `tests/unit/test_pydantic_models.py`
  **Files**: `backend/triage-service/tests/unit/test_pydantic_models.py`
  **Verification**: All schema validations work, edge cases covered
- [ ] **[4.4]** Test routing logic: `tests/unit/test_routing_logic.py`
  **Files**: `backend/triage-service/tests/unit/test_routing_logic.py`
  **Verification**: Intent→agent mapping correct, fallback logic works
- [ ] **[4.5]** Test error handling: `tests/unit/test_error_handling.py`
  **Files**: `backend/triage-service/tests/unit/test_error_handling.py`
  **Verification**: All error paths return correct status codes

### 4.2 Integration Testing (Tasks 4.6-4.10) [P2] [US: 10]
- [ ] **[4.6]** Create test infrastructure: `docker-compose.test.yml`
  **Files**: `backend/triage-service/docker-compose.test.yml`
  **Verification**: Includes Dapr, mock agents, test DB
- [ ] **[4.7]** Test end-to-end triage flow: `tests/integration/test_e2e_triage.py`
  **Files**: `backend/triage-service/tests/integration/test_e2e_triage.py`
  **Verification**: Complete flow: JWT → validation → classification → routing → response
- [ ] **[4.8]** Test circuit breaker behavior: `tests/chaos/test_circuit_breaker.py`
  **Files**: `backend/triage-service/tests/chaos/test_circuit_breaker.py`
  **Verification**: Triggers after 5 failures, recovers after 30s
- [ ] **[4.9]** Test OpenAI fallback: `tests/integration/test_fallback.py`
  **Files**: `backend/triage-service/tests/integration/test_fallback.py`
  **Verification**: Falls back to skill library when OpenAI fails
- [ ] **[4.10]** Test Kafka audit publishing: `tests/integration/test_audit_logging.py`
  **Files**: `backend/triage-service/tests/integration/test_audit_logging.py`
  **Verification**: Audit events published to Kafka topic

### 4.3 Performance Testing (Tasks 4.11-4.15) [P2] [US: 7]
- [ ] **[4.11]** Create load test script: `tests/performance/load.js` (k6)
  **Files**: `backend/triage-service/tests/performance/load.js`
  **Verification**: Simulates 1000 RPS sustained load
- [ ] **[4.12]** Benchmark classification speed: `scripts/benchmark_classification.py`
  **Files**: `backend/triage-service/scripts/benchmark_classification.py`
  **Verification**: Reports p95 <200ms for intent classification
- [ ] **[4.13]** Measure total triage latency: Update benchmark script
  **Files**: `backend/triage-service/scripts/benchmark_classification.py`
  **Verification**: Reports p95 <500ms for complete triage flow
- [ ] **[4.14]** Test memory usage: `scripts/benchmark_memory.py`
  **Files**: `backend/triage-service/scripts/benchmark_memory.py`
  **Verification**: Memory usage <2GB baseline, <4GB under load
- [ ] **[4.15]** Run chaos testing: `pytest tests/chaos/ -v`
  **Files**: `backend/triage-service/tests/chaos/`
  **Verification**: System handles agent failures, network issues gracefully

### 4.4 Token Efficiency Validation (Tasks 4.16-4.18) [P2] [US: 5]
- [ ] **[4.16]** Compare skill vs LLM token usage: `scripts/compare_efficiency.py`
  **Files**: `backend/triage-service/scripts/compare_efficiency.py`
  **Verification**: Reports 90%+ token reduction
- [ ] **[4.17]** Create efficiency dashboard: `docs/performance/token-efficiency.md`
  **Files**: `backend/triage-service/docs/performance/token-efficiency.md`
  **Verification**: Documents metrics from benchmarks
- [ ] **[4.18]** Verify target achievement: Update skill-manifest.yaml
  **Files**: `skills-library/triage-logic/skill-manifest.yaml`
  **Verification**: Confirms 90% token efficiency target met

**🎯 Phase 4 Verification**:
- **Success Criteria**: 95% test coverage, p95 latency <500ms, 90% token efficiency
- **Test Command**: `pytest --cov=src --cov-report=html && k6 run tests/performance/load.js`
- **ADR Suggestion**: 📋 **Performance Architecture**: "Performance budgets and optimization strategies for educational platform"
  **Action**: Run `/sp.adr performance-budget-architecture` if approved

---

## Phase 5: Deployment & Monitoring

**Goal**: Kubernetes deployment, monitoring, and production readiness

### 5.1 Container & Deployment (Tasks 5.1-5.5) [P2] [US: 8]
- [ ] **[5.1]** Create Dockerfile: `backend/triage-service/Dockerfile`
  **Files**: `backend/triage-service/Dockerfile`
  **Verification**: Multi-stage build, minimal base image
- [ ] **[5.2]** Create Kubernetes manifests: `infrastructure/k8s/triage-service/`
  **Files**: `infrastructure/k8s/triage-service/deployment.yaml`
  **Verification**: Includes Dapr sidecar, resource limits, health checks
- [ ] **[5.3]** Create service definition: `infrastructure/k8s/triage-service/service.yaml`
  **Files**: `infrastructure/k8s/triage-service/service.yaml`
  **Verification**: ClusterIP service for Dapr invocation
- [ ] **[5.4]** Create Dapr component: `infrastructure/dapr/components/triage-service.yaml`
  **Files**: `infrastructure/dapr/components/triage-service.yaml`
  **Verification**: App ID, port configuration
- [ ] **[5.5]** Deploy to test cluster: `kubectl apply -f infrastructure/k8s/triage-service/`
  **Verification**: Pod starts, Dapr sidecar injected, service healthy

### 5.2 Kong & Gateway Integration (Tasks 5.6-5.10) [P2] [US: 6]
- [ ] **[5.6]** Configure Kong service: `curl` commands from quickstart-milestone-2.md
  **Verification**: Service and route created in Kong
- [ ] **[5.7]** Add JWT plugin to Kong: Apply `infrastructure/kong/plugins/jwt-config.yaml`
  **Verification**: Plugin active, JWT validation working
- [ ] **[5.8]** Test Kong → Service flow: `curl` through Kong with JWT
  **Verification**: Request flows through Kong, reaches triage-service
- [ ] **[5.9]** Configure rate limiting: Add Kong rate limiting plugin
  **Verification**: 100 req/min limit enforced per student
- [ ] **[5.10]** Document Kong configuration: `docs/deployment/kong-config.md`
  **Files**: `backend/triage-service/docs/deployment/kong-config.md`
  **Verification**: All routes, plugins, and configurations documented

### 5.3 Monitoring & Observability (Tasks 5.11-5.15) [P2] [US: 7]
- [ ] **[5.11]** Add Prometheus metrics: Update `routes.py` with metrics endpoints
  **Files**: `backend/triage-service/src/api/routes.py`
  **Verification**: `/metrics` endpoint returns Prometheus format
- [ ] **[5.12]** Create health checks: Update deployment.yaml with liveness/readiness probes
  **Files**: `infrastructure/k8s/triage-service/deployment.yaml`
  **Verification**: K8s probes pass
- [ ] **[5.13]** Configure alerting rules: `infrastructure/k8s/triage-service/prometheus-rules.yaml`
  **Files**: `infrastructure/k8s/triage-service/prometheus-rules.yaml`
  **Verification**: Alerts for latency >1s, circuit breaker open, auth failures
- [ ] **[5.14]** Create monitoring dashboard: `docs/monitoring/dashboard.md`
  **Files**: `backend/triage-service/docs/monitoring/dashboard.md`
  **Verification**: Key metrics documented (from quickstart-milestone-2.md)
- [ ] **[5.15]** Add distributed tracing: Configure OpenTelemetry in `main.py`
  **Files**: `backend/triage-service/src/main.py`
  **Verification**: Traces span triage service → Dapr → agents

### 5.4 Production Readiness (Tasks 5.16-5.20) [P2] [US: 8]
- [ ] **[5.16]** Create runbooks: `docs/runbooks/`
  **Files**: `backend/triage-service/docs/runbooks/`
  **Verification**: Runbooks for common issues from quickstart-milestone-2.md
- [ ] **[5.17]** Implement feature flags: `backend/triage-service/src/config/feature_flags.py`
  **Files**: `backend/triage-service/src/config/feature_flags.py`
  **Verification**: Flags for OpenAI vs skill-only classification
- [ ] **[5.18]** Create rollback procedures: `docs/deployment/rollback.md`
  **Files**: `backend/triage-service/docs/deployment/rollback.md`
  **Verification**: Steps for quick rollback if issues
- [ ] **[5.19]** Security audit: Run `scripts/security_audit.py` against deployed service
  **Verification**: All security controls active
- [ ] **[5.20]** Final validation: Run full test suite against deployed service
  **Verification**: All integration and chaos tests pass on live deployment

### 5.5 Documentation & Handoff (Tasks 5.21-5.23) [P2] [US: 3]
- [ ] **[5.21]** Create architecture decision records: `docs/architecture/triage-service.md`
  **Files**: `backend/triage-service/docs/architecture/triage-service.md`
  **Verification**: Documents all ADR suggestions from previous phases
- [ ] **[5.22]** Update project documentation: `specs/001-learnflow-architecture/README.md`
  **Files**: `specs/001-learnflow-architecture/README.md`
  **Verification**: Includes triage service architecture, deployment guide
- [ ] **[5.23]** Create operational handoff document: `docs/operations/handoff.md`
  **Files**: `backend/triage-service/docs/operations/handoff.md`
  **Verification**: On-call procedures, escalation paths

**🎯 Phase 5 Verification**:
- **Success Criteria**: Service deployed on K8s, monitoring active, production-ready
- **Test Command**: `kubectl get pods -n learnflow -l app=triage-service` + end-to-end validation
- **ADR Suggestion**: 📋 **Deployment Architecture**: "Kubernetes microservice deployment with Dapr and Kong integration"
  **Action**: Run `/sp.adr k8s-dapr-kong-deployment` if approved

---

## Success Criteria Summary

### Milestone 2 Complete When:

**Functional Requirements**:
- [ ] Triage service responds on `/health` and `/metrics`
- [ ] `POST /api/v1/triage` endpoint works with JWT auth
- [ ] Intent classification >95% accuracy across all 4 types
- [ ] Dapr routing succeeds for all 5 target agents
- [ ] Circuit breaker triggers after 5 failures, recovers after 30s
- [ ] Audit logs published to Kafka with complete context

**Performance Requirements**:
- [ ] p95 classification latency <200ms
- [ ] p95 total triage latency <500ms
- [ ] Throughput: 1000 RPS sustained load
- [ ] Token efficiency: 90% reduction vs LLM classification
- [ ] Memory usage: <2GB baseline, <4GB under load

**Quality Requirements**:
- [ ] Test coverage >95%
- [ ] All security tests pass
- [ ] Chaos tests pass (agent failures, network issues)
- [ ] No critical vulnerabilities
- [ ] ADRs created for significant decisions

**Operational Requirements**:
- [ ] Kubernetes deployment successful
- [ ] Kong JWT integration working
- [ ] Monitoring dashboards active
- [ ] Alerting rules configured
- [ ] Runbooks documented

### Total Task Count: **67 tasks** across **5 phases**

**Phase Distribution**:
- Phase 0: 10 tasks (Skills Library)
- Phase 1: 15 tasks (Service Core)
- Phase 2: 15 tasks (Integration)
- Phase 3: 15 tasks (Security)
- Phase 4: 18 tasks (Testing & Optimization)
- Phase 5: 23 tasks (Deployment & Monitoring)

---

## Execution Instructions

### Pre-requisites Check
```bash
# Verify existing infrastructure
kubectl get pods -n learnflow | grep -E "(kafka|dapr|postgres)"
kubectl get components -n learnflow
curl http://kong-admin:8001/status
```

### Recommended Execution Order
1. **Start with Phase 0** - Skills library provides foundation
2. **Phase 1 and 2 together** - Service core + integration
3. **Phase 3 parallel** - Security can be added alongside
4. **Phase 4 after deployment** - Testing requires running service
5. **Phase 5 final** - Production deployment after validation

### Verification Between Phases
```bash
# After Phase 0: Verify skills work
python skills-library/triage-logic/intent-classifier.py

# After Phase 1: Verify service starts
python -m uvicorn src.main:app --reload

# After Phase 2: Verify Dapr integration
dapr run --app-id triage-service -- python src/main.py

# After Phase 3: Verify auth
curl -H "Authorization: Bearer $JWT" http://localhost:8000/api/v1/triage

# After Phase 4: Verify tests
pytest --cov=src --cov-report=html

# After Phase 5: Verify deployment
kubectl get pods -n learnflow -l app=triage-service
```

### ADR Decision Points
Create ADRs for:
1. **Token Efficiency**: Skill library vs LLM classification
2. **Dapr Resilience**: Circuit breaker patterns
3. **Schema Performance**: Pydantic v2 optimization
4. **Kong Auth**: Gateway-level JWT validation
5. **K8s Deployment**: Microservice architecture

Run `/sp.adr <decision-title>` for each approved decision.

---

## Next Steps

1. **Execute Phase 0** - Create triage-logic skill library
2. **Run `/sp.phr`** - Record this task generation as Prompt History Record
3. **Create ADRs** - Document significant architecture decisions
4. **Begin Implementation** - Start with task [0.1] and progress sequentially
5. **Verify Each Phase** - Run tests before moving to next phase

**Status**: ✅ **READY FOR EXECUTION**
**All artifacts referenced from existing plan, research, data model, quickstart, and contracts**

---

## File References

**Existing Artifacts Used**:
- `specs/001-learnflow-architecture/plan-milestone-2.md` - Implementation plan
- `specs/001-learnflow-architecture/research-milestone-2.md` - Research findings
- `specs/001-learnflow-architecture/data-model-milestone-2.md` - Entity definitions
- `specs/001-learnflow-architecture/quickstart-milestone-2.md` - Setup guide
- `specs/001-learnflow-architecture/contracts/openapi/triage-service.yaml` - API spec
- `.specify/agent-context/claude-context.md` - Technology stack

**Generated By**: Claude Code following Senior Engineer constraints
**Date**: 2026-01-12
**Version**: 1.0.0