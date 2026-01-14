# Milestone 3 Task Breakdown: Specialized Agent Fleet

**Feature**: Agent Fleet Architecture | **Branch**: `002-agent-fleet`
**Standard**: Elite Implementation v2.0.0 | **Constitution**: LearnFlow v2.0.0
**Verification**: `scripts/verify-agents.py` | **Total Tasks**: 89

## Dependencies & Execution Order

```
Phase 1 (Foundation) → Phase 2 (Progress Agent) → Phase 3 (Debug Agent) →
Phase 4 (Concepts Agent) → Phase 5 (Exercise Agent) → Phase 6 (Review Agent & Polish)
```

**Parallel Opportunities**:
- [P] tasks within each agent phase can run in parallel after Phase 1
- MCP script development for all agents can happen simultaneously
- Testing tasks for different agents can run in parallel

**MVP Scope**: Phase 2 (Progress Agent) - establishes Dapr patterns, state store, and Triage integration

## Implementation Strategy

**Phase 1**: Shared infrastructure and foundational components (prerequisite for all agents)
**Phases 2-6**: Agent implementations in sequence, each independently deployable
**Integration**: Each phase includes Triage Service → Agent connection via Dapr Service Invocation
**Verification**: All tasks verified by `scripts/verify-agents.py` with specific flags

---

## Phase 1: Foundation & Shared Infrastructure

**Goal**: Deploy shared infrastructure, establish contracts, and create MCP skills library

### 1.1 Infrastructure & Dapr Components

- [X] T001 Deploy Kafka cluster with agent-specific topics
      **Files**: `infrastructure/kafka/topics.yaml`
      **Verify**: `python scripts/verify-agents.py --check-kafka`

- [X] T002 Deploy Dapr pubsub component (Kafka)
      **Files**: `infrastructure/dapr/components/kafka-pubsub.yaml`
      **Verify**: `python scripts/verify-agents.py --check-dapr-components`

- [X] T003 Deploy Dapr state store component (Redis)
      **Files**: `infrastructure/dapr/components/redis-statestore.yaml`
      **Verify**: `python scripts/verify-agents.py --check-dapr-components`

- [X] T004 Deploy Dapr service invocation component
      **Files**: `infrastructure/dapr/components/service-invocation.yaml`
      **Verify**: `python scripts/verify-agents.py --check-dapr-components`

- [X] T005 Configure Dapr resiliency policies (circuit breakers, retries)
      **Files**: `infrastructure/dapr/components/resiliency.yaml`
      **Verify**: `python scripts/verify-agents.py --check-dapr-resiliency`

- [X] T006 Deploy Prometheus monitoring for all agents
      **Files**: `infrastructure/monitoring/service-monitors.yaml`
      **Verify**: `python scripts/verify-agents.py --check-prometheus`

- [X] T007 Configure Kong gateway routes for all 5 agents
      **Files**: `infrastructure/kong/routes.yaml`
      **Verify**: `python scripts/verify-agents.py --check-kong-routes`

- [X] T008 Configure Kong JWT authentication plugin
      **Files**: `infrastructure/kong/jwt-plugin.yaml`
      **Verify**: `python scripts/verify-agents.py --check-jwt-plugin`

### 1.2 Data Models & API Contracts

- [X] T009 Create Pydantic models for all agent requests/responses
      **Files**: `backend/shared/models/agent_requests.py`, `backend/shared/models/agent_responses.py`
      **Verify**: `python scripts/verify-agents.py --check-models`

- [X] T010 Create StudentProgress event model (Avro-compatible)
      **Files**: `backend/shared/models/student_progress.py`
      **Verify**: `python scripts/verify-agents.py --check-student-progress-model`

- [X] T011 Create Avro schema for StudentProgress events
      **Files**: `specs/002-agent-fleet/contracts/student-progress-v1.avsc`
      **Verify**: `python scripts/verify-agents.py --check-avro-schemas`

- [X] T012 Create Avro schema for AgentResponse events
      **Files**: `specs/002-agent-fleet/contracts/agent-response-v1.avsc`
      **Verify**: `python scripts/verify-agents.py --check-avro-schemas`

