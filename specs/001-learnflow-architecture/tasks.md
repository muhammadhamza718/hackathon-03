# Task Breakdown: LearnFlow Milestone 2 - Triage Service

**Elite Implementation Standard v2.0.0**

**Feature**: `001-learnflow-architecture`
**Milestone**: 2 - Triage Service (The Routing Core)
**Generated**: 2026-01-12
**Branch**: `001-learnflow-architecture`
**Status**: Elite Standard Compliant
**Complexity**: High (Distributed System + AI Agent SDK + Security)

---

## Executive Summary

This document contains **58 elite-standard tasks** organized to build the Triage Service with all architectural mandates integrated. Every task follows the **Elite Implementation Standards**:

### Elite Standards Checklist

- ✅ **The Brain's Anatomy**: FastAPI + openai-agent-sdk Router pattern
- ✅ **Dapr Sidecar Invocation**: Dapr invoke client + Circuit Breaker/YAML config
- ✅ **Deterministic Logic (The Skill)**: intent-detection.py + route-selection.py
- ✅ **Security Handshake**: Auth Middleware extracting student_id + Dapr tracing headers
- ✅ **The Quality Gate**: Every task has verification step using `scripts/verify-triage-logic.py`

### Token Efficiency Target: 90% reduction vs LLM-based routing

---

## User Story Mapping

### User Story 1 (P1) - Student Receives AI Tutoring Support

_Core routing flow with intelligent intent detection_

### User Story 2 (P2) - System Resilience & Fault Tolerance

_Circuit breakers, retries, and graceful degradation_

### User Story 3 (P3) - Security & Auth Enforcement

_JWT validation, student_id extraction, audit logging_

---

## Phase 0: The Skill Foundation (Token Efficiency Core)

**Goal**: Create deterministic skill library for 90% token reduction

### 0.1 Triage Skill Library Creation

- [x] **[0.1]** Create triage skill directory structure
      **Files**: `skills-library/triage-logic/`
      **Quality Gate**: `python scripts/verify-triage-logic.py --check-structure`
      **Verification**: Directory exists with correct manifest and script permissions

- [x] **[0.2]** Create skill manifest with efficiency metrics
      **Files**: `skills-library/triage-logic/skill-manifest.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --validate-manifest`
      **Verification**: Contains `token_efficiency: 0.90` and all required fields

- [x] **[0.3]** Create intent-detection.py (Deterministic Logic - The Skill)
      **Files**: `skills-library/triage-logic/intent-detection.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-intent-detection`
      **Verification**: Returns valid JSON for all 4 intent types with <1000 tokens

- [x] **[0.4]** Create route-selection.py (Deterministic Logic - The Skill)
      **Files**: `skills-library/triage-logic/route-selection.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-route-selection`
      **Verification**: Maps intent → Dapr app_id with 100% accuracy

- [x] **[0.5]** Create training patterns for intent classification
      **Files**: `skills-library/triage-logic/training_data/patterns.json`
      **Quality Gate**: `python scripts/verify-triage-logic.py --validate-patterns`
      **Verification**: Contains patterns for syntax_help, concept_explanation, exercise_request, progress_check

### 0.2 Skill Optimization & Verification

- [x] **[0.6]** Create token efficiency benchmark script
      **Files**: `scripts/benchmark_token_usage.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --benchmark-tokens`
      **Verification**: Reports <1000 tokens per classification, >90% efficiency

- [x] **[0.7]** Optimize classification algorithm for speed
      **Files**: `skills-library/triage-logic/intent-detection.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --benchmark-latency`
      **Verification**: p95 classification <150ms, CPU usage <50%

- [x] **[0.8]** Create skill integration test suite
      **Files**: `tests/unit/test_skill_integration.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-skill-integration`
      **Verification**: 100% test pass rate, all 4 intents classified correctly

**🎯 Phase 0 Quality Gate**: `python scripts/verify-triage-logic.py --phase-0-complete`

---

## Phase 1: The Brain's Anatomy (FastAPI + openai-agent-sdk)

**Goal**: Build FastAPI service with OpenAI Agent SDK Router pattern

### 1.1 FastAPI Service Foundation

