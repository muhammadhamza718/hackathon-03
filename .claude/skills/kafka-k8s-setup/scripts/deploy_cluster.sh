#!/bin/bash
set -e

echo "Deploying Single-Node Kafka Cluster (KRaft Mode)..."
kubectl apply -f https://strimzi.io/examples/latest/kafka/kraft/kafka-single-node.yaml -n kafka

echo "✓ Kafka cluster resource applied."
echo "Note: Use verify.py to check for full readiness."