- [X] T013 Create OpenAPI contract for Progress Agent
      **Files**: `specs/002-agent-fleet/contracts/openapi-progress.yaml`
      **Verify**: `python scripts/verify-agents.py --check-openapi-contracts`

- [X] T014 Create OpenAPI contract for Debug Agent
      **Files**: `specs/002-agent-fleet/contracts/openapi-debug.yaml`
      **Verify**: `python scripts/verify-agents.py --check-openapi-contracts`

- [X] T015 Create OpenAPI contract for Concepts Agent
      **Files**: `specs/002-agent-fleet/contracts/openapi-concepts.yaml`
      **Verify**: `python scripts/verify-agents.py --check-openapi-contracts`

- [X] T016 Create OpenAPI contract for Exercise Agent
      **Files**: `specs/002-agent-fleet/contracts/openapi-exercise.yaml`
      **Verify**: `python scripts/verify-agents.py --check-openapi-contracts`

- [X] T017 Create OpenAPI contract for Review Agent
      **Files**: `specs/002-agent-fleet/contracts/openapi-review.yaml`
      **Verify**: `python scripts/verify-agents.py --check-openapi-contracts`

### 1.3 MCP Skills Library Setup

- [X] T018 Create MCP Skills directory structure for all agents
      **Files**: `skills-library/agents/progress/`, `skills-library/agents/debug/`, `skills-library/agents/concepts/`, `skills-library/agents/exercise/`, `skills-library/agents/review/`
      **Verify**: `python scripts/verify-agents.py --check-mcp-structure`

- [X] T019 [P] Create mastery calculation script (Progress Agent)
      **Files**: `skills-library/agents/progress/mastery-calculation.py`
      **Verify**: `python scripts/verify-agents.py --verify-mastery-calculation`

- [X] T020 [P] Create syntax analyzer script (Debug Agent)
      **Files**: `skills-library/agents/debug/syntax-analyzer.py`
      **Verify**: `python scripts/verify-agents.py --verify-syntax-analyzer`

- [X] T021 [P] Create error pattern detection script (Debug Agent)
      **Files**: `skills-library/agents/debug/error-pattern-detection.py`
      **Verify**: `python scripts/verify-agents.py --verify-error-patterns`

- [X] T022 [P] Create concept mapping script (Concepts Agent)
      **Files**: `skills-library/agents/concepts/concept-mapping.py`
      **Verify**: `python scripts/verify-agents.py --verify-concept-mapping`

- [X] T023 [P] Create explanation generator script (Concepts Agent)
      **Files**: `skills-library/agents/concepts/explanation-generator.py`
      **Verify**: `python scripts/verify-agents.py --verify-explanation-generator`

- [X] T024 [P] Create problem generator script (Exercise Agent)
      **Files**: `skills-library/agents/exercise/problem-generator.py`
      **Verify**: `python scripts/verify-agents.py --verify-problem-generator`

- [X] T025 [P] Create difficulty calibration script (Exercise Agent)
      **Files**: `skills-library/agents/exercise/difficulty-calibration.py`
      **Verify**: `python scripts/verify-agents.py --verify-difficulty-calibration`

- [X] T026 [P] Create code quality scoring script (Review Agent)
      **Files**: `skills-library/agents/review/code-quality-scoring.py`
      **Verify**: `python scripts/verify-agents.py --verify-quality-scoring`

- [X] T027 [P] Create hint generation script (Review Agent)
      **Files**: `skills-library/agents/review/hint-generation.py`
      **Verify**: `python scripts/verify-agents.py --verify-hint-generation`

### 1.4 Triage Service Integration Foundation

- [X] T028 Create Dapr Service Invocation configuration for agent connections
      **Files**: `infrastructure/dapr/components/triage-to-agents.yaml`
      **Verify**: `python scripts/verify-agents.py --check-service-invocation`

- [X] T029 Update Triage Service routing map with 5 agent endpoints
      **Files**: `backend/triage-service/src/config/agent-routing.json`
      **Verify**: `python scripts/verify-agents.py --check-routing-map`

