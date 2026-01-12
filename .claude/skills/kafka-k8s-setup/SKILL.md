---
name: kafka-k8s-setup
description: Deploys Apache Kafka on Kubernetes via Strimzi operator. Use when setting up event-driven microservices or message queuing on K8s.
---

# Kafka Kubernetes Setup

## When to Use

- User asks to deploy Kafka on a Kubernetes cluster.
- Setting up messaging for LearnFlow microservices.

## Instructions

1. **Initialize Namespace:** Run `kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -`.
2. **Deploy Operator:** Execute `./scripts/deploy_operator.sh`.
3. **Deploy Cluster:** Once operator is ready, execute `./scripts/deploy_cluster.sh`.
4. **Verify:** Run `python3 scripts/verify.py` to ensure cluster readiness.

## Validation

- [ ] Strimzi Cluster Operator pod is Running.
- [ ] Kafka cluster (`my-cluster`) pods are Running.
- [ ] Kafka custom resource status is "Ready".

See [REFERENCE.md](./REFERENCE.md) for troubleshooting, manual topic management, and production configurations.
