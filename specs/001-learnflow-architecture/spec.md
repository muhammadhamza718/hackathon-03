# Feature Specification: LearnFlow Multi-Agent AI Tutoring Platform Architecture

**Feature Branch**: `001-learnflow-architecture`
**Created**: 2025-01-11
**Status**: Draft
**Input**: User description: "Project 'LearnFlow' - A Distributed, Multi-Agent AI Tutoring Platform. In keeping with our v2.0.0 Constitution and the Hackathon III standards, specify the learnflow-app architecture with the following high-fidelity details: 1. System Topology: Define the Next.js Frontend (with Monaco Editor) interaction with the FastAPI Triage Service. Map how queries flow from Triage to specialized agents (Concepts, Review, Debug, Exercise, Progress) via Dapr Service Invocation and Kafka Topics. 2. Schema Governance: Define a 'StudentProgress' event schema (using JSON Schema) that ensures data integrity across all 5 tutoring agents. Specify that all inter-service communication is asynchronous and event-driven via Kafka topic 'learning.events'. 3. Mastery Engine Logic: Specify the exact business rules for Mastery Level calculation (40% Completion, 30% Quiz, 20% Quality, 10% Consistency) and define the Dapr State Store keys for persistent storage of these scores. 4. Defensive Operations: Mandate 'Idempotency' in the 'Progress Agent' (to prevent duplicate grading). Specify Kong API Gateway routes that enforce JWT-based authorization for any student exercise submission. 5. Token Efficiency Gateways: Explicitly specify that all backend logic retrieval MUST be driven by the MCP Code Execution pattern. Logic like 'Struggle Detection' must be a local Python script called by the agent, not a verbose LLM instruction. 6. The Sandbox Standard: Define the performance and security requirements for the Python Code Execution sandbox (5s timeout, 50MB memory) as a distinct microservice logic."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Student Receives AI Tutoring Support (Priority: P1)

A student submits a coding exercise through the Next.js frontend Monaco Editor. The system routes the submission through the Triage Service to the appropriate specialized agent (Concepts, Review, Debug, Exercise, or Progress) based on content analysis, processes the request using Dapr service invocation, and returns personalized feedback within performance constraints.

**Why this priority**: This represents the core value proposition of LearnFlow - delivering personalized AI tutoring support to students. Without this flow, the entire platform is non-functional.

**Independent Test**: Can be fully tested by submitting a single coding exercise through the Monaco Editor and verifying that appropriate feedback is received from the correct specialized agent.

**Acceptance Scenarios**:

1. **Given** a student submits a Python function with syntax errors, **When** the Triage Service analyzes the submission, **Then** it should route to the Debug Agent via Dapr service invocation and return specific error correction guidance.
2. **Given** a student submits a correct solution, **When** the Triage Service analyzes the submission, **Then** it should route to the Progress Agent via Kafka event to update mastery scores and return positive reinforcement.

### User Story 2 - Mastery Level Tracking and Progress (Priority: P2)

A student completes multiple learning activities over time. The system continuously calculates mastery levels using the weighted formula (40% Completion, 30% Quiz, 20% Quality, 10% Consistency) and persists these scores in Dapr state store, making them available for personalized learning path recommendations.

**Why this priority**: Enables adaptive learning by tracking student progress across the platform. Essential for demonstrating learning outcomes and personalized instruction.

**Independent Test**: Can be tested by simulating a student completing 5-10 different activity types and verifying mastery scores are calculated correctly and persisted.

**Acceptance Scenarios**:

1. **Given** a student completes 3 exercises, scores 80% on 2 quizzes, maintains 90% code quality, and shows 85% consistency, **When** the Progress Agent calculates mastery, **Then** it should produce: (0.4*0.75) + (0.3*0.80) + (0.2*0.90) + (0.1*0.85) = 0.795 (79.5%).
2. **Given** mastery scores are calculated, **When** the Progress Agent persists them, **Then** they must be stored in Dapr state store with key `student:{student_id}:mastery:{date}`.

### User Story 3 - Code Execution Security and Sandboxing (Priority: P3)

A student or system requests code execution for evaluation or testing. The Python Code Execution Sandbox processes the request with strict resource limits (5s timeout, 50MB memory) and returns results, preventing resource exhaustion and security violations.

**Why this priority**: While core tutoring can function without live code execution, this enables dynamic code evaluation and prevents security risks from untrusted code execution.

**Independent Test**: Can be tested by submitting various Python code snippets (including malicious ones) to verify execution limits and security constraints.

**Acceptance Scenarios**:

1. **Given** a student submits code with infinite loop, **When** processed by the sandbox, **Then** execution terminates after exactly 5 seconds with timeout error.
2. **Given** a student submits code that attempts memory allocation exceeding 50MB, **When** processed by the sandbox, **Then** execution terminates with memory limit error before completion.

### Edge Cases

- What happens when Kafka topic 'learning.events' becomes unavailable during high load?
- How does system handle duplicate Progress Agent events due to Dapr retries?
- What occurs when a student submits the same exercise multiple times within seconds (idempotency challenge)?
- How does system respond when specialized agent crashes during processing?
- What happens when Monaco Editor syntax validation conflicts with Triage Service analysis?

## Requirements _(mandatory)_

**Constitution Compliance**: All requirements MUST align with `.specify/memory/constitution.md` v2.0.0

### Skill Development Requirements

