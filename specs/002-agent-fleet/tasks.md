# Milestone 3 Task Breakdown: Specialized Agent Fleet

**Feature**: Agent Fleet Architecture | **Branch**: `002-agent-fleet`
**Standard**: Elite Implementation v2.0.0 | **Constitution**: LearnFlow v2.0.0
**Verification**: `scripts/verify-agents.py` | **Total Tasks**: 78

## Dependencies & Execution Order

```
Phase 1 (Setup) → Phase 2 (Foundation) → Phase 3 (Progress Agent) →
Phase 4 (Debug Agent) → Phase 5 (Concepts Agent) →
Phase 6 (Exercise Agent) → Phase 7 (Review Agent) → Phase 8 (Polish)
```

**Parallel Opportunities**:
- [P] tasks within each phase can run in parallel
- Agent-specific components (different files) can be developed simultaneously
- Testing tasks for different agents can run in parallel

**MVP Scope**: Phase 3 (Progress Agent) - establishes patterns and Dapr state store

## Implementation Strategy

**Phase 1-2**: Shared infrastructure setup (single sequence)
**Phase 3-7**: Per-agent implementation (independent phases, can run in parallel after Phase 2)
**Phase 8**: Cross-cutting concerns and polish (final verification)

---

## Phase 1: Project Setup & Infrastructure

**Goal**: Initialize repository structure and deploy shared infrastructure components

### 1.1 Repository Structure & Configuration

- [x] T001 Create project directory structure for 5 agents
      **Files**: `backend/progress-agent/`, `backend/debug-agent/`, `backend/concepts-agent/`, `backend/exercise-agent/`, `backend/review-agent/`, each with `src/`, `k8s/`, `tests/` subdirectories
      **Verify**: `python scripts/verify-agents.py --check-structure`

- [x] T002 Create shared Python requirements for all agents
      **Files**: `backend/agent-requirements.txt` (FastAPI, Dapr SDK, Kafka Python, Pydantic v2)
      **Verify**: `python scripts/verify-agents.py --check-requirements`

- [x] T003 Initialize Dockerfiles for all 5 agents (multi-stage)
      **Files**: `backend/progress-agent/Dockerfile`, `backend/debug-agent/Dockerfile`, `backend/concepts-agent/Dockerfile`, `backend/exercise-agent/Dockerfile`, `backend/review-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --check-dockerfiles`

- [x] T004 Create base Kubernetes manifests for each agent (Dapr enabled)
      **Files**: `backend/progress-agent/k8s/deployment.yaml`, `backend/progress-agent/k8s/service.yaml` (repeat for 5 agents)
      **Verify**: `python scripts/verify-agents.py --check-k8s-base`

### 1.2 Kafka & Dapr Infrastructure

- [x] T005 Deploy Kafka cluster with agent-specific topics
      **Files**: `infrastructure/kafka/topics.yaml` (learning.events, dead-letter.queue)
      **Verify**: `python scripts/verify-agents.py --check-kafka`

- [x] T006 Deploy Dapr components (pubsub, statestore, service-invocation)
      **Files**: `infrastructure/dapr/components/kafka-pubsub.yaml`, `infrastructure/dapr/components/statestore.yaml`, `infrastructure/dapr/components/service-invocation.yaml`
      **Verify**: `python scripts/verify-agents.py --check-dapr-components`

- [x] T007 Configure Dapr resiliency policies (circuit breakers, retries)
      **Files**: `infrastructure/dapr/components/resiliency.yaml`
      **Verify**: `python scripts/verify-agents.py --check-dapr-resiliency`

- [x] T008 Verify Dapr-Kafka connectivity from baseline test pod
      **Files**: `infrastructure/tests/dapr-kafka-connection.py`
      **Verify**: `python scripts/verify-agents.py --check-dapr-kafka-connection`

### 1.3 Monitoring & Security Foundation

- [x] T009 Deploy Prometheus service monitors for all agents
      **Files**: `infrastructure/monitoring/service-monitors.yaml`
      **Verify**: `python scripts/verify-agents.py --check-prometheus`