- [X] T030 Create agent health check endpoints in Triage Service
      **Files**: `backend/triage-service/src/api/endpoints/agent-health.py`
      **Verify**: `python scripts/verify-agents.py --check-agent-health-endpoints`

- [X] T031 Implement circuit breaker configuration for all agent calls
      **Files**: `backend/triage-service/src/services/agent-circuit-breakers.py`
      **Verify**: `python scripts/verify-agents.py --check-circuit-breakers`

---

## Phase 2: Progress Agent Implementation [US1]

**Goal**: Deploy stateful mastery tracking agent with Dapr state store and Triage integration

### 2.1 Progress Agent Core Service

- [X] T032 [P] [US1] Create Progress Agent FastAPI application
      **Files**: `backend/progress-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-progress-main`

- [X] T033 [P] [US1] Implement mastery calculation endpoint
      **Files**: `backend/progress-agent/src/api/endpoints/mastery.py`
      **Verify**: `python scripts/verify-agents.py --check-mastery-endpoint`

- [X] T034 [P] [US1] Implement progress retrieval endpoint
      **Files**: `backend/progress-agent/src/api/endpoints/progress.py`
      **Verify**: `python scripts/verify-agents.py --check-progress-endpoint`

- [X] T035 [P] [US1] Implement historical trends endpoint
      **Files**: `backend/progress-agent/src/api/endpoints/history.py`
      **Verify**: `python scripts/verify-agents.py --check-history-endpoint`

- [X] T036 [P] [US1] Create Dapr state store service layer
      **Files**: `backend/progress-agent/src/services/state_store.py`
      **Verify**: `python scripts/verify-agents.py --check-state-store`

- [X] T037 [P] [US1] Create Kafka event consumer for progress updates
      **Files**: `backend/progress-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-kafka-consumer`

- [X] T038 [US1] Integrate MCP mastery calculation script
      **Files**: `backend/progress-agent/src/services/mastery_calculator.py`
      **Verify**: `python scripts/verify-agents.py --check-mastery-integration`

### 2.2 Progress Agent Testing & Deployment

- [X] T039 [P] [US1] Write unit tests for mastery calculation logic
      **Files**: `backend/progress-agent/tests/unit/test_mastery.py`
      **Verify**: `python scripts/verify-agents.py --test-mastery-unit`

- [X] T040 [P] [US1] Write integration tests for state store operations
      **Files**: `backend/progress-agent/tests/integration/test_state_store.py`
      **Verify**: `python scripts/verify-agents.py --test-state-integration`

- [X] T041 [P] [US1] Write end-to-end test for full progress flow
      **Files**: `backend/progress-agent/tests/e2e/test_progress_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-progress-e2e`

- [X] T042 [US1] Build Progress Agent Docker image
      **Files**: `backend/progress-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-progress`

- [X] T043 [US1] Deploy Progress Agent to Kubernetes
      **Files**: `backend/progress-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-progress`

- [X] T044 [US1] Verify Progress Agent health and connectivity
      **Files**: `backend/progress-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-progress-health`

### 2.3 Triage Service ↔ Progress Agent Integration

- [X] T045 [P] [US1] Test Dapr service invocation: Triage → Progress
      **Files**: `tests/integration/triage-to-progress-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-progress-invocation`

- [X] T046 [P] [US1] Test Kafka event publishing from Progress Agent
      **Files**: `tests/integration/progress-kafka-publish.py`
      **Verify**: `python scripts/verify-agents.py --test-progress-kafka`

- [X] T047 [US1] End-to-end flow test: Triage → Progress → Kafka → State
      **Files**: `tests/e2e/triage-progress-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-progress-flow`

---

## Phase 3: Debug Agent Implementation [US2]

**Goal**: Deploy syntax analysis and error detection agent with Triage integration

### 3.1 Debug Agent Core Service

- [X] T048 [P] [US2] Create Debug Agent FastAPI application
      **Files**: `backend/debug-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-debug-main`

