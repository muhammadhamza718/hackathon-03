#!/bin/bash
IMAGE_NAME=$1
NAMESPACE=$2

if [ -z "$IMAGE_NAME" ] || [ -z "$NAMESPACE" ]; then
  echo "Usage: ./deploy.sh <image_name> <namespace>"
  exit 1
fi

echo "Creating Deployment for $IMAGE_NAME in $NAMESPACE..."

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: learnflow-frontend
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: learnflow-frontend
  template:
    metadata:
      labels:
        app: learnflow-frontend
    spec:
      containers:
      - name: frontend
        image: $IMAGE_NAME
        ports:
        - containerPort: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: learnflow-frontend
  namespace: $NAMESPACE
spec:
  selector:
    app: learnflow-frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: LoadBalancer
EOF

echo "✓ Deployment and Service applied."