- [x] T010 Configure Kong gateway routes for all 5 agents
      **Files**: `infrastructure/kong/routes.yaml` (5 routes: /progress, /debug, /concepts, /exercise, /review)
      **Verify**: `python scripts/verify-agents.py --check-kong-routes`

- [x] T011 Create JWT plugin configuration for Kong
      **Files**: `infrastructure/kong/jwt-plugin.yaml`
      **Verify**: `python scripts/verify-agents.py --check-jwt-plugin`

- [x] T012 Generate test JWT credentials for development
      **Files**: `infrastructure/kong/test-jwt-credentials.sh`
      **Verify**: `python scripts/verify-agents.py --check-test-credentials`

---

## Phase 2: Foundational Components & Triage Integration

**Goal**: Create shared patterns, contracts, and establish Triage Service connection

### 2.1 Data Models & Contracts

- [x] T013 Create Pydantic models for all agent requests/responses
      **Files**: `backend/shared/models/agent_requests.py`, `backend/shared/models/agent_responses.py`
      **Verify**: `python scripts/verify-agents.py --check-models`

- [x] T014 Create StudentProgress event model (Avro-compatible)
      **Files**: `backend/shared/models/student_progress.py`
      **Verify**: `python scripts/verify-agents.py --check-student-progress-model`

- [x] T015 Create Avro schema files for Kafka events
      **Files**: `specs/002-agent-fleet/contracts/student-progress-v1.avsc`, `specs/002-agent-fleet/contracts/agent-response-v1.avsc`
      **Verify**: `python scripts/verify-agents.py --check-avro-schemas`

- [x] T016 Create OpenAPI contracts for all 5 agents
      **Files**: `specs/002-agent-fleet/contracts/openapi-progress.yaml`, `openapi-debug.yaml`, `openapi-concepts.yaml`, `openapi-exercise.yaml`, `openapi-review.yaml`
      **Verify**: `python scripts/verify-agents.py --check-openapi-contracts`

### 2.2 MCP Skills Library Foundation

- [ ] T017 Create MCP Skills directory structure
      **Files**: `skills-library/agents/progress/`, `skills-library/agents/debug/`, `skills-library/agents/concepts/`, `skills-library/agents/exercise/`, `skills-library/agents/review/`
      **Verify**: `python scripts/verify-agents.py --check-mcp-structure`

- [ ] T018 Create mastery calculation script (Progress Agent)
      **Files**: `skills-library/agents/progress/mastery-calculation.py`
      **Verify**: `python scripts/verify-agents.py --verify-mastery-calculation`

- [ ] T019 Create syntax analyzer script (Debug Agent)
      **Files**: `skills-library/agents/debug/syntax-analyzer.py`
      **Verify**: `python scripts/verify-agents.py --verify-syntax-analyzer`

- [ ] T020 Create problem generator script (Exercise Agent)
      **Files**: `skills-library/agents/exercise/problem-generator.py`
      **Verify**: `python scripts/verify-agents.py --verify-problem-generator`

- [ ] T021 Create explanation generator script (Concepts Agent)
      **Files**: `skills-library/agents/concepts/explanation-generator.py`
      **Verify**: `python scripts/verify-agents.py --verify-explanation-generator`

- [ ] T022 Create code quality scoring script (Review Agent)
      **Files**: `skills-library/agents/review/code-quality-scoring.py`
      **Verify**: `python scripts/verify-agents.py --verify-quality-scoring`

- [ ] T023 Create hint generation script (Review Agent)
      **Files**: `skills-library/agents/review/hint-generation.py`
      **Verify**: `python scripts/verify-agents.py --verify-hint-generation`

### 2.3 Triage Service Integration Setup

- [ ] T024 Establish Dapr Service Invocation configuration for all agents
      **Files**: `infrastructure/dapr/components/triage-to-agents.yaml`
      **Verify**: `python scripts/verify-agents.py --check-service-invocation`

