# Mastery Engine Implementation Tasks
**Feature**: Mastery Engine | **Version**: 1.0.0 | **Date**: 2026-01-14
**Branch**: `003-mastery-engine` | **Spec**: `specs/003-mastery-engine/spec.md`

## Executive Summary
This task list provides 65 granular, independently testable tasks for implementing the Mastery Engine microservice. All tasks follow the Elite Implementation Standard v2.0.0 and are organized by user stories for independent implementation and testing.

**Total Tasks**: 65
**User Stories**: 10
**Estimated Timeline**: 10 weeks
**MVP Scope**: User Stories 1, 2, 8, 9 (Core functionality)

---

## Dependencies

### User Story Completion Order
```
Phase 2: Foundational → Must complete before all user stories
├── US1: Real-Time Mastery Calculation
├── US2: Event-Driven Learning Progress
├── US8: Security and Compliance
└── US9: Health Monitoring

Phase 3: Advanced Features (independent)
├── US3: Predictive Analytics (requires US1)
├── US4: Adaptive Recommendations (requires US1)
└── US10: Dapr Integration (requires US2)

Phase 4: Analytics (independent)
├── US5: Batch Processing
├── US6: Historical Analysis
└── US7: Cohort Comparison
```

### Parallel Execution Opportunities
- **US5 + US6 + US7**: All analytics features can be implemented in parallel
- **US3 + US4**: Both prediction features can run in parallel
- **US1 + US2**: Can start in parallel, but US2 depends on US1's data models
- **US8 + US9**: Security and monitoring are independent

---

## Phase 1: Setup

### Task List
- [X] T001 Initialize Python project structure in `backend/mastery-engine/`
- [X] T002 Create virtual environment and install core dependencies from plan
- [X] T003 Set up Git repository with `.gitignore` patterns
- [X] T004 Create basic project structure per plan.md specification
- [X] T005 Initialize Dapr configuration files for local development
- [X] T006 Set up Kafka docker-compose for local testing
- [X] T007 Create Redis docker configuration for state store
- [X] T008 Write initial README.md with project overview and quickstart

**Independent Test Criteria**:
- Project structure matches plan.md exactly
- All basic files exist with correct extensions
- Dapr, Kafka, Redis configurations are valid

---

## Phase 2: Foundational (Must Complete Before User Stories)

These tasks provide the infrastructure required for all user stories.

### Task List
- [X] T010 [P] Create `requirements.txt` with all dependencies from plan.md
- [X] T011 [P] Write `pytest.ini` with coverage targets and async configuration
- [X] T012 [P] Create `backend/mastery-engine/src/__init__.py` package files
- [X] T013 [P] Create `backend/mastery-engine/tests/__init__.py` package files
- [X] T014 [P] Set up `backend/mastery-engine/src/models/__init__.py` with exports
- [X] T015 [P] Set up `backend/mastery-engine/src/services/__init__.py` with exports
- [X] T016 [P] Set up `backend/mastery-engine/src/api/__init__.py` with exports
- [X] T017 [P] Set up `backend/mastery-engine/src/skills/__init__.py` with exports
- [X] T018 [P] Set up `backend/mastery-engine/src/api/endpoints/__init__.py` with exports
- [X] T019 Create `backend/mastery-engine/Dockerfile` with multi-stage build
- [X] T020 Create `backend/mastery-engine/.dockerignore` patterns
- [X] T021 Create `backend/mastery-engine/k8s/deployment.yaml` with Dapr sidecar
- [X] T022 Create `backend/mastery-engine/k8s/service.yaml` ClusterIP service
- [X] T023 Create `backend/mastery-engine/k8s/configmap.yaml` for environment variables
- [X] T024 Write `backend/mastery-engine/pytest.ini` with coverage configuration
- [X] T025 Create `backend/mastery-engine/docs/runbooks.md` template
- [X] T026 Create `backend/mastery-engine/docs/architecture-decisions.md` template
- [X] T027 Create `backend/mastery-engine/docs/data-flow-diagrams.md` with ASCII diagrams

**Independent Test Criteria**:
- All files exist and are syntactically valid
- Docker build completes successfully
- Python imports work without errors
- Kubernetes manifests are valid YAML

---

## Phase 3: User Story 1 - Real-Time Mastery Calculation [US1]

**Goal**: API endpoint to query current mastery with breakdown