- [X] T049 [P] [US2] Implement code analysis endpoint
      **Files**: `backend/debug-agent/src/api/endpoints/analyze.py`
      **Verify**: `python scripts/verify-agents.py --check-analyze-endpoint`

- [X] T050 [P] [US2] Implement error pattern detection endpoint
      **Files**: `backend/debug-agent/src/api/endpoints/patterns.py`
      **Verify**: `python scripts/verify-agents.py --check-patterns-endpoint`

- [X] T051 [P] [US2] Implement fix suggestion endpoint
      **Files**: `backend/debug-agent/src/api/endpoints/suggestions.py`
      **Verify**: `python scripts/verify-agents.py --check-suggestions-endpoint`

- [X] T052 [P] [US2] Integrate MCP syntax analyzer script
      **Files**: `backend/debug-agent/src/services/syntax_analyzer.py`
      **Verify**: `python scripts/verify-agents.py --check-syntax-integration`

- [X] T053 [P] [US2] Create error pattern matching service
      **Files**: `backend/debug-agent/src/services/pattern_matching.py`
      **Verify**: `python scripts/verify-agents.py --check-pattern-matching`

- [X] T054 [US2] Create Kafka event consumer for debug requests
      **Files**: `backend/debug-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-debug-consumer`

### 3.2 Debug Agent Testing & Deployment

- [X] T055 [P] [US2] Write unit tests for syntax analysis logic
      **Files**: `backend/debug-agent/tests/unit/test_syntax.py`
      **Verify**: `python scripts/verify-agents.py --test-syntax-unit`

- [X] T056 [P] [US2] Write integration tests for error patterns
      **Files**: `backend/debug-agent/tests/integration/test_patterns.py`
      **Verify**: `python scripts/verify-agents.py --test-patterns-integration`

- [X] T057 [P] [US2] Write end-to-end test for full debug flow
      **Files**: `backend/debug-agent/tests/e2e/test_debug_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-debug-e2e`

- [X] T058 [US2] Build Debug Agent Docker image
      **Files**: `backend/debug-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-debug`

- [X] T059 [US2] Deploy Debug Agent to Kubernetes
      **Files**: `backend/debug-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-debug`

- [X] T060 [US2] Verify Debug Agent health and connectivity
      **Files**: `backend/debug-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-debug-health`

### 3.3 Triage Service ↔ Debug Agent Integration

- [X] T061 [P] [US2] Test Dapr service invocation: Triage → Debug
      **Files**: `tests/integration/triage-to-debug-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-debug-invocation`

- [X] T062 [US2] End-to-end flow test: Triage → Debug → Analysis → Response
      **Files**: `tests/e2e/triage-debug-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-debug-flow`

---

## Phase 4: Concepts Agent Implementation [US3]

**Goal**: Deploy knowledge explanation agent with Triage integration

### 4.1 Concepts Agent Core Service

- [X] T063 [P] [US3] Create Concepts Agent FastAPI application
      **Files**: `backend/concepts-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-concepts-main`

- [X] T064 [P] [US3] Implement explanation generation endpoint
      **Files**: `backend/concepts-agent/src/api/endpoints/explain.py`
      **Verify**: `python scripts/verify-agents.py --check-explain-endpoint`

- [X] T065 [P] [US3] Implement concept mapping endpoint
      **Files**: `backend/concepts-agent/src/api/endpoints/mapping.py`
      **Verify**: `python scripts/verify-agents.py --check-mapping-endpoint`

- [X] T066 [P] [US3] Implement prerequisites endpoint
      **Files**: `backend/concepts-agent/src/api/endpoints/prerequisites.py`
      **Verify**: `python scripts/verify-agents.py --check-prerequisites-endpoint`

- [X] T067 [P] [US3] Integrate MCP explanation generator script
      **Files**: `backend/concepts-agent/src/services/explanation_generator.py`
      **Verify**: `python scripts/verify-agents.py --check-explanation-integration`

- [X] T068 [P] [US3] Create concept mapping service
      **Files**: `backend/concepts-agent/src/services/concept_mapping.py`
      **Verify**: `python scripts/verify-agents.py --check-concept-mapping`

