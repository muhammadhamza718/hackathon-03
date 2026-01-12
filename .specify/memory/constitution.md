<!--
SYNC IMPACT REPORT
Version Change: 1.0.0 → 2.0.0 (MAJOR - Complete governance rewrite for agentic development)
Modified Principles:
  - [PRINCIPLE_1_NAME] → MCP Code Execution First
  - [PRINCIPLE_2_NAME] → Cloud-Native Architecture Mandate
  - [PRINCIPLE_3_NAME] → Token Efficiency & Context Optimization
  - [PRINCIPLE_4_NAME] → Autonomous Agentic Development
Added Sections:
  - Technology Stack & Standards
  - Development Workflow & Skills Architecture
Removed Sections:
  - [PRINCIPLE_5_NAME] (placeholder)
  - [PRINCIPLE_6_NAME] (placeholder)
Templates Requiring Updates:
  - ✅ .specify/templates/plan-template.md - Updated to reference constitution v2.0.0
  - ✅ .specify/templates/spec-template.md - Added MCP pattern requirements
  - ✅ .specify/templates/tasks-template.md - Added agentic task categorization
  - ⚠️ .specify/templates/commands/sp.phr.md - Shell script available but not yet updated
Deferred TODOs:
  - TODO(RATIFICATION_DATE): Set final date after team approval
-->

# LearnFlow Constitution

## Core Principles

### I. MCP Code Execution First

**Non-Negotiable Rule:** Every development task MUST be executed through MCP Code Execution patterns using Skills. No manual code writing for production features. All capabilities must be packaged as reusable Skills with executable scripts that AI agents can invoke autonomously.

**Rationale:** This ensures 80-98% token efficiency reduction by using script-based execution rather than verbose context passing. Skills become reusable assets across multiple projects, and development becomes fully autonomous through Claude Code and Goose agents.

### II. Cloud-Native Architecture Mandate

**Non-Negotiable Rule:** All services MUST be containerized microservices deployed on Kubernetes with Dapr for service mesh and Kafka for event-driven messaging. Direct service-to-service communication is prohibited; all inter-service communication MUST use Dapr pub/sub or service invocation patterns.

**Rationale:** Enables scalability, fault tolerance, and autonomous deployment. Dapr abstracts infrastructure concerns, allowing agents to focus on business logic. Kafka ensures reliable asynchronous communication between learning agents and user interfaces.

### III. Token Efficiency & Context Optimization

**Non-Negotiable Rule:** All Skills MUST achieve 80-98% token reduction through MCP Code Execution patterns. Scripts must be the primary execution mechanism, with context window usage minimized through structured I/O and discrete, measurable operations.

**Rationale:** Cost optimization for AI agent operations and ability to work within constrained context windows. Every Skill must demonstrate measurable token efficiency through benchmarking against manual implementation approaches.

### IV. Autonomous Agentic Development

**Non-Negotiable Rule:** All development MUST be executed entirely by AI agents (Claude Code and/or Goose) using provided Skills. Human developers act as architects and teachers, not implementers. Application code for LearnFlow platform must be generated entirely by agents following Skill instructions.

**Rationale:** Demonstrates the paradigm shift from coding to teaching AI agents. Validates that Skills are effective teaching tools. Produces reusable knowledge assets rather than one-off implementations.

## Technology Stack & Standards

### Required Technology Stack

**Frontend:**
- Next.js 14+ with App Router
- Monaco Editor integration for code editing
- TypeScript for type safety
- Tailwind CSS for styling

**Backend Microservices:**
- FastAPI for Python microservices
- OpenAI Agent SDK for tutoring agent orchestration
- Dapr sidecars for all services
- Python 3.11+ runtime

**Infrastructure:**
- Kubernetes (Minikube for development, production clusters for deployment)
- Dapr runtime for service mesh, state management, and pub/sub
- Apache Kafka for event streaming
- Neon PostgreSQL for persistent storage
- Kong API Gateway for routing and JWT authentication
- Argo CD for GitOps deployment

**Development Tools:**
- MCP servers for real-time data access
- Spec-Kit Plus for specification-driven development
- Docusaurus for documentation
- GitHub Actions + Argo CD for CI/CD