### Task List
- [X] T030 [P] [US1] Create `backend/mastery-engine/src/models/mastery.py` - Core mastery models (Pydantic)
- [X] T031 [P] [US1] Create `backend/mastery-engine/src/services/state_manager.py` - Dapr state operations
- [X] T032 [P] [US1] Create `backend/mastery-engine/src/skills/calculator.py` - MCP mastery calculation
- [X] T033 [P] [US1] Create `backend/mastery-engine/src/api/endpoints/mastery.py` - Query endpoints
- [X] T034 [US1] Implement `POST /mastery/query` endpoint in mastery.py
- [X] T035 [US1] Implement `POST /mastery/calculate` endpoint in mastery.py
- [X] T036 [US1] Write unit tests `tests/unit/test_mastery_calculation.py`
- [X] T037 [US1] Write integration tests `tests/integration/test_mastery_api.py`
- [X] T038 [US1] Write contract tests `tests/contract/test_mastery_api_contracts.py`
- [X] T039 [US1] Implement JWT validation middleware for all mastery endpoints
- [X] T040 [US1] Add rate limiting (50 req/min) to mastery endpoints
- [X] T041 [US1] Implement input sanitization and structured logging
- [X] T042 [US1] Test Dapr integration health check (`test_basic.py`)
- [X] T043 [US1] Verify error handling and HTTP status codes (`test_error_handling.py`)

**Independent Test Criteria**:
- `POST /mastery/query` returns valid mastery data for sample student_id
- Calculation result matches formula: (completion×0.4 + quiz×0.3 + quality×0.2 + consistency×0.1)
- JWT validation rejects invalid tokens
- Rate limiting returns 429 after threshold
- Response time <100ms for queries

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_mastery_calculator.py`
- `backend/mastery-engine/tests/unit/test_state_manager.py`
- `backend/mastery-engine/tests/integration/test_api_endpoints.py`
- `backend/mastery-engine/tests/test_basic.py`

---

## Phase 4: User Story 2 - Event-Driven Learning Progress [US2]

**Goal**: Kafka consumer processing events and updating mastery in real-time

### Task List
- [X] T050 [P] [US2] Create `backend/mastery-engine/src/models/events.py` - Event schemas (Pydantic)
- [X] T051 [P] [US2] Create `backend/mastery-engine/src/services/kafka_consumer.py` - Event processor
- [X] T052 [US2] Implement Kafka consumer with idempotency logic in state manager
- [X] T053 [US2] Add event validation service (`src/services/event_validator.py`)
- [X] T054 [US2] Implement dead-letter queue handling (mastery.dlq topic)
- [X] T055 [US2] Add event processing checkpointing to prevent duplicates
- [X] T056 [US2] Write unit tests for event validation (`test_event_processing.py`)
- [X] T057 [US2] Write integration tests for event processing (`test_event_processing.py`)
- [X] T058 [US2] Implement event -> state update logic for all event types
- [X] T059 [US2] Add monitoring metrics for event processing throughput
- [X] T060 [US2] Create Kafka topic configuration scripts (`scripts/setup_kafka_topics.sh`)
- [X] T061 [US2] Write basic verification test for event processing
- [X] T062 [US2] Add error handling and retry logic for transient failures

**Independent Test Criteria**:
- Kafka consumer successfully processes completion events
- Idempotency prevents duplicate processing of same event_id
- Failed events are moved to DLQ topic
- State store is updated correctly for each event type
- Event processing latency <500ms

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_kafka_consumer.py`
- `backend/mastery-engine/tests/integration/test_kafka_integration.py`
- `backend/mastery-engine/tests/test_basic.py` (add US2 tests)

---

## Phase 5: User Story 8 - Security and Compliance [US8]

**Goal**: Complete security implementation and GDPR compliance

### Task List
- [x] T070 [P] [US8] Create `backend/mastery-engine/src/security.py` - JWT validation, RBAC
- [x] T071 [US8] Implement security context model and middleware
- [x] T072 [US8] Add role-based access control (student/teacher/admin)
- [x] T073 [US8] Implement audit logging for all data access
- [x] T074 [US8] Add 90-day TTL configuration to all state keys
- [x] T075 [US8] Create GDPR deletion endpoint (`DELETE /student/{student_id}`)
- [x] T076 [US8] Implement data export endpoint (`GET /student/{student_id}/export`)
- [x] T077 [US8] Add comprehensive input sanitization (SQLi, XSS, command injection)
- [x] T078 [US8] Write security unit tests (`tests/unit/test_security.py`)
- [x] T079 [US8] Write security integration tests (`tests/integration/test_dapr_integration.py`)
- [x] T080 [US8] Implement consent tracking in student profiles
- [x] T081 [US8] Add TLS configuration (`tls_config.py`) for production deployments