- [X] T069 [US3] Create Kafka event consumer for concept requests
      **Files**: `backend/concepts-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-concepts-consumer`

### 4.2 Concepts Agent Testing & Deployment

- [X] T070 [P] [US3] Write unit tests for explanation generation logic
      **Files**: `backend/concepts-agent/tests/unit/test_explanations.py`
      **Verify**: `python scripts/verify-agents.py --test-explanations-unit`

- [X] T071 [P] [US3] Write integration tests for concept mapping
      **Files**: `backend/concepts-agent/tests/integration/test_mapping.py`
      **Verify**: `python scripts/verify-agents.py --test-mapping-integration`

- [X] T072 [P] [US3] Write end-to-end test for full concepts flow
      **Files**: `backend/concepts-agent/tests/e2e/test_concepts_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-concepts-e2e`

- [X] T073 [US3] Build Concepts Agent Docker image
      **Files**: `backend/concepts-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-concepts`

- [X] T074 [US3] Deploy Concepts Agent to Kubernetes
      **Files**: `backend/concepts-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-concepts`

- [X] T075 [US3] Verify Concepts Agent health and connectivity
      **Files**: `backend/concepts-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-concepts-health`

### 4.3 Triage Service ↔ Concepts Agent Integration

- [X] T076 [P] [US3] Test Dapr service invocation: Triage → Concepts
      **Files**: `backend/concepts-agent/tests/integration/test_dapr_integration.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-concepts-invocation`

- [X] T077 [US3] End-to-end flow test: Triage → Concepts → Explanation → Response
      **Files**: `backend/concepts-agent/tests/e2e/test_dapr_triage_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-concepts-flow`

---

## Phase 5: Exercise Agent Implementation [US4]

**Goal**: Deploy adaptive exercise generation agent with Triage integration

### 5.1 Exercise Agent Core Service

- [X] T078 [P] [US4] Create Exercise Agent FastAPI application
      **Files**: `backend/exercise-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-exercise-main`

- [X] T079 [P] [US4] Implement problem generation endpoint
      **Files**: `backend/exercise-agent/src/api/endpoints/generate.py`
      **Verify**: `python scripts/verify-agents.py --check-generate-endpoint`

- [X] T080 [P] [US4] Implement difficulty calibration endpoint
      **Files**: `backend/exercise-agent/src/api/endpoints/calibrate.py`
      **Verify**: `python scripts/verify-agents.py --check-calibrate-endpoint`

- [X] T081 [P] [US4] Integrate MCP problem generator script
      **Files**: `backend/exercise-agent/src/services/problem_generator.py`
      **Verify**: `python scripts/verify-agents.py --check-problem-integration`

- [X] T082 [P] [US4] Create difficulty calibration service
      **Files**: `backend/exercise-agent/src/services/difficulty_calibration.py`
      **Verify**: `python scripts/verify-agents.py --check-difficulty-calibration`

- [X] T083 [US4] Create Kafka event consumer for exercise requests
      **Files**: `backend/exercise-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-exercise-consumer`

### 5.2 Exercise Agent Testing & Deployment

- [X] T084 [P] [US4] Write unit tests for problem generation logic
      **Files**: `backend/exercise-agent/tests/unit/test_problem_generation.py`
      **Verify**: `python scripts/verify-agents.py --test-problem-generation-unit`

- [X] T085 [P] [US4] Write integration tests for difficulty calibration
      **Files**: `backend/exercise-agent/tests/integration/test_calibration.py`
      **Verify**: `python scripts/verify-agents.py --test-calibration-integration`

- [X] T086 [P] [US4] Write end-to-end test for full exercise flow
      **Files**: `backend/exercise-agent/tests/e2e/test_exercise_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-exercise-e2e`

- [X] T087 [US4] Build Exercise Agent Docker image
      **Files**: `backend/exercise-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-exercise`

- [X] T088 [US4] Deploy Exercise Agent to Kubernetes
      **Files**: `backend/exercise-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-exercise`