- [ ] T025 Update Triage Service routing map with 5 new agents
      **Files**: `backend/triage-service/src/config/agent-routing.json`
      **Verify**: `python scripts/verify-agents.py --check-routing-map`

- [ ] T026 Create agent health check endpoints in Triage Service
      **Files**: `backend/triage-service/src/api/endpoints/agent-health.py`
      **Verify**: `python scripts/verify-agents.py --check-agent-health-endpoints`

- [ ] T027 Implement circuit breaker configuration for agent calls
      **Files**: `backend/triage-service/src/services/agent-circuit-breakers.py`
      **Verify**: `python scripts/verify-agents.py --check-circuit-breakers`

---

## Phase 3: Progress Agent Implementation [US1]

**Goal**: Deploy stateful mastery tracking agent with Dapr state store

### 3.1 Progress Agent Core Service

- [ ] T028 [P] [US1] Create Progress Agent FastAPI application
      **Files**: `backend/progress-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-progress-main`

- [ ] T029 [P] [US1] Implement mastery calculation endpoint
      **Files**: `backend/progress-agent/src/api/endpoints/mastery.py`
      **Verify**: `python scripts/verify-agents.py --check-mastery-endpoint`

- [ ] T030 [P] [US1] Implement progress retrieval endpoint
      **Files**: `backend/progress-agent/src/api/endpoints/progress.py`
      **Verify**: `python scripts/verify-agents.py --check-progress-endpoint`

- [ ] T031 [P] [US1] Implement historical trends endpoint
      **Files**: `backend/progress-agent/src/api/endpoints/history.py`
      **Verify**: `python scripts/verify-agents.py --check-history-endpoint`

- [ ] T032 [P] [US1] Create Dapr state store service layer
      **Files**: `backend/progress-agent/src/services/state_store.py`
      **Verify**: `python scripts/verify-agents.py --check-state-store`

- [ ] T033 [P] [US1] Create Kafka event consumer for progress updates
      **Files**: `backend/progress-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-kafka-consumer`

- [ ] T034 [US1] Integrate MCP mastery calculation script
      **Files**: `backend/progress-agent/src/services/mastery_calculator.py`
      **Verify**: `python scripts/verify-agents.py --check-mastery-integration`

### 3.2 Progress Agent Testing & Deployment

- [ ] T035 [P] [US1] Write unit tests for mastery calculation logic
      **Files**: `backend/progress-agent/tests/unit/test_mastery.py`
      **Verify**: `python scripts/verify-agents.py --test-mastery-unit`

- [ ] T036 [P] [US1] Write integration tests for state store operations
      **Files**: `backend/progress-agent/tests/integration/test_state_store.py`
      **Verify**: `python scripts/verify-agents.py --test-state-integration`

- [ ] T037 [P] [US1] Write end-to-end test for full progress flow
      **Files**: `backend/progress-agent/tests/e2e/test_progress_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-progress-e2e`

- [ ] T038 [US1] Build Progress Agent Docker image
      **Files**: `backend/progress-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-progress`

- [ ] T039 [US1] Deploy Progress Agent to Kubernetes
      **Files**: `backend/progress-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-progress`

- [ ] T040 [US1] Verify Progress Agent health and connectivity
      **Files**: `backend/progress-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-progress-health`

### 3.3 Triage Service ↔ Progress Agent Integration

- [ ] T041 [P] [US1] Test Dapr service invocation: Triage → Progress
      **Files**: `tests/integration/triage-to-progress-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-progress-invocation`

- [ ] T042 [P] [US1] Test Kafka event publishing from Progress Agent
      **Files**: `tests/integration/progress-kafka-publish.py`
      **Verify**: `python scripts/verify-agents.py --test-progress-kafka`

- [ ] T043 [US1] End-to-end flow test: Triage → Progress → Kafka → State
      **Files**: `tests/e2e/triage-progress-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-progress-flow`

---

## Phase 4: Debug Agent Implementation [US2]

**Goal**: Deploy syntax analysis and error detection agent

### 4.1 Debug Agent Core Service

- [ ] T044 [P] [US2] Create Debug Agent FastAPI application
      **Files**: `backend/debug-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-debug-main`