**Independent Test Criteria**:
- JWT validation works for all endpoints
- Student cannot access other student's data
- GDPR deletion removes all student data within 24 hours
- Audit logs capture all data access
- Input sanitization blocks malicious payloads

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_security.py`
- `backend/mastery-engine/tests/integration/test_dapr_integration.py`

---

## Phase 6: User Story 9 - Health Monitoring [US9]

**Goal**: Health checks and observability endpoints

### Task List
- [x] T090 [P] [US9] Add `GET /health` endpoint (lightweight status)
- [x] T091 [P] [US9] Add `GET /ready` endpoint (full dependency check)
- [x] T092 [P] [US9] Add `GET /metrics` endpoint (Prometheus format)
- [x] T093 [P] [US9] Add `GET /` endpoint (service info and version)
- [x] T094 [US9] Implement dependency health checks (Redis, Kafka, Dapr)
- [x] T095 [US9] Add structured JSON logging throughout application
- [x] T096 [US9] Create health check unit tests (`tests/unit/test_health_endpoints.py`)
- [x] T097 [US9] Create health check integration tests (`tests/integration/test_health_integration.py`)
- [x] T098 [US9] Add performance metrics collection (latency, throughput, errors)
- [x] T099 [US9] Implement health check monitoring in main.py lifespan

**Independent Test Criteria**:
- `/health` returns 200 with minimal response
- `/ready` returns 503 if any dependency is down
- `/metrics` returns Prometheus-compatible format
- All endpoints include proper headers and CORS
- Logging is structured JSON with correlation IDs

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_health_endpoints.py`
- `backend/mastery-engine/tests/integration/test_health_integration.py`

### Phase 5 & 6 Completion Summary

**Status**: ✅ **COMPLETE**

**Total Tasks Completed**: 22 tasks

**Phase 5 (Security & Compliance)**: 12/12 tasks ✅
- JWT validation & RBAC with 3-tier permissions
- GDPR Article 17 & 20 compliance endpoints
- Comprehensive audit logging with correlation IDs
- Input sanitization against injection attacks
- Full security test coverage (unit + integration)
- Production TLS configuration

**Phase 6 (Health Monitoring)**: 10/10 tasks ✅
- 4 health endpoints with proper status codes
- Real-time dependency verification
- Structured JSON logging with production format
- Performance metrics (latency, throughput, errors)
- Complete test coverage for monitoring
- Security headers middleware

**Quality Metrics**:
- **Test Coverage**: 2 new test files with 50+ test cases
- **Security**: Role-based access, GDPR compliance, input validation
- **Observability**: JSON logs, metrics, health checks
- **Production Ready**: TLS, CORS, security headers, rate limiting

---

## Phase 7: User Story 3 - Predictive Analytics [US3]

**Goal**: Predict mastery trajectory and intervention needs

### Task List
- [ ] T100 [P] [US3] Create `backend/mastery-engine/src/services/predictor.py` - Prediction logic
- [ ] T101 [US3] Implement linear regression for 7-day mastery prediction
- [ ] T102 [US3] Add confidence scoring based on data volume
- [ ] T103 [US3] Implement intervention flagging algorithm
- [ ] T104 [US3] Add Redis caching with 1-hour TTL for predictions
- [ ] T105 [US3] Create `POST /predictions/next-week` endpoint
- [ ] T106 [US3] Create `POST /predictions/trajectory` endpoint
- [ ] T107 [US3] Write unit tests for predictor.py
- [ ] T108 [US3] Write integration tests for prediction endpoints
- [ ] T109 [US3] Add prediction accuracy tracking (for monitoring)
- [ ] T110 [US3] Handle edge cases (insufficient history, stale data)

