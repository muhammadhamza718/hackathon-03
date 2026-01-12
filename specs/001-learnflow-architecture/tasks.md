# Tasks: Milestone 1 - Infrastructure & Common Schema
**Feature**: `001-learnflow-architecture`
**Milestone**: 1 - Infrastructure & Common Schema
**Generated**: 2026-01-12
**Status**: Ready for autonomous execution

## Milestone Overview

This milestone establishes the foundational infrastructure (Kafka, Dapr, PostgreSQL) and common schema contracts required for all subsequent development. All tasks follow the Skills-First mandate using MCP Code Execution patterns for 80-98% token efficiency.

**Milestone Goal**: Deploy production-ready infrastructure and validate schemas before agent implementation begins.

---

## Phase 1: Skills-First Infrastructure Setup

### 1.1 Core Infrastructure Deployment via Skills Library

**Prerequisite**: Ensure `skills-library/` directory exists in project root. If not, create it with subdirectories for each Skill.

#### Infrastructure Tasks:

- [X] T001 Deploy Kafka cluster using `kafka-k8s-setup` Skill
  - **Description**: Execute `kafka-k8s-setup` Skill to provision Kafka on Kubernetes with 12 partitions for `learning.events` and 6 partitions for `dead-letter.queue`
  - **Skill Path**: `skills-library/kafka-k8s-setup/kafka-setup.py`
  - **Output**: Running Kafka cluster with configured topics
  - **Configuration**: 12 partitions, replication factor 3, 7-day retention
  - **Files**: `infrastructure/k8s/kafka-deployment.yaml`, `infrastructure/kafka/topics-config.yaml`

- [X] T002 Deploy Dapr runtime using `dapr-k8s-setup` Skill
  - **Description**: Execute `dapr-k8s-setup` Skill to install Dapr sidecars on Kubernetes cluster
  - **Skill Path**: `skills-library/dapr-k8s-setup/dapr-config.py`
  - **Output**: Dapr-enabled Kubernetes cluster with sidecar injection
  - **Files**: `infrastructure/k8s/dapr-deployment.yaml`, `infrastructure/dapr/components.yaml`

- [X] T003 Deploy PostgreSQL using `postgres-k8s-setup` Skill
  - **Description**: Execute `postgres-k8s-setup` Skill to provision PostgreSQL database for long-term storage
  - **Skill Path**: `skills-library/postgres-k8s-setup/postgres-config.py`
  - **Output**: Running PostgreSQL instance with proper networking
  - **Files**: `infrastructure/k8s/postgres-deployment.yaml`, `infrastructure/postgres/init.sql`

#### Verification Tasks:

- [X] T004 [P] Verify Kafka health using `verify-infra-health.py`
  - **Description**: Run `verify-infra-health.py` script to confirm Kafka brokers are healthy and topics are created
  - **Script Path**: `scripts/verify-infra-health.py --service kafka --check topics,partitions`
  - **Expected**: All 12 partitions for `learning.events`, 6 for `dead-letter.queue`, 3 replicas

- [X] T005 [P] Verify Dapr health using `verify-infra-health.py`
  - **Description**: Run `verify-infra-health.py` script to confirm Dapr control plane and sidecars are healthy
  - **Script Path**: `scripts/verify-infra-health.py --service dapr --check control-plane,sidecars`
  - **Expected**: Dapr pods running, sidecar injection enabled

- [X] T006 [P] Verify PostgreSQL health using `verify-infra-health.py`
  - **Description**: Run `verify-infra-health.py` script to confirm PostgreSQL is accepting connections
  - **Script Path**: `scripts/verify-infra-health.py --service postgres --check connectivity,query-response`
  - **Expected**: Database responsive, connections successful

---

## Phase 2: Common Contract Implementation

### 2.1 JSON Schema & Contract Generation

#### Schema Implementation Tasks:

- [X] T007 [P] [US1] Generate StudentProgress JSON Schema from data-model.md
  - **Description**: Create `StudentProgress` JSON Schema file based on data-model.md specifications
  - **Skill Path**: `skills-library/schema-validation/schema-generator.py`
  - **Input**: `specs/001-learnflow-architecture/data-model.md`
  - **Output**: `contracts/schemas/student-progress.schema.json`
  - **Validation**: All fields properly typed, required fields enforced, pattern matching for IDs