- [X] T089 [US4] Verify Exercise Agent health and connectivity
      **Files**: `backend/exercise-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-exercise-health`

### 5.3 Triage Service ↔ Exercise Agent Integration

- [X] T090 [P] [US4] Test Dapr service invocation: Triage → Exercise
      **Files**: `backend/exercise-agent/tests/integration/test_dapr_integration.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-exercise-invocation`

- [X] T091 [US4] End-to-end flow test: Triage → Exercise → Problem → Response
      **Files**: `backend/exercise-agent/tests/e2e/test_dapr_triage_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-exercise-flow`

---

## Phase 6: Review Agent Implementation & Production Polish [US5]

**Goal**: Deploy code quality assessment agent and complete fleet verification

### 6.1 Review Agent Core Service

- [x] T092 [P] [US5] Create Review Agent FastAPI application
      **Files**: `backend/review-agent/src/main.py`
      **Verify**: `python scripts/verify-agents.py --check-review-main`

- [x] T093 [P] [US5] Implement code assessment endpoint
      **Files**: `backend/review-agent/src/api/endpoints/assess.py`
      **Verify**: `python scripts/verify-agents.py --check-assess-endpoint`

- [x] T094 [P] [US5] Implement hint generation endpoint
      **Files**: `backend/review-agent/src/api/endpoints/hints.py`
      **Verify**: `python scripts/verify-agents.py --check-hints-endpoint`

- [x] T095 [P] [US5] Implement feedback endpoint
      **Files**: `backend/review-agent/src/api/endpoints/feedback.py`
      **Verify**: `python scripts/verify-agents.py --check-feedback-endpoint`

- [x] T096 [P] [US5] Integrate MCP code quality scoring script
      **Files**: `backend/review-agent/src/services/quality_scoring.py`
      **Verify**: `python scripts/verify-agents.py --check-quality-integration`

- [x] T097 [P] [US5] Integrate MCP hint generation script
      **Files**: `backend/review-agent/src/services/hint_generator.py`
      **Verify**: `python scripts/verify-agents.py --check-hint-integration`

- [x] T098 [US5] Create Kafka event consumer for review requests
      **Files**: `backend/review-agent/src/services/kafka_consumer.py`
      **Verify**: `python scripts/verify-agents.py --check-review-consumer`

### 6.2 Review Agent Testing & Deployment

- [x] T099 [P] [US5] Write unit tests for quality scoring logic
      **Files**: `backend/review-agent/tests/unit/test_quality.py`
      **Verify**: `python scripts/verify-agents.py --test-quality-unit`

- [x] T100 [P] [US5] Write integration tests for hint generation
      **Files**: `backend/review-agent/tests/integration/test_hints.py`
      **Verify**: `python scripts/verify-agents.py --test-hints-integration`

- [x] T101 [P] [US5] Write end-to-end test for full review flow
      **Files**: `backend/review-agent/tests/e2e/test_review_flow.py`
      **Verify**: `python scripts/verify-agents.py --test-review-e2e`

- [x] T102 [US5] Build Review Agent Docker image
      **Files**: `backend/review-agent/Dockerfile`
      **Verify**: `python scripts/verify-agents.py --build-review`

- [x] T103 [US5] Deploy Review Agent to Kubernetes
      **Files**: `backend/review-agent/k8s/`
      **Verify**: `python scripts/verify-agents.py --deploy-review`

- [x] T104 [US5] Verify Review Agent health and connectivity
      **Files**: `backend/review-agent/k8s/health-check.yaml`
      **Verify**: `python scripts/verify-agents.py --verify-review-health`

### 6.3 Triage Service ↔ Review Agent Integration

- [x] T105 [P] [US5] Test Dapr service invocation: Triage → Review
      **Files**: `tests/integration/triage-to-review-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-review-invocation`

- [x] T106 [US5] End-to-end flow test: Triage → Review → Assessment → Response
      **Files**: `tests/e2e/triage-review-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-triage-review-flow`

### 6.4 Fleet Integration & Verification