- [ ] T045 [P] [US2] Implement code analysis endpoint
      **Files**: `backend/debug-agent/src/api/endpoints/analyze.py`
      **Verify**: `python scripts/verify-agents.py --check-analyze-endpoint`

- [ ] T046 [P] [US2] Implement error pattern detection endpoint
      **Files**: `backend/debug-agent/src/api/endpoints/patterns.py`
      **Verify**: `python scripts/verify-agents.py --check-patterns-endpoint`

- [ ] T047 [P] [US2] Implement fix suggestion endpoint
      **Files**: `backend/debug-agent/src/api/endpoints/suggestions.py`
      **Verify**: `python scripts/verify-agents.py --check-suggestions-endpoint`

- [ ] T048 [P] [US2] Integrate MCP syntax analyzer script
      **Files**: `backend/debug-agent/src/services/syntax_analyzer.py`
      **Verify**: `python scripts/verify-agents.py --check-syntax-integration`

- [ ] T049 [P] [US2] Create error pattern matching service
      **Files**: `backend/debug-agent/src/services/pattern_matching.py`
      **Verify**: `python scripts/verify-agents.py --check-pattern-matching`

- [ ] T050 [US2] Create Kafka event consumer for debug requests
      **Files**: `backend/debug-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-debug-consumer`

### 4.2 Debug Agent Testing & Deployment

- [ ] T051 [P] [US2] Write unit tests for syntax analysis logic
      **Files**: `backend/debug-agent/tests/unit/test_syntax.py`
      **Verify**: `python scripts/verify-agents.py --test-syntax-unit`

- [ ] T052 [P] [US2] Write integration tests for error patterns
      **Files**: `backend/debug-agent/tests/integration/test_patterns.py`
      **Verify**: `python scripts/verify-agents.py --test-patterns-integration`

- [ ] T053 [P] [US2] Write end-to-end test for full debug flow
      **Files**: `backend/debug-agent/tests/e2e/test_debug_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-debug-e2e`

- [ ] T054 [US2] Build Debug Agent Docker image
      **Files**: `backend/debug-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-debug`

- [ ] T055 [US2] Deploy Debug Agent to Kubernetes
      **Files**: `backend/debug-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-debug`

- [ ] T056 [US2] Verify Debug Agent health and connectivity
      **Files**: `backend/debug-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-debug-health`

### 4.3 Triage Service ↔ Debug Agent Integration

- [ ] T057 [P] [US2] Test Dapr service invocation: Triage → Debug
      **Files**: `tests/integration/triage-to-debug-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-debug-invocation`

- [ ] T058 [US2] End-to-end flow test: Triage → Debug → Analysis → Response
      **Files**: `tests/e2e/triage-debug-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-debug-flow`

---

## Phase 5: Concepts Agent Implementation [US3]

**Goal**: Deploy knowledge explanation agent

### 5.1 Concepts Agent Core Service

- [ ] T059 [P] [US3] Create Concepts Agent FastAPI application
      **Files**: `backend/concepts-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-concepts-main`

- [ ] T060 [P] [US3] Implement explanation generation endpoint
      **Files**: `backend/concepts-agent/src/api/endpoints/explain.py`
      **Verify**: `python scripts/verify-agents.py --check-explain-endpoint`

- [ ] T061 [P] [US3] Implement concept mapping endpoint
      **Files**: `backend/concepts-agent/src/api/endpoints/mapping.py`
      **Verify**: `python scripts/verify-agents.py --check-mapping-endpoint`

- [ ] T062 [P] [US3] Implement prerequisites endpoint
      **Files**: `backend/concepts-agent/src/api/endpoints/prerequisites.py`
      **Verify**: `python scripts/verify-agents.py --check-prerequisites-endpoint`

- [ ] T063 [P] [US3] Integrate MCP explanation generator script
      **Files**: `backend/concepts-agent/src/services/explanation_generator.py`
      **Verify**: `python scripts/verify-agents.py --check-explanation-integration`