**Independent Test Criteria**:
- Prediction returns within 200ms for cached results
- Confidence score increases with more historical data
- Intervention flag triggers for scores < 0.5
- Predictions are reasonably accurate (within 10% variance)

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_predictor.py`
- `backend/mastery-engine/tests/integration/test_prediction_endpoints.py`

---

## Phase 8: User Story 4 - Adaptive Recommendations [US4]

**Goal**: Generate personalized learning recommendations

### Task List
- [ ] T120 [P] [US4] Create `backend/mastery-engine/src/services/recommendation_engine.py`
- [ ] T121 [US4] Implement component threshold analysis (score < 0.7)
- [ ] T122 [US4] Create priority assignment logic (high/medium/low)
- [ ] T123 [US4] Implement action type mapping (practice/review/refactor/schedule)
- [ ] T124 [US4] Add area-specific recommendations for weak components
- [ ] T125 [US4] Create `POST /recommendations/adaptive` endpoint
- [ ] T126 [US4] Create `POST /recommendations/learning-path` endpoint
- [ ] T127 [US4] Write unit tests for recommendation logic
- [ ] T128 [US4] Write integration tests for recommendation endpoints
- [ ] T129 [US4] Implement MCP skill for recommendation generation
- [ ] T130 [US4] Add estimated time allocation per recommendation

**Independent Test Criteria**:
- Recommendations generated for all components with score < 0.7
- Priority correctly assigned based on impact
- Response includes action, area, and estimated time
- Learning path includes logical sequence of recommendations

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_recommendation_engine.py`
- `backend/mastery-engine/tests/integration/test_recommendation_endpoints.py`

---

## Phase 9: User Stories 5, 6, 7 - Analytics Features [US5, US6, US7]

**Goal**: Batch processing and historical analytics

### Task List
- [ ] T140 [P] [US5] Create `POST /batch/mastery` endpoint for batch calculations
- [ ] T141 [US5] Implement batch validation and error aggregation
- [ ] T142 [US5] Add priority queuing (low/normal/high) for batch jobs
- [ ] T143 [US5] Implement async batch processing with batch_id tracking
- [ ] T144 [US5] Write unit tests for batch endpoint
- [ ] T145 [US5] Write integration tests for batch processing

- [ ] T150 [P] [US6] Create `POST /analytics/mastery-history` endpoint
- [ ] T151 [US6] Implement date range validation and querying
- [ ] T152 [US6] Add aggregation logic (daily/weekly/monthly)
- [ ] T153 [US6] Implement summary statistics calculation
- [ ] T154 [US6] Write unit tests for analytics logic
- [ ] T155 [US6] Write integration tests for analytics endpoints

- [ ] T160 [P] [US7] Create `POST /analytics/compare` endpoint
- [ ] T161 [US7] Implement cohort aggregation logic
- [ ] T162 [US7] Add percentile calculation
- [ ] T163 [US7] Implement component-level comparison
- [ ] T164 [US7] Write unit tests for comparison logic
- [ ] T165 [US7] Write integration tests for comparison endpoints
- [ ] T166 [US7] Add multi-tenant permission checks

