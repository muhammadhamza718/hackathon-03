---
id: 001
title: "Specify LearnFlow Architecture"
stage: "spec"
date_iso: "2025-01-11"
surface: "agent"
model: "claude-sonnet-4-5-20250929"
feature: "001-learnflow-architecture"
branch: "001-learnflow-architecture"
user: "Project 'LearnFlow' - A Distributed, Multi-Agent AI Tutoring Platform. In keeping with our v2.0.0 Constitution and the Hackathon III standards, specify the learnflow-app architecture with the following high-fidelity details: 1. System Topology: Define the Next.js Frontend (with Monaco Editor) interaction with the FastAPI Triage Service. Map how queries flow from Triage to specialized agents (Concepts, Review, Debug, Exercise, Progress) via Dapr Service Invocation and Kafka Topics. 2. Schema Governance: Define a 'StudentProgress' event schema (using JSON Schema) that ensures data integrity across all 5 tutoring agents. Specify that all inter-service communication is asynchronous and event-driven via Kafka topic 'learning.events'. 3. Mastery Engine Logic: Specify the exact business rules for Mastery Level calculation (40% Completion, 30% Quiz, 20% Quality, 10% Consistency) and define the Dapr State Store keys for persistent storage of these scores. 4. Defensive Operations: Mandate 'Idempotency' in the 'Progress Agent' (to prevent duplicate grading). Specify Kong API Gateway routes that enforce JWT-based authorization for any student exercise submission. 5. Token Efficiency Gateways: Explicitly specify that all backend logic retrieval MUST be driven by the MCP Code Execution pattern. Logic like 'Struggle Detection' must be a local Python script called by the agent, not a verbose LLM instruction. 6. The Sandbox Standard: Define the performance and security requirements for the Python Code Execution sandbox (5s timeout, 50MB memory) as a distinct microservice logic."
command: "sp.specify"
labels: ["spec", "learnflow", "architecture", "multi-agent", "hackathon-iii"]
links:
  spec: "specs/001-learnflow-architecture/spec.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files_yaml: |
  - specs/001-learnflow-architecture/spec.md
  - specs/001-learnflow-architecture/checklists/requirements.md
  - .specify/memory/constitution.md
tests_yaml: |
  - Validated against 14-point quality checklist
  - 30 functional requirements created and verified
  - 8 measurable success criteria defined
  - 3 user stories with independent test scenarios
prompt_text: |
Project 'LearnFlow' - A Distributed, Multi-Agent AI Tutoring Platform.

In keeping with our v2.0.0 Constitution and the Hackathon III standards, specify the learnflow-app architecture with the following high-fidelity details:
1. System Topology: Define the Next.js Frontend (with Monaco Editor) interaction with the FastAPI Triage Service. Map how queries flow from Triage to specialized agents (Concepts, Review, Debug, Exercise, Progress) via Dapr Service Invocation and Kafka Topics.
2. Schema Governance: Define a 'StudentProgress' event schema (using JSON Schema) that ensures data integrity across all 5 tutoring agents. Specify that all inter-service communication is asynchronous and event-driven via Kafka topic 'learning.events'.
3. Mastery Engine Logic: Specify the exact business rules for Mastery Level calculation (40% Completion, 30% Quiz, 20% Quality, 10% Consistency) and define the Dapr State Store keys for persistent storage of these scores.
4. Defensive Operations: Mandate 'Idempotency' in the 'Progress Agent' (to prevent duplicate grading). Specify Kong API Gateway routes that enforce JWT-based authorization for any student exercise submission.
5. Token Efficiency Gateways: Explicitly specify that all backend logic retrieval MUST be driven by the MCP Code Execution pattern. Logic like 'Struggle Detection' must be a local Python script called by the agent, not a verbose LLM instruction.
6. The Sandbox Standard: Define the performance and security requirements for the Python Code Execution sandbox (5s timeout, 50MB memory) as a distinct microservice logic.

response_text: |
SPECIFICATION COMPLETE: 001-learnflow-architecture

Successfully created comprehensive architectural specification for LearnFlow Multi-Agent AI Tutoring Platform.