- **SR-001**: Feature MUST be implemented as a Skill with executable MCP code execution pattern
- **SR-002**: Skill MUST include SKILL.md with YAML frontmatter and token efficiency metrics
- **SR-003**: All executable scripts MUST achieve 80-98% token reduction vs manual implementation
- **SR-004**: Skill MUST be compatible with both Claude Code and Goose agents
- **SR-005**: Feature implementation MUST be 100% agent-generated through Skill execution

### Architecture Requirements

- **AR-001**: All services MUST use Dapr for inter-service communication (pub/sub or service invocation)
- **AR-002**: Event-driven communication MUST use Apache Kafka on Kubernetes
- **AR-003**: Frontend MUST use Next.js 14+ with Monaco Editor integration
- **AR-004**: Backend microservices MUST use FastAPI with OpenAI Agent SDK
- **AR-005**: All services MUST be containerized and deployable on Kubernetes

### Functional Requirements

**System Topology Requirements:**

- **FR-001**: Frontend MUST use Next.js 14+ with Monaco Editor for code input and syntax highlighting
- **FR-002**: Triage Service MUST be a FastAPI microservice using OpenAI Agent SDK for query classification
- **FR-003**: System MUST maintain 5 specialized agent services: Concepts-Agent, Review-Agent, Debug-Agent, Exercise-Agent, Progress-Agent
- **FR-004**: All inter-agent communication MUST use Dapr Service Invocation for synchronous requests
- **FR-005**: All agent state updates and cross-cutting events MUST use Kafka topic 'learning.events' for asynchronous messaging
- **FR-006**: Query flow from Frontend → Triage → Specialized Agents MUST complete within 30 seconds

**Schema Governance Requirements:**

- **FR-007**: System MUST define and enforce 'StudentProgress' event schema using JSON Schema standard
- **FR-008**: All 5 tutoring agents MUST validate 'StudentProgress' events against schema before processing
- **FR-009**: All inter-service communication for progress updates MUST be asynchronous via 'learning.events' Kafka topic
- **FR-010**: Schema validation failures MUST be logged and sent to dead-letter queue for analysis

**Mastery Engine Requirements:**

- **FR-011**: Mastery Level calculation MUST use exact formula: 40% Completion + 30% Quiz + 20% Quality + 10% Consistency
- **FR-012**: All component scores MUST be normalized to 0.0-1.0 range before calculation
- **FR-013**: Progress Agent MUST persist mastery scores using Dapr State Store with key pattern: `student:{student_id}:mastery:{date}:{component}`
- **FR-014**: System MUST store both component scores and final calculated mastery score
- **FR-015**: Progress Agent MUST aggregate component scores within 5 seconds of receiving all required data

**Defensive Operations Requirements:**

- **FR-016**: Progress Agent MUST implement idempotency using idempotency keys for all grading operations
- **FR-017**: Kong API Gateway MUST enforce JWT-based authorization for all exercise submission endpoints
- **FR-018**: Kong API Gateway MUST validate JWT claims including student_id and expiration
- **FR-019**: Duplicate submission requests with same idempotency key MUST return cached result within 1 minute
- **FR-020**: System MUST reject exercise submissions from unauthorized JWT tokens with 401 response

**Token Efficiency Requirements:**

- **FR-021**: ALL backend logic retrieval MUST be driven by MCP Code Execution pattern using executable scripts
- **FR-022**: 'Struggle Detection' logic MUST be implemented as local Python script: `/scripts/detect_struggle.py`
- **FR-023**: Complex business logic (mastery calculation, quality scoring) MUST use script-based execution
- **FR-024**: Each MCP script MUST demonstrate 80-98% token reduction compared to equivalent LLM instruction prompts
- **FR-025**: Scripts MUST be invoked by agents via MCP protocol, not embedded in agent instructions

**Sandbox Standard Requirements:**

- **FR-026**: Python Code Execution Sandbox MUST be a distinct FastAPI microservice
- **FR-027**: Sandbox MUST enforce strict 5-second timeout for all code execution
- **FR-028**: Sandbox MUST enforce strict 50MB memory limit for all code execution
- **FR-029**: Sandbox MUST run untrusted code in isolated containers with no network access
- **FR-030**: Sandbox MUST return execution results, timeout errors, or memory violations within 1 second overhead

### Key Entities

- **StudentProgress**: Event schema containing student_id, exercise_id, completion_score, quiz_score, quality_score, consistency_score, timestamp, agent_source
- **MasteryScore**: Calculated scores stored in Dapr state with components: completion, quiz, quality, consistency, final_calculated, timestamp
- **IdempotencyKey**: Unique identifier for exercise submissions to prevent duplicate processing
- **JWTClaims**: Authorization claims including student_id, role, permissions, expiration

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: 95% of student queries are routed to correct specialized agent within 2 seconds by Triage Service
- **SC-002**: Mastery calculations for individual students complete within 5 seconds with 100% accuracy against formula
- **SC-003**: Code execution sandbox handles 50 concurrent requests while maintaining 5s timeout and 50MB memory limits
- **SC-004**: Zero duplicate grading events occur due to idempotency implementation
- **SC-005**: 100% of exercise submissions require valid JWT authorization, with zero unauthorized access
- **SC-006**: All MCP code execution scripts demonstrate 85%+ token reduction compared to manual LLM implementation
- **SC-007**: System maintains 99.9% availability during peak load scenarios with 1000 concurrent students
- **SC-008**: Average end-to-end query response time from frontend submission to feedback delivery stays under 15 seconds