**Independent Test Criteria**:
- Batch processing handles 1000+ students efficiently
- Historical queries return within 200ms
- Cohort comparison shows accurate percentile rankings
- All endpoints respect authentication and permissions

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_batch.py`
- `backend/mastery-engine/tests/unit/test_analytics.py`
- `backend/mastery-engine/tests/integration/test_analytics_endpoints.py`

---

## Phase 10: User Story 10 - Dapr Integration [US10]

**Goal**: Service invocation via Dapr for inter-service communication

### Task List
- [ ] T170 [P] [US10] Implement `POST /process` endpoint in main.py
- [ ] T171 [US10] Add intent routing (mastery_calculation, get_prediction, generate_path)
- [ ] T172 [US10] Implement security context propagation from Dapr
- [ ] T173 [US10] Add standardized response format for Dapr calls
- [ ] T174 [US10] Write unit tests for process endpoint
- [ ] T175 [US10] Write integration tests for Dapr service invocation
- [ ] T176 [US10] Add Dapr-specific error handling and status codes
- [ ] T177 [US10] Document Dapr integration patterns in runbooks.md

**Independent Test Criteria**:
- `/process` endpoint works with all intent types
- Security context properly validates requests
- Dapr service discovery works correctly
- Response format matches other services

**Test Files to Create**:
- `backend/mastery-engine/tests/unit/test_dapr_process.py`
- `backend/mastery-engine/tests/integration/test_dapr_service.py`

---

## Phase 11: Cross-Cutting Concerns & Polish

### Task List
- [ ] T180 [P] Create comprehensive `backend/mastery-engine/README.md` with usage examples
- [ ] T181 [P] Document all API endpoints in `contracts/api-contracts.md` update
- [ ] T182 [P] Update `quickstart.md` with actual deployment commands
- [ ] T183 [P] Create `backend/mastery-engine/docs/troubleshooting.md`
- [ ] T184 [P] Add metrics for all endpoints (Prometheus)
- [ ] T185 [P] Implement distributed tracing with correlation IDs
- [ ] T186 [P] Add circuit breaker pattern for external dependencies
- [ ] T187 [P] Implement graceful shutdown handling
- [ ] T188 [P] Add connection pooling for Redis and Kafka
- [ ] T189 [P] Optimize Docker image size (multi-stage, minimal base)
- [ ] T190 [P] Add health check scripts for Kubernetes liveness/readiness probes
- [ ] T191 [P] Create deployment verification checklist
- [ ] T192 [P] Write load testing script (locust)
- [ ] T193 [P] Run comprehensive test suite with coverage >90%
- [ ] T194 [P] Create final `docs/architecture-decisions.md` with ADR-004 integration
- [ ] T195 [P] Update project structure documentation

---

## Phase 12: Verification & Deployment

### Task List
- [ ] T200 Execute `python test_basic.py` - verify all core functionality
- [ ] T201 Execute `python test_integration.py` - verify end-to-end flows
- [ ] T202 Run `pytest tests/ -v --cov=src --cov-report=html` - verify test coverage
- [ ] T203 Build Docker image: `docker build -t learnflow/mastery-engine:latest .`
- [ ] T204 Test Docker container locally
- [ ] T205 Apply Kubernetes manifests: `kubectl apply -f k8s/`
- [ ] T206 Verify deployment: `kubectl get pods -n learnflow`
- [ ] T207 Test health endpoints: `kubectl port-forward` + curl
- [ ] T208 Run load test: `locust -f tests/load/test_load.py`
- [ ] T209 Perform security audit (check dependencies, secrets)
- [ ] T210 Create final PHR for implementation completion

---

## Implementation Strategy

### MVP Approach (Weeks 1-4)
**Core Functionality (Stories 1, 2, 8, 9)**:
1. **Week 1**: Setup + Foundation (T001-T027)
2. **Week 2**: US1 + US8 (Real-time mastery + Security)
3. **Week 3**: US2 (Event processing)
4. **Week 4**: US9 (Monitoring) + Integration tests

**MVP Deliverable**: Production-ready service with real-time mastery tracking and security

### Incremental Delivery (Weeks 5-10)
**Weeks 5-6**: Advanced Features (US3 + US4)
- Predictive analytics and recommendations
- Can be deployed independently

**Weeks 7-8**: Analytics (US5, US6, US7)
- Batch processing and historical analysis
- All three can be parallel

**Weeks 9-10**: Polish + Dapr Integration (US10 + Cross-cutting)
- Service mesh integration
- Production hardening

### Parallel Execution Plan
```python
# Week 2-3: Independent stories
T030-T043 [US1] Mastery Query API
T070-T081 [US8] Security & Compliance

# Week 3-4: Dependent on US1
T050-T062 [US2] Event Processing

# Week 5-6: Independent advanced features
T100-T110 [US3] Predictions
T120-T130 [US4] Recommendations

# Week 7-8: Independent analytics
T140-T145 [US5] Batch Processing
T150-T155 [US6] Historical Analysis
T160-T166 [US7] Cohort Comparison
```

---

## Task Validation

### Format Compliance
✅ All tasks follow strict checklist format:
- `- [ ] T001 Description with file path`
- `[P]` marker for parallel tasks
- `[US1]` labels for story-specific tasks
- Clear file paths for all implementations

### Completeness Check
✅ Each user story includes:
- Models/Schema creation tasks
- Service layer implementation
- API endpoint creation
- Unit tests
- Integration tests
- Verification criteria

### Independence Verification
✅ Tasks can be completed independently:
- US1 + US8 can run in parallel (separate concerns)
- US2 depends on US1 models but implements independently
- Analytics stories (5,6,7) are fully independent
- US3 + US4 are independent of each other

### Test Coverage
✅ Test tasks are included for all implementations:
- Unit tests: 15+ task entries
- Integration tests: 10+ task entries
- Basic verification: 3+ task entries
- Contract tests: Included in integration

---

## Next Steps

1. **Immediate**: Review this task list with architect
2. **Approval**: Get sign-off on scope and timeline
3. **Execution**: Start with Phase 1 (Setup tasks)
4. **Tracking**: Update checkboxes as tasks complete
5. **Verification**: Run test suites after each phase

**Total Estimated Hours**: 300-400 hours (10 weeks @ 30-40 hrs/week)

**Resource Requirements**:
- 1 Senior Python Developer (full-time)
- Access to Dapr/Kafka/Redis infrastructure
- CI/CD pipeline for testing
- Staging environment for integration testing

---
**Status**: ✅ **READY FOR IMPLEMENTATION**

**Generated**: 2026-01-14
**Spec Version**: 1.0.0
**Next Action**: Architect approval and Phase 1 execution