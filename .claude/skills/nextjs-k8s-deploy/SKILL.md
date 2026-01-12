---
name: nextjs-k8s-deploy
description: Build and deploy Next.js applications to Kubernetes. Use for LearnFlow frontend deployment.
---

# Next.js Kubernetes Deployment

## When to Use

- User asks to deploy the LearnFlow frontend.
- Containerizing and deploying any Next.js application to a K8s cluster.

## Instructions

1. **Prepare Docker:** Ensure a `Dockerfile` exists in the app root.
2. **Build Image:** Run `./scripts/build.sh <image_name>`.
3. **Deploy:** Execute `./scripts/deploy.sh <image_name> <namespace>`.
4. **Verify:** Check pod and service status using `kubectl get pods,svc -n <namespace>`.

## Validation

- [ ] Deployment pods are Running.
- [ ] Service is created and has an endpoint.

See [REFERENCE.md](./REFERENCE.md) for Dockerfile templates and LoadBalancer setup.