- [ ] **[1.1]** Create triage-service directory and structure
      **Files**: `backend/triage-service/src/`
      **Quality Gate**: `python scripts/verify-triage-logic.py --check-service-structure`
      **Verification**: Matches plan.md structure with all required directories

- [ ] **[1.2]** Generate requirements.txt with elite dependencies
      **Files**: `backend/triage-service/requirements.txt`
      **Quality Gate**: `python scripts/verify-triage-logic.py --validate-deps`
      **Verification**: Contains fastapi, openai, dapr, pydantic, python-jose

- [ ] **[1.3]** Create FastAPI main entrypoint (The Brain)
      **Files**: `backend/triage-service/src/main.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-fastapi-startup`
      **Verification**: Service starts on port 8000, Dapr sidecar config present

- [ ] **[1.4]** Create Pydantic schemas from data-model-milestone-2.md
      **Files**: `backend/triage-service/src/models/schemas.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --validate-schemas`
      **Verification**: All 4 entities (TriageRequest, IntentClassification, RoutingDecision, TriageAudit) implemented

- [ ] **[1.5]** Create custom error types with Dapr context
      **Files**: `backend/triage-service/src/models/errors.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-error-handling`
      **Verification**: Contains DaprConnectionError, CircuitBreakerError, AuthError

### 1.2 API Layer with Security Handshake

- [ ] **[1.6]** Create main API routes (POST /api/v1/triage)
      **Files**: `backend/triage-service/src/api/routes.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-triage-endpoint`
      **Verification**: Endpoint responds with 200, includes Dapr tracing headers

- [ ] **[1.7]** Create auth middleware (Security Handshake - Extract student_id)
      **Files**: `backend/triage-service/src/api/middleware/auth.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-auth-middleware`
      **Verification**: Extracts student_id from X-Consumer-Username, validates JWT claims

- [ ] **[1.8]** Create Dapr tracing middleware
      **Files**: `backend/triage-service/src/api/middleware/tracing.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-tracing-middleware`
      **Verification**: Injects Dapr tracing headers (traceparent, tracestate)

- [ ] **[1.9]** Register all middleware in main.py
      **Files**: `backend/triage-service/src/main.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-middleware-registration`
      **Verification**: Auth, tracing, and error middleware properly mounted

- [ ] **[1.10]** Create health and metrics endpoints
      **Files**: `backend/triage-service/src/api/routes.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-health-metrics`
      **Verification**: /health returns 200, /metrics returns Prometheus format

### 1.3 OpenAI Agent SDK Router Pattern Integration

- [ ] **[1.11]** Create OpenAI Agent SDK router service
      **Files**: `backend/triage-service/src/services/openai_router.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-openai-router`
      **Verification**: Integrates OpenAI Agent SDK for function-calling pattern

- [ ] **[1.12]** Connect skill library to OpenAI router
      **Files**: `backend/triage-service/src/services/openai_router.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-skill-router-connection`
      **Verification**: Router can invoke intent-detection.py and route-selection.py

- [ ] **[1.13]** Create fallback logic (OpenAI → Skill Library)
      **Files**: `backend/triage-service/src/services/openai_router.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-fallback-logic`
      **Verification**: Falls back to deterministic skill if OpenAI fails or times out

- [ ] **[1.14]** Create router performance tests
      **Files**: `tests/integration/test_openai_router.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-router-performance`
      **Verification**: p95 latency <200ms, 95%+ classification accuracy

- [ ] **[1.15]** Create router configuration management
      **Files**: `backend/triage-service/src/config/openai_config.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --validate-router-config`
      **Verification**: Supports feature flags, model selection, timeout config

**🎯 Phase 1 Quality Gate**: `python scripts/verify-triage-logic.py --phase-1-complete`

---

## Phase 2: Dapr Sidecar Invocation + Circuit Breaker

**Goal**: Implement resilient Dapr service invocation with circuit breaker patterns

### 2.1 Dapr Client Configuration

