# Kafka on K8s Reference Guide

## Strimzi Operator

The Strimzi operator simplifies running Kafka on Kubernetes by using Custom Resource Definitions (CRDs).

### Installation Details

The operator is installed using the latest stable manifests from Strimzi.io into the `kafka` namespace.

## Topic Management

### Create Topic via CRD

```yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: learnflow-events
  namespace: kafka
  labels:
    strimzi.io/cluster: my-cluster
spec:
  partitions: 3
  replicas: 1
```

## Troubleshooting

### Check Logs

- **Operator:** `kubectl logs deployment/strimzi-cluster-operator -n kafka`
- **Kafka:** `kubectl logs my-cluster-kafka-0 -n kafka`

### Common Issues

- **PVC Pending:** Ensure a StorageClass is available in the cluster (e.g., standard on Minikube).
- **Insufficient Memory:** Minikube needs at least 8GB RAM for a stable Kafka setup.

## Dapr Integration

Bootstrap Server for Dapr Pub/Sub:
`my-cluster-kafka-bootstrap.kafka.svc.cluster.local:9092`
