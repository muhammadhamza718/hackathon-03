#!/bin/bash
set -e

echo "Deploying PostgreSQL StatefulSet..."

# In a real scenario, this would apply a manifest or a Helm chart
# For this skill, we simulate a basic deployment
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: postgres
spec:
  serviceName: "postgres"
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_PASSWORD
          value: "password"
        ports:
        - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: postgres
spec:
  selector:
    app: postgres
  ports:
    - protocol: TCP
      port: 5432
EOF

echo "✓ PostgreSQL deployment applied."