- [ ] T064 [P] [US3] Create concept mapping service
      **Files**: `backend/concepts-agent/src/services/concept_mapping.py`
      **Verify**: `python scripts/verify-agents.py --check-concept-mapping`

- [ ] T065 [US3] Create Kafka event consumer for concept requests
      **Files**: `backend/concepts-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-concepts-consumer`

### 5.2 Concepts Agent Testing & Deployment

- [ ] T066 [P] [US3] Write unit tests for explanation generation logic
      **Files**: `backend/concepts-agent/tests/unit/test_explanations.py`
      **Verify**: `python scripts/verify-agents.py --test-explanations-unit`

- [ ] T067 [P] [US3] Write integration tests for concept mapping
      **Files**: `backend/concepts-agent/tests/integration/test_mapping.py`
      **Verify**: `python scripts/verify-agents.py --test-mapping-integration`

- [ ] T068 [P] [US3] Write end-to-end test for full concepts flow
      **Files**: `backend/concepts-agent/tests/e2e/test_concepts_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-concepts-e2e`

- [ ] T069 [US3] Build Concepts Agent Docker image
      **Files**: `backend/concepts-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-concepts`

- [ ] T070 [US3] Deploy Concepts Agent to Kubernetes
      **Files**: `backend/concepts-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-concepts`

- [ ] T071 [US3] Verify Concepts Agent health and connectivity
      **Files**: `backend/concepts-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-concepts-health`

### 5.3 Triage Service ↔ Concepts Agent Integration

- [ ] T072 [P] [US3] Test Dapr service invocation: Triage → Concepts
      **Files**: `tests/integration/triage-to-concepts-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-concepts-invocation`

- [ ] T073 [US3] End-to-end flow test: Triage → Concepts → Explanation → Response
      **Files**: `tests/e2e/triage-concepts-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-concepts-flow`

---

## Phase 6: Exercise Agent Implementation [US4]

**Goal**: Deploy adaptive exercise generation agent

### 6.1 Exercise Agent Core Service

- [ ] T074 [P] [US4] Create Exercise Agent FastAPI application
      **Files**: `backend/exercise-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-exercise-main`

- [ ] T075 [P] [US4] Implement problem generation endpoint
      **Files**: `backend/exercise-agent/src/api/endpoints/generate.py`
      **Verify**: `python scripts/verify-agents.py --check-generate-endpoint`

- [ ] T076 [P] [US4] Implement difficulty calibration endpoint
      **Files**: `backend/exercise-agent/src/api/endpoints/calibrate.py`
      **Verify**: `python scripts/verify-agents.py --check-calibrate-endpoint`

- [ ] T077 [P] [US4] Integrate MCP problem generator script
      **Files**: `backend/exercise-agent/src/services/problem_generator.py`
      **Verify**: `python scripts/verify-agents.py --check-problem-integration`

- [ ] T078 [P] [US4] Create difficulty calibration service
      **Files**: `backend/exercise-agent/src/services/difficulty_calibration.py`
      **Verify**: `python scripts/verify-agents.py --check-difficulty-calibration`

- [ ] T079 [US4] Create Kafka event consumer for exercise requests
      **Files**: `backend/exercise-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-exercise-consumer`

### 6.2 Exercise Agent Testing & Deployment

- [ ] T080 [P] [US4] Write unit tests for problem generation logic
      **Files**: `backend/exercise-agent/tests/unit/test_problem_generation.py`
      **Verify**: `python scripts/verify-agents.py --test-problem-generation-unit`

- [ ] T081 [P] [US4] Write integration tests for difficulty calibration
      **Files**: `backend/exercise-agent/tests/integration/test_calibration.py`
      **Verify**: `python scripts/verify-agents.py --test-calibration-integration`

- [ ] T082 [P] [US4] Write end-to-end test for full exercise flow
      **Files**: `backend/exercise-agent/tests/e2e/test_exercise_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-exercise-e2e`

- [ ] T083 [US4] Build Exercise Agent Docker image
      **Files**: `backend/exercise-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-exercise`

