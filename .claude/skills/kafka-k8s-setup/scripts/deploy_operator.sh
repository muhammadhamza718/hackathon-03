#!/bin/bash
set -e

echo "Installing Strimzi Cluster Operator..."
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

echo "Waiting for Strimzi Operator to be available..."
kubectl wait deployment/strimzi-cluster-operator --for=condition=Available -n kafka --timeout=300s

echo "✓ Strimzi Operator is ready."