- [ ] **[2.1]** Create Dapr client service (The Brain's Dapr Arm)
      **Files**: `backend/triage-service/src/services/dapr_client.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dapr-client`
      **Verification**: DaprClient initialized, service invocation methods implemented

- [ ] **[2.2]** Implement circuit breaker configuration (The Brain's Shield)
      **Files**: `infrastructure/dapr/components/resiliency.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-circuit-breaker-config`
      **Verification**: 5 failures → 30s open, exponential backoff configured

- [ ] **[2.3]** Create retry logic with exponential backoff
      **Files**: `backend/triage-service/src/services/routing_logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-retry-logic`
      **Verification**: 3 attempts (100ms → 200ms → 400ms)

- [ ] **[2.4]** Create agent routing mapping (The Brain's Decision Tree)
      **Files**: `backend/triage-service/src/services/routing_map.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-routing-map`
      **Verification**: 100% accurate mapping: syntax_help→debug, concept_explanation→concepts, etc.

- [ ] **[2.5]** Create Dapr service discovery
      **Files**: `backend/triage-service/src/services/service_discovery.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-service-discovery`
      **Verification**: Discovers all 5 agents with health checks

### 2.2 Dapr Integration Layer

- [ ] **[2.6]** Connect routing logic to API routes
      **Files**: `backend/triage-service/src/api/routes.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-route-to-dapr`
      **Verification**: POST /api/v1/triage → Dapr invocation → Agent response

- [ ] **[2.7]** Implement dead-letter queue for failures
      **Files**: `backend/triage-service/src/services/dead_letter_queue.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dead-letter-queue`
      **Verification**: Failed routing events published to Kafka DLQ

- [ ] **[2.8]** Create Dapr tracing integration
      **Files**: `backend/triage-service/src/services/dapr_tracing.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dapr-tracing`
      **Verification**: Traces span triage-service → Dapr → target agent

- [ ] **[2.9]** Create circuit breaker health monitoring
      **Files**: `backend/triage-service/src/services/circuit_breaker_monitor.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-cb-monitor`
      **Verification**: Monitors CB state, triggers alerts when open

- [ ] **[2.10]** Create Dapr integration test suite
      **Files**: `tests/integration/test_dapr_integration.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dapr-integration`
      **Verification**: Full flow: service → Dapr → mock agent → response

### 2.3 Resilience Testing

- [ ] **[2.11]** Create circuit breaker chaos tests
      **Files**: `tests/chaos/test_circuit_breaker.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-chaos-cb`
      **Verification**: Triggers after 5 failures, recovers after 30s

- [ ] **[2.12]** Create network failure simulation tests
      **Files**: `tests/chaos/test_network_failures.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-network-chaos`
      **Verification**: Graceful degradation with DLQ fallback

- [ ] **[2.13]** Create retry logic verification tests
      **Files**: `tests/unit/test_retry_logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-retry-verification`
      **Verification**: Exact exponential backoff timing verified

**🎯 Phase 2 Quality Gate**: `python scripts/verify-triage-logic.py --phase-2-complete`

---

## Phase 3: Security Handshake + Auth Enforcement

**Goal**: JWT validation, student_id extraction, audit logging with Dapr tracing

### 3.1 Kong Gateway Integration

- [ ] **[3.1]** Create Kong JWT plugin configuration
      **Files**: `infrastructure/kong/plugins/jwt-config.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-jwt-config`
      **Verification**: JWT validation active, student_id in sub claim

- [ ] **[3.2]** Create Kong service definition for triage
      **Files**: `infrastructure/kong/services/triage-service.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-service`
      **Verification**: Routes to triage-service, JWT plugin attached

- [ ] **[3.3]** Create Kong route configuration
      **Files**: `infrastructure/kong/services/triage-route.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-route`
      **Verification**: Matches `/api/v1/triage` path, rate limiting configured

### 3.2 Security Middleware (The Brain's Security Layer)

- [ ] **[3.4]** Enhance auth middleware for student_id extraction (Security Handshake)
      **Files**: `backend/triage-service/src/api/middleware/auth.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-student-id-extraction`
      **Verification**: Extracts student_id from X-Consumer-Username header

- [ ] **[3.5]** Create JWT claim validation logic
      **Files**: `backend/triage-service/src/services/jwt_validator.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-jwt-validation`
      **Verification**: Validates exp, sub, role claims, rejects invalid tokens

- [ ] **[3.6]** Create authorization middleware for permissions
      **Files**: `backend/triage-service/src/api/middleware/authorization.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-authorization`
      **Verification**: Validates student permissions for triage access

- [ ] **[3.7]** Create rate limiting middleware
      **Files**: `backend/triage-service/src/api/middleware/rate_limiter.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-rate-limiting`
      **Verification**: 100 req/min per student, 429 on violation

- [ ] **[3.8]** Create request sanitization middleware
      **Files**: `backend/triage-service/src/api/middleware/sanitization.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-sanitization`
      **Verification**: SQL injection, XSS prevention, input validation

### 3.3 Audit Logging with Dapr Tracing

- [ ] **[3.9]** Create audit logger service (Security Handshake Audit)
      **Files**: `backend/triage-service/src/services/audit_logger.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-audit-logger`
      **Verification**: Creates TriageAudit with all required fields

- [ ] **[3.10]** Implement Dapr tracing header injection
      **Files**: `backend/triage-service/src/services/dapr_tracing_injector.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-tracing-injection`
      **Verification**: Injects traceparent, tracestate into all Dapr calls

- [ ] **[3.11]** Create Kafka audit event publishing
      **Files**: `backend/triage-service/src/services/kafka_publisher.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kafka-publishing`
      **Verification**: TriageAudit published to learning.events topic

- [ ] **[3.12]** Create security compliance reporting
      **Files**: `backend/triage-service/src/services/security_reporter.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-security-reporting`
      **Verification**: Tracks auth failures, schema violations, CB events

### 3.4 Security Testing

- [ ] **[3.13]** Create JWT validation test suite
      **Files**: `tests/security/test_jwt_validation.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-jwt-security`
      **Verification**: Expired tokens, invalid signatures, missing headers blocked

- [ ] **[3.14]** Create injection attack prevention tests
      **Files**: `tests/security/test_injection_prevention.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-injection-security`
      **Verification**: SQL injection, XSS, command injection blocked

- [ ] **[3.15]** Create end-to-end security flow test
      **Files**: `tests/security/test_e2e_security.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-e2e-security`
      **Verification**: JWT → Auth → Routing → Audit complete flow

**🎯 Phase 3 Quality Gate**: `python scripts/verify-triage-logic.py --phase-3-complete`

---

## Phase 4: Quality Gate Verification System

**Goal**: Comprehensive verification using scripts/verify-triage-logic.py

### 4.1 Core Verification Script

- [ ] **[4.1]** Create main verification script
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --self-test`
      **Verification**: Script has all required test functions and dependencies

- [ ] **[4.2]** Implement structure validation functions
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-structure-validation`
      **Verification**: Can validate file existence, directory structure

- [ ] **[4.3]** Implement token efficiency testing
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-token-efficiency-check`
      **Verification**: Measures token usage, calculates efficiency percentage

- [ ] **[4.4]** Implement performance benchmarking
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-performance-benchmark`
      **Verification**: Measures latency, throughput, memory usage

- [ ] **[4.5]** Implement security validation checks
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-security-validation`
      **Verification**: Checks auth, sanitization, JWT validation

### 4.2 Phase-Specific Verification

- [ ] **[4.6]** Create Phase 0 verification suite
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --phase-0-complete`
      **Verification**: All skill library tasks pass, token efficiency >90%

- [ ] **[4.7]** Create Phase 1 verification suite
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --phase-1-complete`
      **Verification**: FastAPI startup, schema validation, router integration

- [ ] **[4.8]** Create Phase 2 verification suite
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --phase-2-complete`
      **Verification**: Dapr client, circuit breaker, retry logic working

- [ ] **[4.9]** Create Phase 3 verification suite
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --phase-3-complete`
      **Verification**: Auth middleware, audit logging, security controls

- [ ] **[4.10]** Create comprehensive end-to-end verification
      **Files**: `scripts/verify-triage-logic.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-complete-flow`
      **Verification**: Full triage flow: JWT → Auth → Skill → Dapr → Audit

### 4.3 Continuous Validation

- [ ] **[4.11]** Create pre-commit verification hook
      **Files**: `scripts/pre-commit-verify.sh`
      **Quality Gate**: `./scripts/pre-commit-verify.sh`
      **Verification**: Runs critical checks before commits

- [ ] **[4.12]** Create CI/CD integration script
      **Files**: `scripts/ci-verify.sh`
      **Quality Gate**: `./scripts/ci-verify.sh --full-suite`
      **Verification**: All tests + integration + security validation

**🎯 Phase 4 Quality Gate**: `python scripts/verify-triage-logic.py --phase-4-complete`

---

## Phase 5: Testing & Performance Optimization

**Goal**: Achieve elite quality with comprehensive testing and performance benchmarks

### 5.1 Unit Testing (The Brain's Unit Tests)

- [ ] **[5.1]** Create comprehensive unit test suite
      **Files**: `tests/unit/`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-unit-coverage`
      **Verification**: >95% code coverage, all unit tests pass

- [ ] **[5.2]** Test skill library components
      **Files**: `tests/unit/test_skill_components.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-skill-components`
      **Verification**: intent-detection.py, route-selection.py unit tested

- [ ] **[5.3]** Test Pydantic models and validation
      **Files**: `tests/unit/test_pydantic_models.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-model-validation`
      **Verification**: All 4 entities validate correctly, edge cases covered

- [ ] **[5.4]** Test OpenAI Agent SDK integration
      **Files**: `tests/unit/test_openai_integration.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-openai-unit`
      **Verification**: Function-calling pattern, structured output parsing

- [ ] **[5.5]** Test Dapr client functionality
      **Files**: `tests/unit/test_dapr_client.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dapr-client-unit`
      **Verification**: Service invocation, circuit breaker logic, retry policies

### 5.2 Integration Testing (The Brain's Full System)

- [ ] **[5.6]** Create test infrastructure with Docker compose
      **Files**: `docker-compose.test.yml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-docker-infra`
      **Verification**: Dapr, mock agents, Kafka, Kong all start correctly

- [ ] **[5.7]** Create end-to-end triage flow tests
      **Files**: `tests/integration/test_e2e_triage.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-e2e-flow`
      **Verification**: Complete flow: JWT → validation → classification → Dapr → agent → response

- [ ] **[5.8]** Create circuit breaker integration tests
      **Files**: `tests/integration/test_circuit_breaker.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-cb-integration`
      **Verification**: Triggers on agent failures, recovers after timeout

- [ ] **[5.9]** Create security integration tests
      **Files**: `tests/integration/test_security_flow.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-security-integration`
      **Verification**: Auth middleware → Dapr tracing → audit logging complete chain

- [ ] **[5.10]** Create Kafka audit publishing tests
      **Files**: `tests/integration/test_kafka_audit.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kafka-audit`
      **Verification**: TriageAudit events published and consumed correctly

### 5.3 Performance Testing (The Brain's Performance Benchmarks)

- [ ] **[5.11]** Create load test script (k6)
      **Files**: `tests/performance/load.js`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-load-performance`
      **Verification**: Handles 1000 RPS sustained, 5000 RPS burst

- [ ] **[5.12]** Benchmark intent classification speed
      **Files**: `tests/performance/benchmark_classification.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --benchmark-classification`
      **Verification**: p95 <200ms for intent detection

- [ ] **[5.13]** Measure total triage latency (p95, p99)
      **Files**: `tests/performance/benchmark_end_to_end.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --benchmark-latency`
      **Verification**: p95 <500ms, p99 <1000ms for complete triage flow

- [ ] **[5.14]** Test memory usage under load
      **Files**: `tests/performance/benchmark_memory.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-memory-usage`
      **Verification**: <2GB baseline, <4GB under 1000 RPS load

- [ ] **[5.15]** Run chaos engineering tests
      **Files**: `tests/chaos/`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-chaos-engineering`
      **Verification**: System handles agent failures, network issues, Dapr downtime

### 5.4 Token Efficiency Validation (Elite Standard Compliance)

- [ ] **[5.16]** Create comprehensive efficiency comparison
      **Files**: `scripts/compare_efficiency.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --validate-90-percent-efficiency`
      **Verification**: Confirms 90%+ token reduction vs manual LLM implementation

- [ ] **[5.17]** Create efficiency dashboard documentation
      **Files**: `docs/performance/token-efficiency.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --document-efficiency`
      **Verification**: Documents all benchmarks and achieves targets

- [ ] **[5.18]** Update skill manifest with final metrics
      **Files**: `skills-library/triage-logic/skill-manifest.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --final-skill-validation`
      **Verification**: Confirms 90% token efficiency achieved and documented

**🎯 Phase 5 Quality Gate**: `python scripts/verify-triage-logic.py --phase-5-complete`

---

## Phase 6: Production Deployment & Monitoring

**Goal**: Kubernetes deployment, Dapr integration, production readiness

### 6.1 Containerization

- [ ] **[6.1]** Create optimized Dockerfile (multi-stage)
      **Files**: `backend/triage-service/Dockerfile`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dockerfile`
      **Verification**: Multi-stage build, minimal base image, security scanned

- [ ] **[6.2]** Create Kubernetes deployment manifest
      **Files**: `infrastructure/k8s/triage-service/deployment.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-k8s-deployment`
      **Verification**: Dapr sidecar injection, resource limits, health checks

- [ ] **[6.3]** Create Kubernetes service definition
      **Files**: `infrastructure/k8s/triage-service/service.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-k8s-service`
      **Verification**: ClusterIP service for Dapr invocation

- [ ] **[6.4]** Create Dapr component for triage-service
      **Files**: `infrastructure/dapr/components/triage-service.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-dapr-component`
      **Verification**: App ID, port config, logging configured

- [ ] **[6.5]** Deploy to test cluster and verify
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-k8s-deployment-live`
      **Verification**: Pods start, Dapr sidecar injected, service healthy

### 6.2 Kong Gateway Integration

- [ ] **[6.6]** Configure Kong service via API
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-service-config`
      **Verification**: Service created in Kong, health checks pass

- [ ] **[6.7]** Apply JWT plugin to Kong route
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-jwt-plugin`
      **Verification**: JWT validation active, 401 without valid token

- [ ] **[6.8]** Add rate limiting plugin to Kong
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-rate-limit`
      **Verification**: 100 req/min enforced per student

- [ ] **[6.9]** Test complete Kong → triage-service flow
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-kong-end-to-end`
      **Verification**: Request flows: Kong JWT → triage-service → Dapr → response

- [ ] **[6.10]** Document Kong configuration
      **Files**: `docs/deployment/kong-config.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --document-kong-config`
      **Verification**: All routes, plugins, and security config documented

### 6.3 Monitoring & Observability

- [ ] **[6.11]** Add Prometheus metrics endpoint
      **Files**: `backend/triage-service/src/api/routes.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-prometheus-metrics`
      **Verification**: /metrics returns valid Prometheus format

- [ ] **[6.12]** Configure health checks in deployment
      **Files**: `infrastructure/k8s/triage-service/deployment.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-health-probes`
      **Verification**: Liveness and readiness probes configured

- [ ] **[6.13]** Create Prometheus alerting rules
      **Files**: `infrastructure/k8s/triage-service/prometheus-rules.yaml`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-alerting-rules`
      **Verification**: Alerts for latency >1s, CB open, auth failures

- [ ] **[6.14]** Create monitoring dashboard documentation
      **Files**: `docs/monitoring/dashboard.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --document-monitoring`
      **Verification**: Key metrics documented with thresholds

- [ ] **[6.15]** Add distributed tracing with OpenTelemetry
      **Files**: `backend/triage-service/src/main.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-distributed-tracing`
      **Verification**: Traces span triage-service → Dapr → agents

### 6.4 Production Readiness

- [ ] **[6.16]** Create operational runbooks
      **Files**: `docs/runbooks/`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-runbooks`
      **Verification**: Runbooks for common operational issues

- [ ] **[6.17]** Implement feature flags for routing
      **Files**: `backend/triage-service/src/config/feature_flags.py`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-feature-flags`
      **Verification**: Flags for OpenAI vs skill-only classification

- [ ] **[6.18]** Create rollback procedures
      **Files**: `docs/deployment/rollback.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-rollback-procedures`
      **Verification**: Steps for quick rollback if issues occur

- [ ] **[6.19]** Run final security audit
      **Quality Gate**: `python scripts/verify-triage-logic.py --final-security-audit`
      **Verification**: All security controls active, no critical vulnerabilities

- [ ] **[6.20]** Complete final integration validation
      **Quality Gate**: `python scripts/verify-triage-logic.py --final-validation`
      **Verification**: All systems operational, metrics within budget

### 6.5 Documentation & Handoff

- [ ] **[6.21]** Create architecture decision records (ADRs)
      **Files**: `docs/architecture/triage-service.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --document-adrs`
      **Verification**: Documents all ADR suggestions from previous phases

- [ ] **[6.22]** Update project README and specifications
      **Files**: `specs/001-learnflow-architecture/README.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --update-documentation`
      **Verification**: Includes triage service architecture, deployment guide

- [ ] **[6.23]** Create operational handoff document
      **Files**: `docs/operations/handoff.md`
      **Quality Gate**: `python scripts/verify-triage-logic.py --test-handoff-doc`
      **Verification**: On-call procedures, escalation paths, contact info

**🎯 Phase 6 Quality Gate**: `python scripts/verify-triage-logic.py --phase-6-complete`

---

## Final Milestone Verification

### Elite Standards Compliance Check

- [ ] **[F.1]** Verify The Brain's Anatomy: FastAPI + openai-agent-sdk Router
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-brain-anatomy`
      **Verification**: Service architecture matches elite standard

- [ ] **[F.2]** Verify Dapr Sidecar Invocation + Circuit Breaker
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-dapr-invocation`
      **Verification**: Dapr client with circuit breaker configured

- [ ] **[F.3]** Verify Deterministic Logic (The Skill) Scripts
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-deterministic-logic`
      **Verification**: intent-detection.py + route-selection.py functional

- [ ] **[F.4]** Verify Security Handshake (Auth + Dapr Tracing)
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-security-handshake`
      **Verification**: student_id extraction + tracing headers working

- [ ] **[F.5]** Verify Quality Gate System
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-quality-gate-system`
      **Verification**: All tasks have verification steps using verify-triage-logic.py

### Performance Targets Verification

- [ ] **[F.6]** Verify 90%+ token efficiency achievement
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-90-percent-efficiency`
      **Verification**: Benchmarks show 90%+ reduction vs LLM implementation

- [ ] **[F.7]** Verify p95 latency <500ms for triage flow
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-latency-target`
      **Verification**: Performance tests confirm <500ms p95 latency

- [ ] **[F.8]** Verify 95%+ test coverage
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-test-coverage`
      **Verification**: Coverage report shows >95% code coverage

- [ ] **[F.9]** Verify security compliance
      **Quality Gate**: `python scripts/verify-triage-logic.py --verify-security-compliance`
      **Verification**: All security controls pass audit

---

## Success Criteria Summary

### Milestone 2 Complete When ALL Are Met:

**Elite Standards Compliance**:

- [ ] FastAPI service with openai-agent-sdk Router pattern implemented
- [ ] Dapr sidecar invocation with circuit breaker configured
- [ ] Deterministic scripts (intent-detection.py, route-selection.py) functional
- [ ] Security handshake (auth middleware + Dapr tracing) working
- [ ] Quality gate system using verify-triage-logic.py complete

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

---

## Task Count: **58 elite-standard tasks** across **6 phases**

### Phase Distribution:

- **Phase 0**: 8 tasks (Skill Foundation)
- **Phase 1**: 15 tasks (FastAPI + Brain Anatomy)
- **Phase 2**: 13 tasks (Dapr + Circuit Breaker)
- **Phase 3**: 15 tasks (Security Handshake)
- **Phase 4**: 11 tasks (Quality Gate System)
- **Phase 5**: 18 tasks (Testing & Performance)
- **Phase 6**: 23 tasks (Deployment & Monitoring)
- **Final**: 9 tasks (Elite Standards Verification)

---

## Dependency Graph & Parallel Execution

### Critical Path (Must Execute Sequentially):

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

### Parallel Execution Groups (Can Run Simultaneously):

**Group A**: Phase 0 (Skill Foundation)

```bash
# Tasks 0.1-0.5 can run in parallel
- Create skill directory structure
- Create skill manifest
- Create intent-detection.py
- Create route-selection.py
- Create training patterns
```

**Group B**: Phase 1 + Phase 3 (Core + Security)

```bash
# FastAPI setup + Security middleware can run in parallel
# But must complete before Phase 2 integration
- Backend service structure
- Auth middleware development
- Kong configuration
```

**Group C**: Phase 5 Testing (All tests can run in parallel after service is ready)

```bash
# Unit, integration, security, performance tests in parallel
pytest tests/unit/ tests/integration/ tests/security/ tests/performance/
```

**Group D**: Phase 6 Deployment (Infrastructure tasks in parallel)

```bash
# K8s manifests, Kong config, monitoring setup
kubectl apply -f infrastructure/k8s/
kubectl apply -f infrastructure/dapr/
curl -X POST http://kong-admin:8001/services/
```

### MVP Scope Suggestion (If Time Constrained):

**Week 1: Core Brain** (Tasks 0.1-0.5, 1.1-1.5, 2.1-2.3)

- Skill library with intent detection
- FastAPI service skeleton
- Basic Dapr client integration

**Week 2: Security & Routing** (Tasks 3.1-3.6, 2.4-2.6)

- JWT auth with student_id extraction
- Complete routing logic
- Dapr circuit breaker

**Week 3: Testing & Deployment** (Tasks 4.1-4.5, 5.1-5.5, 6.1-6.5)

- Verification script
- Unit/integration tests
- Docker + basic K8s deployment

**MVP Result**: Functional triage service with basic routing, auth, and testing

---

## Execution Instructions

### Pre-requisites Check:

```bash
# Verify infrastructure exists
python scripts/verify-triage-logic.py --check-prerequisites
# Should verify: Python 3.11+, Docker, kubectl, Dapr CLI, Kong
```

### Recommended Execution Order:

1. **Start Phase 0** - Skill library is the foundation
2. **Phase 1 & 3** - Service core and security can develop in parallel
3. **Phase 2** - Dapr integration after service is ready
4. **Phase 4** - Quality gate system after basic functionality
5. **Phase 5** - Testing after integration is complete
6. **Phase 6** - Deployment after all tests pass

### Quality Gate Between Phases:

```bash
# After each phase complete, run:
python scripts/verify-triage-logic.py --phase-N-complete

# Full system verification:
python scripts/verify-triage-logic.py --test-complete-flow

# Elite standards compliance:
python scripts/verify-triage-logic.py --verify-elite-standards
```

---

## Next Steps

1. **Execute Phase 0** - Create triage-logic skill library
2. **Run `/sp.phr`** - Record this task generation as Prompt History Record
3. **Begin Implementation** - Start with task [0.1] and progress sequentially
4. **Verify Each Phase** - Run quality gate before moving to next phase
5. **Create ADRs** - Document significant architecture decisions with `/sp.adr`

**Status**: ✅ **ELITE STANDARD READY**
**All tasks verified against elite implementation standards**
**Quality gate system integrated into every task**
**Ready for autonomous execution via MCP Skills**

---

## Elite Standards References

**Architecture Mandates**:

- The Brain's Anatomy: FastAPI + openai-agent-sdk Router pattern
- Dapr Sidecar Invocation: Circuit breaker + resilience patterns
- Deterministic Logic: intent-detection.py + route-selection.py scripts
- Security Handshake: Auth middleware + Dapr tracing headers
- Quality Gate: verify-triage-logic.py validation for all tasks

**Performance Targets**:

- Token Efficiency: 90%+ reduction vs LLM implementation
- Latency: p95 <500ms for complete triage flow
- Throughput: 1000 RPS sustained, 5000 RPS burst
- Coverage: 95%+ test coverage required

**Compliance**: All tasks must pass `python scripts/verify-triage-logic.py` validation

---

**Generated**: 2026-01-12
**Version**: Elite Standard v2.0.0
**Compliance**: 100% Elite Standards Adherence