- [x] T107 [P] [US1] [US2] [US3] [US4] [US5] Run complete fleet health check
      **Files**: `tests/integration/fleet-health-check.py`
      **Verify**: `python scripts/verify-agents.py --test-fleet-health`

- [x] T108 [P] [US1] [US2] [US3] [US4] [US5] Test concurrent requests to all agents
      **Files**: `tests/integration/concurrent-fleet-test.py`
      **Verify**: `python scripts/verify-agents.py --test-concurrent`

- [x] T109 [P] [US1] [US2] [US3] [US4] [US5] Test circuit breaker behavior across fleet
      **Files**: `tests/integration/circuit-breaker-fleet.py`
      **Verify**: `python scripts/verify-agents.py --test-circuit-breakers`

- [x] T110 [US1] [US2] [US3] [US4] [US5] End-to-end flow test: Student → Triage → Agent → Response
      **Files**: `tests/e2e/full-fleet-flow.py`
      **Verify**: `python scripts/verify-agents.py --test-full-flow`

### 6.5 Security & Performance Verification

- [x] T111 [P] Test JWT validation across all agent routes
      **Files**: `tests/security/test-jwt-validation.py`
      **Verify**: `python scripts/verify-agents.py --test-jwt-validation`

- [x] T112 [P] Test rate limiting enforcement (100 req/min per student)
      **Files**: `tests/security/test-rate-limiting.py`
      **Verify**: `python scripts/verify-agents.py --test-rate-limiting`

- [x] T113 [P] Test input sanitization across all agents
      **Files**: `tests/security/test-sanitization.py`
      **Verify**: `python scripts/verify-agents.py --test-sanitization`

- [x] T114 [P] Test Dapr service invocation security (no direct communication)
      **Files**: `tests/security/test-service-invocation.py`
      **Verify**: `python scripts/verify-agents.py --test-service-security`

- [x] T115 [P] Load test: 100 concurrent users, 1000 requests
      **Files**: `tests/performance/load-test-100.py`
      **Verify**: `python scripts/verify-agents.py --test-load-100`

- [x] T116 [P] Load test: 1000 concurrent users
      **Files**: `tests/performance/load-test-1000.py`
      **Verify**: `python scripts/verify-agents.py --test-load-1000`

- [x] T117 [P] Token efficiency verification across all MCP scripts
      **Files**: `tests/performance/token-efficiency-verification.py`
      **Verify**: `python scripts/verify-agents.py --test-token-efficiency`

- [x] T118 [P] Response time verification (all agents <500ms)
      **Files**: `tests/performance/response-time-verification.py`
      **Verify**: `python scripts/verify-agents.py --test-response-times`

### 6.6 Production Readiness & Documentation

- [x] T119 [P] Create operational runbooks for all 5 agents
      **Files**: `docs/runbooks/progress-agent.md`, `docs/runbooks/debug-agent.md`, `docs/runbooks/concepts-agent.md`, `docs/runbooks/exercise-agent.md`, `docs/runbooks/review-agent.md`
      **Verify**: `python scripts/verify-agents.py --check-runbooks`

- [x] T120 [P] Create rollback procedures for fleet deployment
      **Files**: `docs/deployment/rollback-agents.md`
      **Verify**: `python scripts/verify-agents.py --check-rollback`

- [x] T121 [P] Create monitoring dashboard documentation
      **Files**: `docs/monitoring/agent-fleet-dashboard.md`
      **Verify**: `python scripts/verify-agents.py --check-monitoring-docs`

- [x] T122 [P] Create ADRs for significant decisions (Boundaries, Event-Driven, MCP Scripts)
      **Files**: `docs/architecture/adr-003-agent-boundaries.md`, `docs/architecture/adr-006-event-driven.md`, `docs/architecture/adr-007-mcp-scripts.md`
      **Verify**: `python scripts/verify-agents.py --check-adrs`

- [x] T123 [P] Update project README with fleet architecture
      **Files**: `specs/002-agent-fleet/README.md`
      **Verify**: `python scripts/verify-agents.py --check-readme`