- [ ] T084 [US4] Deploy Exercise Agent to Kubernetes
      **Files**: `backend/exercise-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-exercise`

- [ ] T085 [US4] Verify Exercise Agent health and connectivity
      **Files**: `backend/exercise-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-exercise-health`

### 6.3 Triage Service ↔ Exercise Agent Integration

- [ ] T086 [P] [US4] Test Dapr service invocation: Triage → Exercise
      **Files**: `tests/integration/triage-to-exercise-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-exercise-invocation`

- [ ] T087 [US4] End-to-end flow test: Triage → Exercise → Problem → Response
      **Files**: `tests/e2e/triage-exercise-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-exercise-flow`

---

## Phase 7: Review Agent Implementation [US5]

**Goal**: Deploy code quality assessment agent

### 7.1 Review Agent Core Service

- [ ] T088 [P] [US5] Create Review Agent FastAPI application
      **Files**: `backend/review-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-review-main`

- [ ] T089 [P] [US5] Implement code assessment endpoint
      **Files**: `backend/review-agent/src/api/endpoints/assess.py`
      **Verify**: `python scripts/verify-agents.py --check-assess-endpoint`

- [ ] T090 [P] [US5] Implement hint generation endpoint
      **Files**: `backend/review-agent/src/api/endpoints/hints.py`
      **Verify**: `python scripts/verify-agents.py --check-hints-endpoint`

- [ ] T091 [P] [US5] Implement feedback endpoint
      **Files**: `backend/review-agent/src/api/endpoints/feedback.py`
      **Verify**: `python scripts/verify-agents.py --check-feedback-endpoint`

- [ ] T092 [P] [US5] Integrate MCP code quality scoring script
      **Files**: `backend/review-agent/src/services/quality_scoring.py`
      **Verify**: `python scripts/verify-agents.py --check-quality-integration`

- [ ] T093 [P] [US5] Integrate MCP hint generation script
      **Files**: `backend/review-agent/src/services/hint_generator.py`
      **Verify**: `python scripts/verify-agents.py --check-hint-integration`

- [ ] T094 [US5] Create Kafka event consumer for review requests
      **Files**: `backend/review-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-review-consumer`

### 7.2 Review Agent Testing & Deployment

- [ ] T095 [P] [US5] Write unit tests for quality scoring logic
      **Files**: `backend/review-agent/tests/unit/test_quality.py`
      **Verify**: `python scripts/verify-agents.py --test-quality-unit`

- [ ] T096 [P] [US5] Write integration tests for hint generation
      **Files**: `backend/review-agent/tests/integration/test_hints.py`
      **Verify**: `python scripts/verify-agents.py --test-hints-integration`

- [ ] T097 [P] [US5] Write end-to-end test for full review flow
      **Files**: `backend/review-agent/tests/e2e/test_review_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-review-e2e`

- [ ] T098 [US5] Build Review Agent Docker image
      **Files**: `backend/review-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-review`

- [ ] T099 [US5] Deploy Review Agent to Kubernetes
      **Files**: `backend/review-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-review`

- [ ] T100 [US5] Verify Review Agent health and connectivity
      **Files**: `backend/review-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-review-health`

### 7.3 Triage Service ↔ Review Agent Integration

- [ ] T101 [P] [US5] Test Dapr service invocation: Triage → Review
      **Files**: `tests/integration/triage-to-review-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-review-invocation`

- [ ] T102 [US5] End-to-end flow test: Triage → Review → Assessment → Response
      **Files**: `tests/e2e/triage-review-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-review-flow`

---

## Phase 8: Production Polish & Cross-Cutting Concerns

**Goal**: Final integration, security hardening, monitoring, and comprehensive verification

### 8.1 Comprehensive Integration Testing

- [ ] T103 [P] [US1] [US2] [US3] [US4] [US5] Run full fleet health check
      **Files**: `tests/integration/fleet-health-check.py`
      **Verify**: `python scripts/verify-agents.py --test-fleet-health`