- [X] T008 [P] [US1] Generate MasteryScore JSON Schema
  - **Description**: Create `MasteryScore` schema for Dapr state store persistence
  - **Skill Path**: `skills-library/schema-validation/schema-generator.py`
  - **Input**: Mastery formula requirements (40/30/20/10)
  - **Output**: `contracts/schemas/mastery-score.schema.json`
  - **Validation**: Component breakdown, final calculation field, timestamp

- [X] T009 [P] [US1] Generate IdempotencyKey schema
  - **Description**: Create schema for duplicate prevention mechanism
  - **Skill Path**: `skills-library/schema-validation/schema-generator.py`
  - **Output**: `contracts/schemas/idempotency-key.schema.json`
  - **Validation**: 32-character hex format, uniqueness constraint

#### Schema Verification Tasks:

- [X] T010 [P] Validate all schemas using `verify-schema-validation.py`
  - **Description**: Run validation script against all generated JSON schemas
  - **Script Path**: `scripts/verify-schema-validation.py --schemas contracts/schemas/`
  - **Expected**: 100% schema validity, no JSON syntax errors, proper type definitions

- [X] T011 [P] Test schema validation with sample data
  - **Description**: Generate test data and validate against schemas
  - **Script Path**: `scripts/verify-schema-validation.py --test-data tests/data/ --schema contracts/schemas/student-progress.schema.json`
  - **Expected**: Valid test data passes, invalid data fails with appropriate errors

### 2.2 Avro Event Envelopes

#### Event Schema Tasks:

- [X] T012 [P] [US1] Generate StudentProgressEvent Avro schema
  - **Description**: Create Avro schema for Kafka event from existing yaml definition
  - **Skill Path**: `skills-library/schema-validation/avro-converter.py`
  - **Input**: `specs/001-learnflow-architecture/contracts/kafka-schemas.yaml`
  - **Output**: `contracts/avro/student-progress-event.avsc`
  - **Validation**: Matches student_id partitioning decision from research

- [X] T013 [P] [US1] Generate MasteryScoreUpdate Avro schema
  - **Description**: Create Avro schema for mastery updates
  - **Skill Path**: `skills-library/schema-validation/avro-converter.py`
  - **Input**: `specs/001-learnflow-architecture/contracts/kafka-schemas.yaml`
  - **Output**: `contracts/avro/mastery-score-update.avsc`

- [X] T014 [P] [US1] Generate DeadLetterEvent Avro schema
  - **Description**: Create Avro schema for dead-letter queue events
  - **Skill Path**: `skills-library/schema-validation/avro-converter.py`
  - **Input**: `specs/001-learnflow-architecture/contracts/kafka-schemas.yaml`
  - **Output**: `contracts/avro/dead-letter-event.avsc`

- [X] T015 [P] [US1] Generate SandboxExecutionEvent Avro schema
  - **Description**: Create Avro schema for sandbox execution results
  - **Skill Path**: `skills-library/schema-validation/avro-converter.py`
  - **Input**: `specs/001-learnflow-architecture/contracts/kafka-schemas.yaml`
  - **Output**: `contracts/avro/sandbox-execution-event.avsc`

#### Avro Verification Tasks:

- [X] T016 [P] Validate Avro schemas using `verify-avro-schemas.py`
  - **Description**: Verify all Avro schemas compile and are valid
  - **Script Path**: `scripts/verify-avro-schemas.py --schemas contracts/avro/`
  - **Expected**: All schemas compile, proper field types, namespace validation

- [X] T017 [P] Test Avro schema serialization/deserialization
  - **Description**: Test that Avro schemas can correctly serialize and deserialize sample events
  - **Script Path**: `scripts/verify-avro-schemas.py --test-serialization contracts/avro/student-progress-event.avsc`
  - **Expected**: Round-trip serialization works, data integrity maintained

---

## Phase 3: Infrastructure-as-Code Components

### 3.1 Dapr State Store Configuration

#### Dapr Component Tasks:

- [X] T018 Configure Redis State Store for Dapr
  - **Description**: Create Dapr component definition for Redis state store (Progress Agent)
  - **Files**: `infrastructure/dapr/components/redis-statestore.yaml`
  - **Configuration**: Based on research findings (<5ms read, <10ms write at 1000+ QPS)
  - **Key Pattern**: `student:{student_id}:mastery:{date}:{component}`