- [x] T124 [US1] [US2] [US3] [US4] [US5] Run complete fleet verification
      **Files**: `scripts/verify-agents.py --complete-fleet`
      **Verify**: `python scripts/verify-agents.py --complete-fleet`

- [x] T125 [US1] [US2] [US3] [US4] [US5] Generate final status report
      **Files**: `reports/milestone-3-complete.md`
      **Verify**: `python scripts/verify-agents.py --generate-report`

---

## Task Verification Summary

**Total Tasks**: 125
**Foundation Phase**: 31 tasks (T001-T031)
**Progress Agent (US1)**: 16 tasks (T032-T047)
**Debug Agent (US2)**: 15 tasks (T048-T062)
**Concepts Agent (US3)**: 15 tasks (T063-T077)
**Exercise Agent (US4)**: 14 tasks (T078-T091)
**Review Agent & Polish (US5)**: 19 tasks (T092-T125)

**Parallel Opportunities**:
- 78 tasks marked [P] (parallelizable)
- MCP script development (T019-T027) can run in parallel
- Agent-specific development (Phases 2-5) can run in parallel after Phase 1
- Testing tasks for different agents can run in parallel

**Independent Test Criteria**:
- **Progress Agent**: Mastery calculation accuracy (100%), state persistence, Kafka events, Dapr state store
- **Debug Agent**: Syntax error detection (100%), pattern matching, fix suggestions, AST parsing
- **Concepts Agent**: Explanation quality, prerequisite mapping, template selection, concept relationships
- **Exercise Agent**: Problem generation, difficulty calibration, adaptability, student-level matching
- **Review Agent**: Quality scoring accuracy, hint relevance, feedback quality, code analysis

**MVP Scope**: Phase 2 (Progress Agent) - establishes Dapr patterns, state store, Triage integration, and Kafka event patterns

---

## Implementation Strategy

**Step 1**: Complete Phase 1 (31 tasks) - Shared infrastructure and foundational components
**Step 2**: Implement Phase 2 (Progress Agent) - 16 tasks, establish patterns and Dapr integration
**Step 3**: Implement Phases 3-5 in parallel (Debug, Concepts, Exercise) - 44 tasks
**Step 4**: Complete Phase 6 (Review Agent & Polish) - 34 tasks, verify fleet-wide integration

**Estimated Timeline**: 4-6 weeks with 2-3 developers
**Critical Path**: Phase 1 → Phase 2 → Phase 6
**Parallel Opportunities**: Phases 3-5 can be distributed across team members

---

## Verification Commands

All tasks require verification via `scripts/verify-agents.py`:

```bash
# Individual task verification
python scripts/verify-agents.py --check-kafka
python scripts/verify-agents.py --check-progress-main
python scripts/verify-agents.py --test-triage-progress-invocation

# Phase verification
python scripts/verify-agents.py --check-mcp-structure  # Phase 1 foundation
python scripts/verify-agents.py --verify-progress-health  # Phase 2 complete
python scripts/verify-agents.py --test-triage-review-flow  # Phase 6 complete

# Complete fleet verification
python scripts/verify-agents.py --complete-fleet

# Performance verification
python scripts/verify-agents.py --test-load-100
python scripts/verify-agents.py --test-token-efficiency
```

**All tasks must pass their verification before marking as complete.**

---

## Constitution Compliance

This task breakdown adheres to **LearnFlow v2.0.0 Constitution**:

✅ **MCP Code Execution First**: All 6 phases include MCP script development as prerequisites
✅ **Cloud-Native Architecture**: Kubernetes + Dapr + Kafka pattern throughout
✅ **Token Efficiency**: All MCP scripts target 86-94% efficiency, verified by tests
✅ **Autonomous Development**: All agents agent-generated via Skills
✅ **No Direct Communication**: Dapr service invocation only, enforced in integration tests

**All tasks include explicit verification steps using `scripts/verify-agents.py`**

---

**Generated**: 2026-01-14
**Version**: 2.0.0
**Standard**: Elite Implementation v2.0.0
**Constitution**: LearnFlow v2.0.0
**Status**: ✅ Ready for Execution