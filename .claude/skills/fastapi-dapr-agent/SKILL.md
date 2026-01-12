---
name: fastapi-dapr-agent
description: Scaffold FastAPI microservices with Dapr sidecars. Use for LearnFlow backend service development.
---

# FastAPI Dapr Agent Scaffolding

## When to Use

- User asks to create a new tutor microservice (Triage, Concepts, etc.).
- Adding Dapr sidecars to existing FastAPI applications.

## Instructions

1. **Scaffold Project:** Run `python3 scripts/scaffold.py <service_name>`.
2. **Add Dapr Components:** Execute `./scripts/apply_dapr_components.sh`.
3. **Verify:** Run `dapr run --app-id <service_name> -- python3 main.py` for local testing.

## Validation

- [ ] FastAPI application starts without errors.
- [ ] Dapr sidecar is successfully initialized (check `dapr list`).

See [REFERENCE.md](./REFERENCE.md) for pub/sub and state management patterns.
