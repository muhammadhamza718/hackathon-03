# Implementation Plan: Mastery Engine

**Branch**: `003-mastery-engine` | **Date**: 2026-01-14 | **Spec**: [specs/003-mastery-engine/spec.md]
**Input**: Feature specification from `/specs/003-mastery-engine/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

**Mastery Engine** is a stateful microservice that tracks student learning progress across multiple dimensions using a sophisticated mastery formula (40% Completion + 30% Quiz + 20% Quality + 10% Consistency). It provides real-time mastery computation, adaptive recommendations, and predictive analytics for personalized learning paths. The service integrates with Dapr State Store for persistent progress tracking, Kafka for event streaming, and MCP skills for efficient calculation algorithms.

**Technical Approach**:
- **Core**: FastAPI microservice with Pydantic V2 for robust validation
- **State Management**: Dapr State Store with composite key patterns (`student:{student_id}:mastery:{date}:{component}`)
- **Event Processing**: Kafka consumer with idempotency and dead-letter queue patterns
- **Computation**: MCP skills achieving 90%+ token efficiency through algorithmic analysis
- **Integration**: Service mesh architecture via Dapr for inter-service communication
- **Analytics**: Real-time mastery tracking with predictive progression modeling

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.104+, Pydantic V2.5+, Dapr Python SDK 1.12+, Kafka-Python 2.0+, OpenAI Agent SDK
**Storage**: Dapr State Store (Redis/PostgreSQL backend) + Kafka for event streaming
**Testing**: pytest 7.4+, pytest-asyncio, pytest-cov (90%+ coverage target)
**Target Platform**: Linux server (Kubernetes 1.28+), containerized microservice
**Project Type**: Web microservice - backend only (Part of multi-agent fleet)
**Performance Goals**:
- P95 latency <100ms for mastery queries
- 1000+ mastery calculations per second
- Kafka throughput: 10k events/sec
- State store operations: 5000+ ops/sec

**Constraints**:
- Real-time response <50ms for active learning paths
- Memory footprint <256MB per pod (baseline)
- Idempotent event processing (at-least-once delivery)
- Zero-downtime deployments required
- GDPR compliance for student data retention (90 days)

**Scale/Scope**:
- 50,000+ active students simultaneously
- 1M+ daily learning events
- 10+ distinct skill areas per student
- 30+ data points per mastery calculation
- Multi-tenant architecture for school/organizational isolation

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**Constitution Version**: 2.0.0 (LearnFlow Agentic Development)

**Mandatory Gates**:
- ✅ **MCP Code Execution First**: All development MUST use Skills with executable scripts
- ✅ **Cloud-Native Architecture**: Must use Kubernetes + Dapr + Kafka for microservices
- ✅ **Token Efficiency**: Skills must demonstrate 80-98% token reduction via script execution
- ✅ **Autonomous Development**: All code must be agent-generated via Skills, not manual

**Framework Requirements**:
- Frontend: Next.js 14+ with Monaco Editor
- Backend: FastAPI + OpenAI Agent SDK
- Infrastructure: Kubernetes, Dapr, Kafka, PostgreSQL
- Standards: AAIF compliance, OpenAPI 3.1, Avro/JSON Schema

**Validation Checklist**:
- [ ] All features planned as Skills with executable scripts
- [ ] Architecture uses Dapr pub/sub or service invocation (no direct communication)
- [ ] Token efficiency metrics included in Skill design
- [ ] Cross-agent compatibility (Claude Code + Goose) verified
- [ ] ADRs planned for architecturally significant decisions

**References**: See `.specify/memory/constitution.md` v2.0.0 for complete requirements

## Project Structure

### Documentation (this feature)

```text
specs/003-mastery-engine/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command) - TODO
├── data-model.md        # Phase 1 output (/sp.plan command) - TODO
├── quickstart.md        # Phase 1 output (/sp.plan command) - TODO
├── contracts/           # Phase 1 output (/sp.plan command) - TODO
│   ├── api-contracts.md
│   ├── event-schemas.md
│   └── state-store-keys.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/mastery-engine/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, Dapr integration, lifecycle
│   ├── security.py                # JWT validation, security context
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mastery.py             # Pydantic models for mastery data
│   │   ├── events.py              # Kafka event schemas
│   │   └── recommendations.py     # Adaptive learning recommendations
│   ├── services/
│   │   ├── __init__.py
│   │   ├── mastery_calculator.py  # MCP skill: mastery formula computation
│   │   ├── state_manager.py       # Dapr State Store operations
│   │   ├── kafka_consumer.py      # Event processing with DLQ support
│   │   └── predictor.py           # Predictive analytics for progression
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── mastery.py         # Query mastery status
│   │       ├── recommendations.py # Get adaptive recommendations
│   │       └── analytics.py       # Historical analysis endpoints
│   └── skills/
│       ├── __init__.py
│       ├── calculator.py          # MCP skill scripts for calculations
│       ├── pattern_matcher.py     # Learning pattern detection
│       └── adaptive_engine.py     # Personalization algorithms
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── tests/
│   ├── unit/
│   │   ├── test_mastery_calculator.py
│   │   ├── test_state_manager.py
│   │   └── test_kafka_consumer.py
│   ├── integration/
│   │   ├── test_api_endpoints.py
│   │   ├── test_dapr_integration.py
│   │   └── test_kafka_integration.py
│   └── contract/
│       └── test_api_contracts.py
├── docs/
│   ├── runbooks.md
│   ├── architecture-decisions.md
│   └── data-flow-diagrams.md
├── Dockerfile
├── requirements.txt
├── .dockerignore
├── .gitignore
└── pytest.ini
```

**Structure Decision**: Microservice backend architecture following the same pattern as Review Agent (Phase 6). Service will be part of the multi-agent fleet, utilizing Dapr for inter-service communication and Kafka for event-driven patterns.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - The plan fully adheres to the Elite Implementation Standard v2.0.0.

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| N/A                        | N/A                | N/A                                  |

## Next Steps

This plan establishes the foundation for Phase 0 (Research). The following phases will proceed as:

1. **Phase 0**: Research all NEEDS CLARIFICATION items
2. **Phase 1**: Detailed design with data models and contracts
3. **Phase 2**: Create 50+ granular tasks via `/sp.tasks` command
4. **Phase 3**: Implementation via autonomous agent execution
5. **Phase 4**: Production deployment and verification

**Immediate Action**: Create Phase 0 Research document to resolve technical unknowns before proceeding to implementation.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**Constitution Version**: 2.0.0 (LearnFlow Agentic Development)

**Mandatory Gates**:
- ✅ **MCP Code Execution First**: All development MUST use Skills with executable scripts
- ✅ **Cloud-Native Architecture**: Must use Kubernetes + Dapr + Kafka for microservices
- ✅ **Token Efficiency**: Skills must demonstrate 80-98% token reduction via script execution
- ✅ **Autonomous Development**: All code must be agent-generated via Skills, not manual

**Framework Requirements**:
- Frontend: Next.js 14+ with Monaco Editor
- Backend: FastAPI + OpenAI Agent SDK
- Infrastructure: Kubernetes, Dapr, Kafka, PostgreSQL
- Standards: AAIF compliance, OpenAPI 3.1, Avro/JSON Schema

**Validation Checklist**:
- [ ] All features planned as Skills with executable scripts
- [ ] Architecture uses Dapr pub/sub or service invocation (no direct communication)
- [ ] Token efficiency metrics included in Skill design
- [ ] Cross-agent compatibility (Claude Code + Goose) verified
- [ ] ADRs planned for architecturally significant decisions

**References**: See `.specify/memory/constitution.md` v2.0.0 for complete requirements

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |
