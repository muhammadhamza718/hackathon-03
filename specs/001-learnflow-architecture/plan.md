# Implementation Plan: LearnFlow Multi-Agent AI Tutoring Platform

**Branch**: `001-learnflow-architecture` | **Date**: 2025-01-11 | **Spec**: [specs/001-learnflow-architecture/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-learnflow-architecture/spec.md`

**Note**: This plan outlines five professional milestones for autonomous implementation via Skills Library and MCP Code Execution patterns.

## Summary

LearnFlow is a distributed, multi-agent AI tutoring platform built on cloud-native architecture with Next.js frontend, FastAPI microservices, Dapr service mesh, and Kafka event streaming. The platform provides personalized tutoring through specialized agents with mastery tracking, sandboxed code execution, and real-time feedback. All development must follow v2.0.0 Constitution using Skills with 80-98% token efficiency.

## Technical Context

**Language/Version**: Python 3.11+ for backend services, TypeScript 5.0+ for Next.js frontend
**Primary Dependencies**: FastAPI, OpenAI Agent SDK, Dapr SDK, Kafka Python, Next.js 14+, Monaco Editor
**Storage**: PostgreSQL via Neon, Dapr State Store, Kafka for event streaming
**Testing**: PyTest for Python, Jest/React Testing Library for frontend, Dapr observability tools
**Target Platform**: Kubernetes (Minikube dev, production clusters), containerized microservices
**Project Type**: Web application (frontend + distributed backend microservices)
**Performance Goals**: 1000+ concurrent users, <2s response time for Triage routing, <30s end-to-end query completion
**Constraints**: All services must use Dapr/Kafka only (no direct communication), 5s/50MB sandbox limits, JWT auth required
**Scale/Scope**: 1000+ concurrent students, 5 specialized agents, event-driven architecture with 10+ microservices

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
- [x] All features planned as Skills with executable scripts
- [x] Architecture uses Dapr pub/sub or service invocation (no direct communication)
- [x] Token efficiency metrics included in Skill design
- [x] Cross-agent compatibility (Claude Code + Goose) verified
- [x] ADRs planned for architecturally significant decisions

**Gate Status**: ✅ **PASSED** - All requirements satisfied by architecture specification

**References**: See `.specify/memory/constitution.md` v2.0.0 for complete requirements

## Project Structure

### Documentation (this feature)

```text
specs/001-learnflow-architecture/
├── plan.md              # This file - 5 milestone roadmap
├── research.md          # Phase 0 - Resolved clarifications & best practices
├── data-model.md        # Phase 1 - Entities & relationships
├── quickstart.md        # Phase 1 - Setup & deployment guide
├── contracts/           # Phase 1 - API schemas (OpenAPI, JSON Schema)
└── tasks.md             # Phase 2 - Executable task breakdown
```

### Source Code Structure (Final Architecture)

```text
learnflow-app/
├── frontend/                    # Next.js 14+ App
│   ├── src/
│   │   ├── app/                 # App Router routes
│   │   ├── components/          # Monaco Editor integration
│   │   ├── lib/                 # API clients & utilities
│   │   └── services/            # Real-time (SSE/Dapr) clients
│   └── tests/
├── backend/                     # FastAPI microservices
│   ├── triage-service/          # Routing & intent detection
│   │   ├── src/
│   │   └── skills/              # MCP execution scripts
│   ├── concepts-agent/          # Concept explanations
│   ├── review-agent/            # Code review & feedback
│   ├── debug-agent/             # Debugging assistance
│   ├── exercise-agent/          # Exercise generation
│   ├── progress-agent/          # Mastery tracking (stateful)
│   └── sandbox-service/         # Code execution isolation
├── infrastructure/              # K8s + Dapr manifests
│   ├── k8s/                     # Deployment specs
│   ├── dapr/                    # Component configs
│   └── kafka/                   # Topic definitions
├── skills-library/              # Shared executable scripts
│   ├── schema-validation/       # StudentProgress validation
│   ├── mastery-calculation/     # 40/30/20/10 formula
│   ├── struggle-detection/      # Python script patterns
│   └── code-execution/          # Sandbox orchestration
└── docs/
    ├── architecture/            # ADRs & diagrams
    └── api/                     # OpenAPI specs
```

**Structure Decision**: Distributed microservices pattern with frontend/backend separation, shared skills library for MCP execution, and infrastructure-as-code for cloud-native deployment.

## Complexity Tracking

> **No violations** - Architecture fully complies with v2.0.0 Constitution

| Principle | Implementation | Rationale |
|-----------|----------------|-----------|
| MCP Code Execution First | All business logic via Skills library scripts | Achieves 80-98% token efficiency |
| Cloud-Native Architecture | Kubernetes + Dapr + Kafka (non-negotiable) | Enables autonomous scaling & deployment |
| Token Efficiency | Scripts for all complex logic (mastery, grading, struggle detection) | Reduces context window usage |
| Autonomous Development | 100% agent-generated via Skills | Validates paradigm shift to teaching AI |

## Five Professional Milestones

### MILESTONE 1: Infrastructure & Common Schema
**Purpose**: Foundation deployment and shared contracts

**Activities:**
1. Deploy Infrastructure using Skills Library:
   - Kafka cluster via `kafka-k8s-setup` Skill
   - Dapr runtime via `dapr-k8s-setup` Skill
   - PostgreSQL via `postgres-k8s-setup` Skill
2. Create Common Types Library:
   - `StudentProgress` JSON Schema with strict validation
   - `MasteryScores` schema for state persistence
   - Event envelope schemas for Kafka topics
3. Establish Dev Environment:
   - Minikube configuration for local development
   - Dapr component definitions (pub/sub, state store)
   - Kafka topic provisioning: `learning.events`, `dead-letter.queue`

**MCP Code Execution:**
- Scripts: `infrastructure/deploy-kafka.py`, `schema/validation-generator.py`
- Token Efficiency: 90% reduction vs manual K8s YAML authoring
- Output: Running cluster with validated schemas

**AD Required:** ADR-001: Event-Driven Architecture Selection (Kafka vs alternatives)
**PHR Required:** Document infrastructure decisions and schema design rationale

**Verification:** Infrastructure health checks + Schema validation tests = 95% token efficiency achieved

---

### MILESTONE 2: The Routing Core (Triage Service)
**Purpose**: Intelligent request routing with Intent Detection

**Activities:**
1. Build FastAPI Triage Service:
   - OpenAI Agent SDK integration for natural language parsing
   - Intent classification logic (syntax errors vs concepts vs grading requests)
2. Dapr Service Invocation Setup:
   - Sidecar configuration for Triage Service
   - Service discovery for 5 specialized agents
   - Circuit breaker patterns for fault tolerance
3. MCP Code Execution Integration:
   - `intent-detection.py` - Local script for classification
   - `route-selection.py` - Deterministic agent routing logic

**MCP Code Execution:**
- Scripts: `triage/intent-detection.py`, `triage/route-selection.py`
- Token Efficiency: 85% reduction vs LLM-based routing instructions
- Input: Raw student query → Output: Target agent + routing metadata

**AD Required:** ADR-002: Dapr Service Invocation vs gRPC for Inter-Service Communication
**PHR Required:** Document intent detection model training and routing accuracy metrics

**Verification:** 95% routing accuracy with <2s response time = Token efficiency benchmark met

---

### MILESTONE 3: The Specialized Agent Fleet
**Purpose**: Five autonomous tutoring agents with unique capabilities

**Sequence of Implementation:**
1. **Progress Agent** (Stateful foundation - deploy first)
2. **Debug Agent** (Syntax/error handling - logical next step)
3. **Concepts Agent** (Knowledge explanations - builds on Debug)
4. **Exercise Agent** (Generation capabilities - requires other agents)
5. **Review Agent** (Quality assessment - completes fleet)

**Per-Agent Implementation Pattern:**
- FastAPI microservice with Dapr sidecar
- OpenAI Agent SDK for natural language processing
- **Unique MCP Scripts per Agent:**
  - **Progress Agent**: `mastery-calculation.py`, `score-aggregation.py`
  - **Debug Agent**: `syntax-analyzer.py`, `error-pattern-detection.py`
  - **Concepts Agent**: `concept-mapping.py`, `explanation-generator.py`
  - **Exercise Agent**: `problem-generator.py`, `difficulty-calibration.py`
  - **Review Agent**: `code-quality-scoring.py`, `hint-generation.py`

**Common Infrastructure:**
- Dapr Pub/Sub subscriptions to `learning.events`
- State store access (Progress Agent only writes, others read)
- Idempotency keys for all operations

**MCP Code Execution:**
- Each agent has 2-3 specialized scripts (10 total)
- Token Efficiency: 82-94% reduction vs manual implementation
- Pattern: Scripts encapsulate domain logic, agents handle orchestration

**AD Required:** ADR-003: Agent Specialization Boundaries (what belongs where)
**PHR Required:** Document each agent's script efficiency metrics

**Verification:** Each agent independently functional with valid token efficiency benchmarks

---

### MILESTONE 4: The Mastery Engine (Progress Agent)
**Purpose**: Stateful learning progress tracking with Dapr State Store

**Activities:**
1. Dapr State Store Integration:
   - Key pattern implementation: `student:{student_id}:mastery:{date}:{component}`
   - Composite score storage and retrieval
   - Historical tracking for trend analysis
2. Kafka Consumer Logic:
   - Event processing from `learning.events` topic
   - Deduplication via idempotency keys
   - Real-time mastery score updates
3. Mastery Formula Implementation:
   - Exact calculation: 40% Completion + 30% Quiz + 20% Quality + 10% Consistency
   - Normalization logic for component scores (0.0-1.0)
   - Aggregation and final score computation
4. Defensive Operations:
   - Idempotency implementation to prevent duplicate grading
   - Dead-letter queue handling for malformed events

**MCP Code Execution:**
- Scripts: `mastery-engine/calculation.py`, `mastery-engine/aggregation.py`
- Token Efficiency: 92% reduction vs LLM-based calculation
- Validation: 100% formula accuracy across test cases

**AD Required:** ADR-004: Dapr State Store vs Redis for Mastery Data
**PHR Required:** Document idempotency implementation and Kafka consumer patterns

**Verification:** Zero duplicate events, formula accuracy 100%, state persistence verified

---

### MILESTONE 5: Real-Time Frontend & Monaco Integration
**Purpose**: User interface with live feedback and code editing

**Activities:**
1. Next.js 14+ App Router Setup:
   - Server Components for initial render
   - Client Components for interactive Monaco Editor
   - Route handlers for API integration
2. Monaco Editor Integration:
   - Python language server connection
   - Real-time syntax validation
   - Custom theming and keybindings
3. Real-Time Communication:
   - Dapr Pub/Sub for frontend subscriptions
   - Server-Sent Events (SSE) for streaming feedback
   - Fallback patterns for connection resilience
4. Kong API Gateway Configuration:
   - JWT validation for exercise submissions
   - Rate limiting and circuit breakers
   - Secure routing to microservices
5. Frontend Skills Integration:
   - `monaco-setup.py` - Editor configuration scripts
   - `sse-client.py` - Real-time event handling
   - `jwt-auth.py` - Token validation logic

**MCP Code Execution:**
- Scripts: `frontend/monaco-config.py`, `frontend/sse-handler.py`
- Token Efficiency: 88% reduction vs manual React implementation
- Performance: <200ms re-render, <1s feedback delivery

**AD Required:** ADR-005: SSE vs WebSocket vs Dapr Pub/Sub for Real-Time Updates
**PHR Required:** Document frontend integration patterns and latency optimization

**Verification:** End-to-end flow <15s, real-time feedback within 1s, JWT auth enforced

---

## Milestone Interdependencies

```
M1 (Infrastructure) → M2 (Triage) → M3 (Agents) → M4 (Mastery) → M5 (Frontend)
    ↓                    ↓                ↓              ↓              ↓
  Kafka,             Routing,         Agent         State,         Monaco,
  Dapr,              Intent           Logic         Events         SSE
  PostgreSQL         Detection        Scripts       Consumer       Kong
```

**Critical Path**: M1 → M2 → M3a → M4 → M5 (Progress Agent is prerequisite for others)

## Operational Mandates

### ADR Requirement
Every milestone MUST include an Architecture Decision Record:
- **ADR-001**: Infrastructure Technology Selection
- **ADR-002**: Service Communication Pattern
- **ADR-003**: Agent Architecture Boundaries
- **ADR-004**: State Management Strategy
- **ADR-005**: Real-Time Communication Protocol

### PHR Requirement
Every milestone MUST include a Prompt History Record documenting:
- Design decisions and rationale
- Token efficiency benchmarks
- Cross-agent compatibility results
- Lessons learned and improvements

### Token Efficiency Gate
**No milestone is "Done" until verified:**
- Scripts achieve 80-98% token reduction vs manual implementation
- Benchmarks measured using before/after context window comparison
- Results documented in PHR for each milestone

## Phase 0 Research (Next Step)

Before M1 implementation, resolve these research items:

### Unknowns & Clarifications Needed:
1. **Kafka Partitioning Strategy**: How should `learning.events` be partitioned for optimal parallel processing?
2. **Dapr State Store Performance**: What are the latency characteristics at 1000+ concurrent students?
3. **Monaco Python LSP**: What are the integration patterns for Monaco + Python language server in Next.js?
4. **Kong JWT Overhead**: What is the performance impact of JWT validation on Kong gateway?

### Research Tasks:
- [ ] Research Kafka topic partitioning for `learning.events` with 10+ microservices
- [ ] Find best practices for Dapr state store key patterns at scale
- [ ] Discover Monaco Editor Python integration patterns for Next.js App Router
- [ ] Benchmark Kong JWT validation performance overhead

**Exit Criteria**: All research items resolved in `research.md` before Milestone 1 begins.

## Next Commands

1. **Create Research**: `/sp.clarify` to resolve unknowns from Phase 0
2. **Generate Data Model**: After research, `/sp.plan` will create `data-model.md` and `contracts/`
3. **Create Tasks**: `/sp.tasks` to break down Milestone 1 into executable Skill tasks

**Branch Ready**: `001-learnflow-architecture` - Ready for autonomous development via Skills.