- [X] T019 Configure Dapr Pub/Sub Component for Kafka
  - **Description**: Create Dapr pub/sub component linking to Kafka `learning.events` topic
  - **Files**: `infrastructure/dapr/components/kafka-pubsub.yaml`
  - **Configuration**: Topic: `learning.events`, consumerGroup: per-service

- [X] T020 Configure Dapr Service Invocation
  - **Description**: Create service invocation configuration for inter-agent communication
  - **Files**: `infrastructure/dapr/components/service-invocation.yaml`
  - **Configuration**: Circuit breaker, retry policies

#### Dapr Verification Tasks:

- [X] T021 [P] Verify Dapr components using `verify-dapr-components.py`
  - **Description**: Validate all Dapr components are properly configured and healthy
  - **Script Path**: `scripts/verify-dapr-components.py --components infrastructure/dapr/components/`
  - **Expected**: All components registered, no configuration errors

- [X] T022 [P] Test Dapr Redis state store connectivity
  - **Description**: Test read/write operations to Redis via Dapr
  - **Script Path**: `scripts/verify-dapr-components.py --test-state-store redis --test-key-pattern "student:123:mastery:2024-01-12:completion"`
  - **Expected**: <10ms write, <5ms read, proper key storage

### 3.2 Kubernetes Manifests

#### K8s Manifest Tasks:

- [X] T023 Create namespace and RBAC for LearnFlow
  - **Description**: Create kubernetes namespace and RBAC policies
  - **Files**: `infrastructure/k8s/001-namespace.yaml`, `infrastructure/k8s/002-rbac.yaml`

- [X] T024 Create Dapr sidecar injection configuration
  - **Description**: Configure automatic Dapr sidecar injection for microservices
  - **Files**: `infrastructure/k8s/003-dapr-injection.yaml`

- [X] T025 Create Kafka topic provisioning Job
  - **Description**: Kubernetes Job to provision Kafka topics with exact partition count
  - **Files**: `infrastructure/k8s/004-kafka-topics.yaml`
  - **Configuration**: 12 partitions for `learning.events`, 6 for `dead-letter.queue`

- [X] T026 Create Dapr component deployment manifests
  - **Description**: Deploy Dapr components as Kubernetes resources
  - **Files**: `infrastructure/k8s/005-dapr-components.yaml`
  - **Content**: Redis state store, Kafka pub/sub, service invocation

#### K8s Verification Tasks:

- [X] T027 [P] Verify Kubernetes resources using `verify-k8s-resources.py`
  - **Description**: Validate all K8s manifests are syntactically correct
  - **Script Path**: `scripts/verify-k8s-resources.py --manifests infrastructure/k8s/ --check syntax,resources`
  - **Expected**: Valid YAML, proper API versions, resource definitions

- [X] T028 [P] Test Kafka topic creation via Job
  - **Description**: Execute Kafka topic provisioning job and verify creation
  - **Script Path**: `scripts/verify-k8s-resources.py --test-job kafka-topics --verify-partitions 12`
  - **Expected**: Topics created with correct partition counts

---

## Phase 4: ADR Documentation

### 4.1 Architecture Decision Records

#### ADR Creation Tasks:

- [X] T029 Document ADR-001: Infrastructure Technology Selection
  - **Description**: Create ADR documenting infrastructure choices based on research findings
  - **File**: `history/adr/ADR-001-infrastructure-technology-selection.md`
  - **Content**:
    - **Context**: Need for cloud-native infrastructure supporting 1000+ concurrent students
    - **Decision**: Kafka (12 partitions), Dapr + Redis (state store), PostgreSQL (long-term)
    - **Alternatives Considered**: RabbitMQ (rejected), PostgreSQL-only (rejected), pure Redis (rejected)
    - **Consequences**: High performance, scalable, but operational complexity
    - **Validation**: Based on research.md findings (Kafka <5ms, Dapr Redis <10ms)

#### ADR Verification Tasks:

- [X] T030 [P] Validate ADR completeness using `verify-adr-completeness.py`
  - **Description**: Ensure ADR contains all required sections per constitution
  - **Script Path**: `scripts/verify-adr-completeness.py --adr history/adr/ADR-001-infrastructure-technology-selection.md`
  - **Expected**: Context, Decision, Alternatives, Consequences sections present

---

## Phase 5: Integration Testing & Final Validation

### 5.1 End-to-End Infrastructure Validation