### Compliance Standards

- **AAIF Standards:** All Skills and Recipes must comply with Agentic AI Foundation standards for interoperability
- **Container Security:** All images must be scanned and signed
- **API Contracts:** Must follow OpenAPI 3.1 specification
- **Event Schema:** Must use Avro or JSON Schema for Kafka topics

## Development Workflow & Skills Architecture

### Skill Development Lifecycle

1. **Specification Phase:** Create spec.md files using Spec-Kit Plus templates
2. **Planning Phase:** Generate plan.md with architecture decisions and ADRs
3. **Task Creation:** Break into tasks.md with measurable acceptance criteria
4. **Skill Creation:** Write SKILL.md with YAML frontmatter and executable scripts
5. **Agent Execution:** Claude Code or Goose execute Skills to generate code
6. **Validation:** Automated testing of both Skill execution and generated outputs

### Skills Repository Requirements

**Repository Structure:**
```
.claude/skills/
├── agents-md-gen/           # AGENTS.md generation
├── kafka-k8s-setup/         # Kafka deployment on K8s
├── postgres-k8s-setup/      # PostgreSQL deployment
├── fastapi-dapr-agent/      # FastAPI + Dapr service templates
├── nextjs-k8s-deploy/       # Next.js deployment
├── mcp-code-execution/      # MCP pattern implementation
└── docusaurus-deploy/       # Documentation deployment
```

**Each Skill Must Include:**
- SKILL.md with YAML frontmatter (name, description, prerequisites)
- Executable scripts (Python/Shell) for autonomous operation
- Verification scripts for testing execution
- Token efficiency benchmarks
- Cross-agent compatibility (Claude Code + Goose)

### LearnFlow Application Development

**Application Repository Structure:**
```
learnflow-app/
├── frontend/                # Next.js application
├── backend/                 # FastAPI microservices
│   ├── concepts-agent/
│   ├── coding-agent/
│   ├── quiz-agent/
│   └── progress-agent/
├── infrastructure/          # K8s manifests and Helm charts
├── dapr-components/         # Dapr configuration
├── kafka-topics/            # Topic definitions
└── mcp-servers/             # Context providers
```

**Development Rule:** No manual code commits to application repository. All changes must come from agent execution of Skills.

## Governance

### Amendment Procedure

1. **Proposal:** Any team member can propose constitution changes via PR to this document
2. **Review:** Requires approval from 2/3 of core architects
3. **Versioning:** Follow semantic versioning (MAJOR.MINOR.PATCH)
   - MAJOR: Core principle changes or technology stack changes
   - MINOR: New principles or significant workflow additions
   - PATCH: Clarifications, corrections, non-semantic updates
4. **Documentation:** All amendments require corresponding ADRs and template updates
5. **Migration:** Major version changes require migration plan and Skills updates

### Compliance Review

**Weekly Reviews:**
- Verify all new Skills follow token efficiency benchmarks
- Check that application code is 100% agent-generated
- Validate Dapr/Kafka patterns in deployed services
- Review ADRs for architecturally significant decisions

**Gate Requirements:**
- No PR merges without PHR (Prompt History Record) for the work
- All Skills must pass cross-agent testing (Claude Code + Goose)
- Token efficiency must meet 80% reduction target vs manual implementation
- All ADRs must be linked to corresponding Skills or application changes

### Runtime Guidance

**For Agent Development Sessions:**
- Always reference this constitution when making architectural decisions
- Create PHRs for every user interaction (constitution → history/prompts/constitution/)
- Suggest ADRs when architectural decisions impact long-term system design
- Use `/sp.adr <decision-title>` for significant choices (framework, data model, API patterns)

**Skill Execution Guidelines:**
- Skills are the primary product, not the generated application
- Every Skill must demonstrate measurable autonomous execution
- Token efficiency must be benchmarked and documented
- Cross-agent compatibility is mandatory for all Skills

---

**Version**: 2.0.0 | **Ratified**: TODO(2025-01-11) | **Last Amended**: 2025-01-11

**Version Rationale**: MAJOR bump - Complete rewrite from generic template to LearnFlow-specific agentic development constitution with 4 core principles, technology stack requirements, and governance for autonomous development.
