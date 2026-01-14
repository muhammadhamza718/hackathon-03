# Rollback Procedures

**Elite Implementation Standard v2.0.0**

This document describes the rollback procedures for the Triage Service.

## Quick Rollback (Emergency)

### Immediate Rollback Command

```bash
# Rollback to previous deployment version
kubectl rollout undo deployment/triage-service -n learnflow

# Monitor rollback progress
kubectl rollout status deployment/triage-service -n learnflow --watch

# Check pods are running with old version
kubectl get pods -n learnflow -l app=triage-service
```

### Verification After Rollback

```bash
# Verify health endpoint returns 200
curl -f http://triage-service/health || echo "Health check failed"

# Check Dapr sidecar is healthy
kubectl logs -n learnflow -l app=triage-service -c daprd

# Verify service logs show no errors
kubectl logs -n learnflow -l app=triage-service -c triage-service --tail=50
```

## Version-Based Rollback

### Find Previous Version

```bash
# View deployment history
kubectl rollout history deployment/triage-service -n learnflow

# See detailed revision info
kubectl rollout history deployment/triage-service -n learnflow --revision=2

# Get current image
kubectl get deployment triage-service -n learnflow -o jsonpath='{.spec.template.spec.containers[0].image}'
```

### Specific Version Rollback

```bash
# Rollback to specific revision
kubectl rollout undo deployment/triage-service -n learnflow --to-revision=2

# Or update to specific image tag
kubectl set image deployment/triage-service \
  triage-service=your-registry/triage-service:v1.0.0 \
  -n learnflow
```

## Kong Configuration Rollback

### Backup Current Configuration

```bash
# Export current Kong service config
curl -s http://kong-admin:8001/services/triage-service > kong-service-backup.json

# Export route config
curl -s http://kong-admin:8001/routes/triage-route > kong-route-backup.json

# Export plugin configs
curl -s http://kong-admin:8001/plugins > kong-plugins-backup.json
```

### Restore Kong Configuration

```bash
# Update service
curl -X PATCH http://kong-admin:8001/services/triage-service \
  -d @kong-service-backup.json

# Update route
curl -X PATCH http://kong-admin:8001/routes/triage-route \
  -d @kong-route-backup.json

# Remove plugins and re-add
curl -X DELETE http://kong-admin:8001/plugins/<plugin-id>
curl -X POST http://kong-admin:8001/plugins -d @plugin-config.json
```

## Database Rollback (If Needed)

### PostgreSQL Rollback

```bash
# If using PostgreSQL migrations
# List available migrations
kubectl exec -n learnflow postgres-pod -- psql -U learnflow -d learnflow -c "\dt"

# Check migration history
kubectl exec -n learnflow postgres-pod -- psql -U learnflow -d learnflow -c "SELECT * FROM alembic_version;"

# Rollback to previous version (if using migrations)
kubectl exec -n learnflow postgres-pod -- \
  psql -U learnflow -d learnflow -c "UPDATE alembic_version SET version_num = 'previous_version';"
```

### Data Backup Before Changes

```bash
# Backup triage events table
kubectl exec -n learnflow postgres-pod -- \
  pg_dump -U learnflow learnflow -t triage_events > triage-events-backup.sql

# Backup audit logs
kubectl exec -n learnflow postgres-pod -- \
  pg_dump -U learnflow learnflow -t audit_logs > audit-logs-backup.sql
```

## Dapr Component Rollback

### Backup Dapr Components

```bash
# Export Dapr resiliency config
kubectl get resiliency triage-resiliency -n learnflow -o yaml > dapr-resiliency-backup.yaml

# Export Dapr components
kubectl get components -n learnflow -o yaml > dapr-components-backup.yaml
```

### Restore Dapr Components

```bash
# Apply backup configs
kubectl apply -f dapr-resiliency-backup.yaml
kubectl apply -f dapr-components-backup.yaml

# Restart triage-service to pick up Dapr changes
kubectl rollout restart deployment/triage-service -n learnflow
```

## Complete System Rollback

### Step-by-Step Procedure

1. **Stop New Deployments**
   ```bash
   kubectl rollout pause deployment/triage-service -n learnflow
   ```

2. **Rollback Kubernetes**
   ```bash
   kubectl rollout undo deployment/triage-service -n learnflow
   ```

3. **Rollback Kong**
   ```bash
   # Restore from backups
   curl -X PATCH http://kong-admin:8001/services/triage-service -d @kong-service-backup.json
   ```

4. **Verify Health**
   ```bash
   # Check all components
   ./scripts/verify-triage-logic.py --test-complete-flow
   ```

5. **Resume Monitoring**
   ```bash
   # Check metrics
   curl http://triage-service/metrics
   ```

## Monitoring During Rollback

### Key Metrics to Watch

```bash
# Pod status
kubectl get pods -n learnflow -w -l app=triage-service

# Service endpoints
kubectl get endpoints -n learnflow triage-service

# Dapr status
kubectl get components -n learnflow

# Kong status
curl http://kong-admin:8001/status
```

### Alert Conditions

**Rollback Required When**:
- Error rate > 5% over 5 minutes
- P95 latency > 1000ms
- Circuit breakers open for > 30 seconds
- Authentication failures > 10% of traffic
- Memory usage > 2GB for sustained period

## Emergency Contact

For production incidents requiring immediate rollback:

1. **Primary**: Execute Quick Rollback section above
2. **Secondary**: Contact on-call engineer
3. **Documentation**: Record incident in runbook

## Post-Rollback Actions

### Investigation

```bash
# Collect logs
kubectl logs -n learnflow deployment/triage-service --previous > rollback-logs.txt

# Get events
kubectl get events -n learnflow --sort-by='.lastTimestamp' > rollback-events.txt

# Analyze metrics
# Use Prometheus queries to identify correlation between changes and issues
```

### Reporting

Create incident report with:
- Time of rollback
- Version rolled back from/to
- Root cause analysis
- Impact assessment
- Prevention measures for future

## Prevention

### Best Practices

1. **Always** backup before changes
2. **Always** test rollback procedures in staging
3. **Always** have monitoring in place
4. **Always** deploy during low-traffic periods
5. **Always** have rollback plan before deployment

### Staging Verification

```bash
# Test rollback in staging first
./scripts/verify-rollback.sh --environment=staging
```

**Generated**: 2026-01-13
**Version**: 1.0.0
**Compliance**: Elite Standard v2.0.0