- [X] T031 Run comprehensive infrastructure health check
  - **Description**: Execute full infrastructure validation suite
  - **Script Path**: `scripts/verify-infra-health.py --full-suite --timeout 300`
  - **Expected**: All services healthy, Kafka/Dapr/PostgreSQL responding

- [X] T032 Test schema compatibility across infrastructure
  - **Description**: Verify schemas work correctly with Kafka and Dapr
  - **Script Path**: `scripts/verify-schema-compatibility.py --kafka --dapr --schemas contracts/`
  - **Expected**: 100% compatibility, no serialization errors

- [X] T033 Document infrastructure endpoints and connection strings
  - **Description**: Create operational documentation for all infrastructure components
  - **File**: `specs/001-learnflow-architecture/infrastructure-connections.md`
  - **Content**: Connection strings, ports, health endpoints, monitoring URLs

---

## Dependencies & Completion Order

### Setup Phase (Must Complete First)
```
T001 (Kafka) → T004 (Verify) → T002 (Dapr) → T005 (Verify) → T003 (Postgres) → T006 (Verify)
```

### Contracts Phase (Parallelizable after Setup)
```
T007→T008→T009 (Schema Gen) → T010→T011 (Schema Validation) [P]
T012→T013→T014→T015 (Avro Gen) → T016→T017 (Avro Validation) [P]
```

### IaC Phase (Depends on Setup)
```
T018→T019→T020 (Dapr Config) → T021→T022 (Dapr Verify) [P]
T023→T024→T025→T026 (K8s Manifests) → T027→T028 (K8s Verify) [P]
```

### Documentation Phase (Can run parallel to IaC)
```
T029 (ADR) → T030 (Validate) [P]
```

### Integration Phase (Final)
```
T031 (Full Health Check) → T032 (Schema Compatibility) → T033 (Documentation)
```

---

## Parallel Execution Opportunities

**High-Parallelism Groups:**

1. **Schema Generation Group** (T007-T009 + T012-T015) - All schema creation tasks
2. **Verification Group** (T010, T011, T016, T017, T021, T022, T027, T028) - All validation tasks
3. **Infrastructure Group** (T004, T005, T006, T031) - All health checks

**Medium-Parallelism Groups:**

4. **Dapr Configuration** (T018, T019, T020) - All Dapr components
5. **K8s Manifests** (T023, T024, T025, T026) - All K8s resources

---

## Independent Test Criteria

**Each Phase Can Be Tested Independently:**

- **Phase 1**: `verify-infra-health.py` returns PASS for all infrastructure services
- **Phase 2**: `verify-schema-validation.py` validates all schemas 100%
- **Phase 3**: `verify-dapr-components.py` and `verify-k8s-resources.py` return PASS
- **Phase 4**: `verify-adr-completeness.py` confirms ADR meets standards
- **Phase 5**: End-to-end health check confirms 95%+ of infrastructure is operational

---

## MVP Scope Recommendation

**Start with these critical tasks (Minimum Viable Progress):**

1. **T001**: Deploy Kafka cluster
2. **T004**: Verify Kafka health
3. **T007**: Generate StudentProgress JSON Schema
4. **T012**: Generate StudentProgressEvent Avro schema
5. **T018**: Configure Dapr Redis State Store
6. **T029**: Document ADR-001

**MVP Success Criteria**: Kafka running + Schemas created + Dapr configured + ADR documented

---

## Token Efficiency Metrics

**Skills-First Mandate**: All tasks use executable MCP scripts for token reduction:

- **Infrastructure Deployment**: 90% reduction vs manual K8s YAML authoring
- **Schema Generation**: 95% reduction vs manual schema writing
- **Verification Scripts**: 85% reduction vs manual testing
- **ADR Documentation**: 80% reduction vs manual ADR creation

**Target**: 85%+ average token efficiency across all tasks

---

## Next Steps After Milestone 1

Once all tasks complete successfully:

1. **Verify**: Run final `verify-infra-health.py --full-suite`
2. **Commit**: All changes to `001-learnflow-architecture` branch
3. **Proceed**: Move to Milestone 2 (Triage Service implementation)
4. **Ready**: Infrastructure now supports 1000+ concurrent student scenarios

**Estimated Completion Time**: 4-6 hours with autonomous agent execution
**Complexity**: High (distributed infrastructure)
**Risk Level**: Medium (requires careful coordination of multiple services)