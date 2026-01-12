---
name: postgres-k8s-setup
description: Deploy PostgreSQL on Kubernetes. Use when setting up databases for LearnFlow services.
---

# PostgreSQL Kubernetes Setup

## When to Use

- User asks to deploy PostgreSQL on a Kubernetes cluster.
- Running database migrations or verifying connectivity.

## Instructions

1. **Initialize Namespace:** Run `kubectl create namespace postgres --dry-run=client -o yaml | kubectl apply -f -`.
2. **Deploy Database:** Execute `./scripts/deploy.sh`.
3. **Verify:** Run `python3 scripts/verify.py` to ensure database readiness.

## Validation

- [ ] PostgreSQL deployment/statefulset is Running.
- [ ] Database service is accessible.

See [REFERENCE.md](./REFERENCE.md) for credentials and migration examples.