KEY DELIVERABLES:
- Feature Branch: 001-learnflow-architecture
- Spec File: specs/001-learnflow-architecture/spec.md
- Quality Checklist: specs/001-learnflow-architecture/checklists/requirements.md

ARCHITECTURAL COMPONENTS COVERED:
1. ✅ System Topology: Next.js → Triage → 5 Specialized Agents via Dapr/Kafka
2. ✅ Schema Governance: StudentProgress JSON Schema with async event flow
3. ✅ Mastery Engine: Exact 40/30/20/10 formula with Dapr State Store keys
4. ✅ Defensive Ops: Idempotency + Kong JWT authorization
5. ✅ Token Efficiency: MCP Code Execution pattern mandate for all logic
6. ✅ Sandbox Standard: 5s timeout, 50MB memory, isolated execution

VALIDATION: All 14 quality checklist items PASSED
- 30 functional requirements (FR-001 to FR-030)
- 8 measurable success criteria
- 3 priority-ranked user stories with acceptance scenarios
- 5 edge cases identified
- No [NEEDS CLARIFICATION] markers remaining

STATUS: Ready for /sp.clarify or /sp.plan execution
outcome: "Specification created and validated successfully"
evaluation: "All checklist items passed - ready for planning phase"
---
# PHR: LearnFlow Architecture Specification

## Summary

Created comprehensive architectural specification for LearnFlow Multi-Agent AI Tutoring Platform (Branch: `001-learnflow-architecture`). The spec addresses all 6 high-fidelity requirements provided by the user.

## Specification Components

### 1. System Topology ✅
- **Frontend**: Next.js 14+ with Monaco Editor integration
- **Triage Service**: FastAPI microservice using OpenAI Agent SDK for routing
- **Specialized Agents**: Concepts, Review, Debug, Exercise, Progress (5 total)
- **Communication**: Dapr Service Invocation for sync, Kafka for async events
- **Flow**: Frontend → Triage → Agent → Response within 30s

### 2. Schema Governance ✅
- **Event Schema**: StudentProgress JSON Schema for data integrity
- **Validation**: All 5 agents must validate against schema
- **Transport**: Kafka topic 'learning.events' for all inter-service communication
- **Error Handling**: Failed validations go to dead-letter queue

### 3. Mastery Engine ✅
- **Formula**: 40% Completion + 30% Quiz + 20% Quality + 10% Consistency
- **Storage**: Dapr State Store keys `student:{id}:mastery:{date}:{component}`
- **Performance**: Calculation within 5 seconds of data receipt
- **Accuracy**: 100% formula compliance

### 4. Defensive Operations ✅
- **Idempotency**: Progress Agent prevents duplicate grading via idempotency keys
- **Authorization**: Kong API Gateway JWT validation for exercise submissions
- **Security**: Student ID validation in JWT claims

### 5. Token Efficiency ✅
- **MCP Mandate**: All backend logic via MCP Code Execution pattern
- **Struggle Detection**: Local Python script `/scripts/detect_struggle.py`
- **Token Reduction**: 80-98% target vs manual LLM implementation
- **Pattern**: Scripts invoked via MCP protocol, not embedded instructions

### 6. Sandbox Standard ✅
- **Service**: Distinct FastAPI microservice for code execution
- **Limits**: 5s timeout, 50MB memory maximum
- **Security**: Isolated containers, no network access
- **Response**: Results/Errors within 1s overhead

## Validation Metrics

**Functional Requirements**: 30 (FR-001 to FR-030) ✅
**Success Criteria**: 8 measurable outcomes ✅
**User Stories**: 3 priority-ranked stories ✅
**Edge Cases**: 5 identified scenarios ✅
**Quality Check**: 14/14 items passed ✅

## Next Steps

The specification is complete and validated. Ready for:
- `/sp.clarify` - If any architecture decisions need clarification
- `/sp.plan` - To generate detailed implementation plan
- `/sp.tasks` - To break down into executable tasks

## Architecture Significance

This specification represents a significant architectural decision for the LearnFlow platform, defining:
- Event-driven microservices architecture
- Multi-agent AI system design
- Security and performance requirements
- MCP Code Execution pattern integration

Consider documenting this as an ADR using `/sp.adr learnflow-multi-agent-architecture`.