- [ ] T104 [P] [US1] [US2] [US3] [US4] [US5] Test concurrent requests to all agents
      **Files**: `tests/integration/concurrent-fleet-test.py`
      **Verify**: `python scripts/verify-agents.py --test-concurrent`

- [ ] T105 [P] [US1] [US2] [US3] [US4] [US5] Test circuit breaker behavior across all agents
      **Files**: `tests/integration/circuit-breaker-fleet.py`
      **Verify**: `python scripts/verify-agents.py --test-circuit-breakers`

- [ ] T106 [US1] [US2] [US3] [US4] [US5] End-to-end flow test: Student → Triage → Agent → Response
      **Files**: `tests/e2e/full-fleet-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-full-flow`

### 8.2 Security & Rate Limiting

- [ ] T107 [P] Test JWT validation across all agent routes
      **Files**: `tests/security/test-jwt-validation.py`
      **Verify**: `python scripts/verify-agents.py --test-jwt-validation`

- [ ] T108 [P] Test rate limiting enforcement (100 req/min per student)
      **Files**: `tests/security/test-rate-limiting.py`
      **Verify**: `python scripts/verify-agents.py --test-rate-limiting`

- [ ] T109 [P] Test input sanitization across all agents
      **Files**: `tests/security/test-sanitization.py`
      **Verify**: `python scripts/verify-agents.py --test-sanitization`

- [ ] T110 [P] Test Dapr service invocation security (no direct communication)
      **Files**: `tests/security/test-service-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-service-security`

### 8.3 Monitoring & Observability

- [ ] T111 [P] Verify Prometheus metrics for all agents
      **Files**: `tests/monitoring/test-metrics.py`
      **Verify**: `python scripts/verify-agents.py --test-metrics`

- [ ] T112 [P] Test alerting rules for all 11 Prometheus alerts
      **Files**: `tests/monitoring/test-alerts.py`
      **Verify**: `python scripts/verify-agents.py --test-alerts`

- [ ] T113 [P] Verify Kafka event streaming for all agents
      **Files**: `tests/monitoring/test-kafka-streaming.py`
      **Verify**: `python scripts/verify-agents.py --test-kafka-streaming`

- [ ] T114 [P] Verify Dapr state store operations (Progress Agent)
      **Files**: `tests/monitoring/test-state-store.py`
      **Verify**: `python scripts/verify-agents.py --test-state-store`

### 8.4 Performance & Load Testing

- [ ] T115 [US1] [US2] [US3] [US4] [US5] Load test: 100 concurrent users, 1000 requests
      **Files**: `tests/performance/load-test-100.py`
      **Verify**: `python scripts/verify-agents.py --test-load-100`

- [ ] T116 [US1] [US2] [US3] [US4] [US5] Load test: 1000 concurrent users
      **Files**: `tests/performance/load-test-1000.py`
      **Verify**: `python scripts/verify-agents.py --test-load-1000`

- [ ] T117 [US1] [US2] [US3] [US4] [US5] Token efficiency verification across all scripts
      **Files**: `tests/performance/token-efficiency-verification.py`
      **Verify**: `python scripts/verify-agents.py --test-token-efficiency`

- [ ] T118 [US1] [US2] [US3] [US4] [US5] Response time verification (all agents <500ms)
      **Files**: `tests/performance/response-time-verification.py`
      **Verify**: `python scripts/verify-agents.py --test-response-times`

### 8.5 Production Readiness & Documentation

- [ ] T119 [P] Create operational runbooks for all 5 agents
      **Files**: `docs/runbooks/progress-agent.md`, `docs/runbooks/debug-agent.md`, `docs/runbooks/concepts-agent.md`, `docs/runbooks/exercise-agent.md`, `docs/runbooks/review-agent.md`
      **Verify**: `python scripts/verify-agents.py --check-runbooks`

- [ ] T120 [P] Create rollback procedures for fleet deployment
      **Files**: `docs/deployment/rollback-agents.md`
      **Verify**: `python scripts/verify-agents.py --check-rollback`

- [ ] T121 [P] Create monitoring dashboard documentation
      **Files**: `docs/monitoring/agent-fleet-dashboard.md`
      **Verify**: `python scripts/verify-agents.py --check-monitoring-docs`

- [ ] T122 [P] Create ADRs for significant decisions (ADR-003, ADR-006, ADR-007)
      **Files**: `docs/architecture/adr-003-agent-boundaries.md`, `docs/architecture/adr-006-event-driven.md`, `docs/architecture/adr-007-mcp-scripts.md`
      **Verify**: `python scripts/verify-agents.py --check-adrs`

- [ ] T123 [P] Update project README with fleet architecture
      **Files**: `specs/002-agent-fleet/README.md`
      **Verify**: `python scripts/verify-agents.py --check-readme`

### 8.6 Final Verification & Handoff

- [ ] T124 [US1] [US2] [US3] [US4] [US5] Run complete fleet verification
      **Files**: `scripts/verify-agents.py --complete-fleet`
      **Verify**: `python scripts/verify-agents.py --complete-fleet`

- [ ] T125 [US1] [US2] [US3] [US4] [US5] Generate final status report
      **Files**: `reports/milestone-3-complete.md`
      **Verify**: `python scripts/verify-agents.py --generate-report`

---

## Task Verification Summary

**Total Tasks**: 125
**Setup Phase**: 12 tasks (T001-T012)
**Foundation Phase**: 13 tasks (T013-T027)
**Progress Agent (US1)**: 18 tasks (T028-T045)
**Debug Agent (US2)**: 15 tasks (T046-T060)
**Concepts Agent (US3)**: 15 tasks (T061-T075)
**Exercise Agent (US4)**: 14 tasks (T076-T089)
**Review Agent (US5)**: 14 tasks (T090-T103)
**Polish Phase**: 22 tasks (T104-T125)

**Parallel Opportunities**:
- 78 tasks marked [P] (parallelizable)
- Agent-specific development (different files) can run in parallel after Phase 2
- Testing tasks for different agents can run in parallel

**Independent Test Criteria**:
- **Progress Agent**: Mastery calculation accuracy (100%), state persistence, Kafka events
- **Debug Agent**: Syntax error detection (100%), pattern matching, fix suggestions
- **Concepts Agent**: Explanation quality, prerequisite mapping, template selection
- **Exercise Agent**: Problem generation, difficulty calibration, adaptability
- **Review Agent**: Quality scoring accuracy, hint relevance, feedback quality

**MVP Scope**: Phase 3 (Progress Agent) - establishes Dapr patterns, state store, and Triage integration

---

## Implementation Strategy

**Step 1**: Complete Phase 1-2 (13 tasks) - Shared infrastructure
**Step 2**: Implement Phase 3 (Progress Agent) - 18 tasks, establish patterns
**Step 3**: Implement remaining agents in parallel (Phases 4-7, 58 tasks)
**Step 4**: Complete Phase 8 (Polish) - 22 tasks, verify everything

**Estimated Timeline**: 4-6 weeks with 2-3 developers
**Critical Path**: Phase 1-2 → Phase 3 → Phase 8
**Parallel Opportunities**: Phases 4-7 can be distributed across team members

---

## Verification Commands

All tasks require verification via `scripts/verify-agents.py`:

```bash
# Individual task verification
python scripts/verify-agents.py --check-progress-main
python scripts/verify-agents.py --test-mastery-unit
python scripts/verify-agents.py --test-triage-progress-invocation

# Phase verification
python scripts/verify-agents.py --verify-phase-1
python scripts/verify-agents.py --verify-phase-3-complete
python scripts/verify-agents.py --verify-phase-8-complete

# Complete fleet verification
python scripts/verify-agents.py --complete-fleet

# Performance verification
python scripts/verify-agents.py --test-load-100
python scripts/verify-agents.py --test-token-efficiency
```

**All tasks must pass their verification before marking as complete.**

---

**Generated**: 2026-01-13
**Version**: 1.0.0
**Standard**: Elite Implementation v2.0.0
**Constitution**: LearnFlow Agentic Development v2.0.0
**Status**: ✅ Ready for Execution