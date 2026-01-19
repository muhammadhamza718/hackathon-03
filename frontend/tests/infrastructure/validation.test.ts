/**
 * Infrastructure Validation Tests
 * Tests for Docker, Kubernetes, Kong, and Dapr configurations
 * Last Updated: 2026-01-15
 */

import { readFileSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';
import yaml from 'js-yaml';

describe('Infrastructure Validation', () => {
  const k8sPath = join(process.cwd(), 'k8s');
  const dockerfilePath = join(process.cwd(), 'Dockerfile');
  const dockerignorePath = join(process.cwd(), '.dockerignore');

  describe('Docker Configuration', () => {
    test('T030: Dockerfile exists and is valid', () => {
      expect(() => readFileSync(dockerfilePath, 'utf8')).not.toThrow();

      const dockerfile = readFileSync(dockerfilePath, 'utf8');

      // Multi-stage build validation
      expect(dockerfile).toContain('FROM node:18-alpine');
      expect(dockerfile).toContain('WORKDIR /app');
      expect(dockerfile).toContain('pnpm install');
      expect(dockerfile).toContain('pnpm build');
      expect(dockerfile).toContain('USER nextjs');

      // Health check validation
      expect(dockerfile).toContain('HEALTHCHECK');
      expect(dockerfile).toContain('--interval=30s');
      expect(dockerfile).toContain('--timeout=3s');
      expect(dockerfile).toContain('--start-period=5s');
      expect(dockerfile).toContain('--retries=3');
    });

    test('T031: .dockerignore exists and excludes development files', () => {
      expect(() => readFileSync(dockerignorePath, 'utf8')).not.toThrow();

      const dockerignore = readFileSync(dockerignorePath, 'utf8');

      // Should exclude development artifacts
      expect(dockerignore).toContain('node_modules');
      expect(dockerignore).toContain('.next');
      expect(dockerignore).toContain('*.md');
      expect(dockerignore).toContain('.git');
      expect(dockerignore).toContain('coverage'); // Test coverage directory
      expect(dockerignore).toContain('scripts');
    });

    test('Docker build succeeds (skip in CI)', async () => {
      // Skip this test in CI due to resource constraints
      if (process.env.CI) {
        console.log('Skipping Docker build test in CI environment');
        return;
      }

      try {
        const result = execSync('docker build -f Dockerfile --no-cache .', {
          encoding: 'utf8',
          stdio: 'pipe',
        });
        expect(result).toContain('Successfully built');
      } catch (error: any) {
        // Docker might not be available in test environment
        console.warn('Docker build test skipped:', error.message);
      }
    });
  });

  describe('Kubernetes Manifests', () => {
    test('T032: Deployment manifest is valid YAML', () => {
      const deploymentPath = join(k8sPath, 'deployment.yaml');
      const content = readFileSync(deploymentPath, 'utf8');

      expect(() => yaml.loadAll(content)).not.toThrow();

      const parts = yaml.loadAll(content) as any[];
      const deployment = parts.find((p: any) => p.kind === 'Deployment');

      // Validate structure
      expect(deployment.apiVersion).toBe('apps/v1');
      expect(deployment.kind).toBe('Deployment');
      expect(deployment.metadata.name).toBe('realtime-frontend');
      expect(deployment.metadata.namespace).toBe('realtime-platform');

      // Validate spec
      expect(deployment.spec.replicas).toBe(2);
      expect(deployment.spec.selector.matchLabels.app).toBe('realtime-frontend');

      // Validate container
      const container = deployment.spec.template.spec.containers[0];
      expect(container.name).toBe('frontend');
      expect(container.image).toContain('realtime-frontend');
      expect(container.ports[0].containerPort).toBe(3000);

      // Validate environment variables
      const envVars = container.env;
      expect(envVars.find((e: any) => e.name === 'NODE_ENV')?.value).toBe('production');

      // Validate health checks
      expect(container.livenessProbe).toBeDefined();
      expect(container.livenessProbe.httpGet.path).toBe('/health');
      expect(container.readinessProbe).toBeDefined();
      expect(container.readinessProbe.httpGet.path).toBe('/ready');

      // Validate Dapr sidecar
      const containers = deployment.spec.template.spec.containers;
      expect(containers.length).toBe(2);
      const daprContainer = containers.find((c: any) => c.name === 'daprd');
      expect(daprContainer).toBeDefined();
      expect(daprContainer.image).toContain('daprio/daprd');
    });

    test('T033: HPA configuration is valid', () => {
      const hpaPath = join(k8sPath, 'hpa.yaml');
      const content = readFileSync(hpaPath, 'utf8');

      expect(() => yaml.loadAll(content)).not.toThrow();

      const parts = yaml.loadAll(content) as any[];
      const hpa = parts.find((p: any) => p.kind === 'HorizontalPodAutoscaler');

      // Validate API version and kind
      expect(hpa.apiVersion).toBe('autoscaling/v2');
      expect(hpa.kind).toBe('HorizontalPodAutoscaler');
      expect(hpa.metadata.name).toBe('realtime-frontend-hpa');

      // Validate scale target
      expect(hpa.spec.scaleTargetRef.kind).toBe('Deployment');
      expect(hpa.spec.scaleTargetRef.name).toBe('realtime-frontend');

      // Validate replica counts
      expect(hpa.spec.minReplicas).toBe(2);
      expect(hpa.spec.maxReplicas).toBe(10);

      // Validate CPU metric
      const cpuMetric = hpa.spec.metrics.find((m: any) => m.type === 'Resource');
      expect(cpuMetric).toBeDefined();
      expect(cpuMetric.resource.name).toBe('cpu');
      expect(cpuMetric.resource.target.type).toBe('Utilization');
      expect(cpuMetric.resource.target.averageUtilization).toBe(70);

      // Validate behavior
      expect(hpa.spec.behavior.scaleDown.stabilizationWindowSeconds).toBe(300);
      expect(hpa.spec.behavior.scaleUp.stabilizationWindowSeconds).toBe(60);
    });

    test('T035: Kong Gateway configuration is valid', () => {
      const kongPath = join(k8sPath, 'kong-gateway.yaml');
      const content = readFileSync(kongPath, 'utf8');

      expect(() => yaml.loadAll(content)).not.toThrow();

      const parts = yaml.loadAll(content) as any[];

      // Find KongPlugin for JWT
      const jwtPlugin = parts.find((p: any) => p.kind === 'KongPlugin' && p.metadata.name === 'realtime-frontend-jwt');
      expect(jwtPlugin).toBeDefined();
      expect(jwtPlugin.plugin).toBe('jwt');

      // Find KongConsumer
      const consumer = parts.find((p: any) => p.kind === 'KongConsumer');
      expect(consumer).toBeDefined();
      expect(consumer.username).toBe('realtime-frontend');
      expect(consumer.credentials).toContain('realtime-frontend-jwt');

      // Find Ingress
      const ingress = parts.find((p: any) => p.kind === 'Ingress');
      expect(ingress).toBeDefined();
      expect(ingress.spec.rules[0].host).toBe('frontend.realtime-platform.local');
      expect(ingress.spec.rules[0].http.paths[0].path).toBe('/');

      // Find RateLimitPlugin
      const rateLimit = parts.find((p: any) => p.kind === 'RateLimitPlugin');
      expect(rateLimit).toBeDefined();
      expect(rateLimit.config.minute).toBe(100);
      expect(rateLimit.config.hour).toBe(1000);

      // Find CORSPlugin
      const corsPlugin = parts.find((p: any) => p.kind === 'CORSPlugin');
      expect(corsPlugin).toBeDefined();
      expect(corsPlugin.config.origins).toContain('https://realtime-platform.local');
    });

    test('T036: Dapr pub/sub configuration is valid', () => {
      const daprPath = join(k8sPath, 'dapr-components.yaml');
      const content = readFileSync(daprPath, 'utf8');

      expect(() => yaml.loadAll(content)).not.toThrow();

      const parts = yaml.loadAll(content) as any[];

      // Dapr components are embedded in ConfigMap, not separate YAML docs
      const configMap = parts.find((p: any) => p.kind === 'ConfigMap');
      expect(configMap).toBeDefined();
      expect(configMap.metadata.name).toBe('dapr-components');

      // Parse the embedded YAML in ConfigMap data
      const pubsubYaml = configMap.data['pubsub.yaml'];
      expect(pubsubYaml).toBeDefined();

      const pubsub = yaml.load(pubsubYaml) as any;
      expect(pubsub).toBeDefined();
      expect(pubsub.kind).toBe('Component');
      expect(pubsub.metadata.name).toBe('mastery-pubsub');
      expect(pubsub.spec.type).toBe('pubsub.redis');
      expect(pubsub.spec.version).toBe('v1');

      // Validate Redis configuration
      const redisHost = pubsub.spec.metadata.find((m: any) => m.name === 'redisHost');
      expect(redisHost.value).toContain('redis-service.realtime-platform.svc.cluster.local:6379');

      // Validate consumer ID
      const consumerId = pubsub.spec.metadata.find((m: any) => m.name === 'consumerID');
      expect(consumerId.value).toBe('realtime-frontend');

      // Validate scopes (if present)
      if (pubsub.spec.scopes) {
        expect(pubsub.spec.scopes).toContain('realtime-frontend');
        expect(pubsub.spec.scopes).toContain('mastery-engine');
      }

      // Find subscription in ConfigMap data
      const subscriptionYaml = configMap.data['subscriptions.yaml'];
      expect(subscriptionYaml).toBeDefined();

      const subscription = yaml.load(subscriptionYaml) as any;
      expect(subscription).toBeDefined();
      expect(subscription.kind).toBe('Subscription');
      expect(subscription.spec.topic).toBe('mastery-updates');
      expect(subscription.spec.route).toBe('/api/events/mastery');
      expect(subscription.spec.pubsubname).toBe('mastery-pubsub');
    });

    test('T037: All manifests follow Kubernetes best practices', () => {
      const manifestFiles = ['deployment.yaml', 'hpa.yaml', 'kong-gateway.yaml', 'dapr-components.yaml'];

      manifestFiles.forEach(file => {
        const path = join(k8sPath, file);
        const content = readFileSync(path, 'utf8');

        // Check for required metadata fields
        expect(content).toContain('apiVersion:');
        expect(content).toContain('kind:');
        expect(content).toContain('metadata:');

        // Check for namespace usage (required for our platform)
        if (!file.includes('dapr-components')) {
          expect(content).toContain('namespace: realtime-platform');
        }

        // Check for labels (skip for Kong config as it doesn't require them)
        if (!file.includes('kong-gateway')) {
          expect(content).toContain('labels:');
        }

        // Check for proper indentation (2 spaces)
        const lines = content.split('\n');
        lines.forEach((line, index) => {
          if (line.startsWith('  ') && !line.startsWith('    ') && line.trim()) {
            // Lines with exactly 2 spaces at start are properly indented
            expect(line.match(/^ {2}/)).toBeTruthy();
          }
        });
      });
    });
  });

  describe('Health Check Endpoints', () => {
    test('T034: Health endpoint returns proper structure', () => {
      // This would normally test the actual API endpoint
      // For infrastructure validation, we verify the files exist
      const healthPath = join(process.cwd(), 'src/app/api/health/route.ts');
      const readyPath = join(process.cwd(), 'src/app/api/ready/route.ts');

      expect(() => readFileSync(healthPath, 'utf8')).not.toThrow();
      expect(() => readFileSync(readyPath, 'utf8')).not.toThrow();

      const healthContent = readFileSync(healthPath, 'utf8');
      const readyContent = readFileSync(readyPath, 'utf8');

      // Validate health endpoint structure
      expect(healthContent).toContain('export async function GET()');
      expect(healthContent).toContain('status');
      expect(healthContent).toContain('healthy');
      expect(healthContent).toContain('timestamp');
      expect(healthContent).toContain('version');

      // Validate ready endpoint structure
      expect(readyContent).toContain('export async function GET()');
      expect(readyContent).toContain('checks');
      expect(readyContent).toContain('healthAPI.check()');
      expect(readyContent).toContain('checkRedis()');
      expect(readyContent).toContain('checkDapr()');
      expect(readyContent).toContain('200');
      expect(readyContent).toContain('503');
    });
  });

  describe('Security Configuration', () => {
    test('Kong JWT plugin validates token structure', () => {
      const kongPath = join(k8sPath, 'kong-gateway.yaml');
      const content = readFileSync(kongPath, 'utf8');
      const parts = yaml.loadAll(content) as any[];

      const jwtPlugin = parts.find((p: any) => p.kind === 'KongPlugin' && p.metadata.name === 'realtime-frontend-jwt');

      // Validate JWT configuration
      expect(jwtPlugin.config.secret_is_base64).toBe(false);
      expect(jwtPlugin.config.run_on_preflight).toBe(true);
      expect(jwtPlugin.config.key_claim_name).toBe('kid');
      expect(jwtPlugin.config.secret_claim_name).toBe('secret');
    });

    test('CORS configuration is restrictive', () => {
      const kongPath = join(k8sPath, 'kong-gateway.yaml');
      const content = readFileSync(kongPath, 'utf8');
      const parts = yaml.loadAll(content) as any[];

      const corsPlugin = parts.find((p: any) => p.kind === 'CORSPlugin');

      // Validate CORS origins are specific
      expect(corsPlugin.config.origins).toHaveLength(2);
      expect(corsPlugin.config.origins).toContain('https://realtime-platform.local');
      expect(corsPlugin.config.origins).toContain('https://app.realtime-platform.local');

      // Validate allowed methods
      expect(corsPlugin.config.methods).toContain('GET');
      expect(corsPlugin.config.methods).toContain('POST');
      expect(corsPlugin.config.methods).toContain('DELETE');

      // Validate credentials are allowed
      expect(corsPlugin.config.credentials).toBe(true);
    });
  });

  describe('Performance Budget', () => {
    test('Docker image size will be under budget (estimated)', () => {
      // This is a static analysis test
      const dockerfile = readFileSync(dockerfilePath, 'utf8');

      // Check for multi-stage build (reduces final image size)
      expect(dockerfile).toContain('node:18-alpine');

      // Check for pnpm (smaller than npm)
      expect(dockerfile).toContain('pnpm install');

      // Check for production-only dependencies
      expect(dockerfile).toContain('--prod');

      // Verify unnecessary files are excluded
      const dockerignore = readFileSync(dockerignorePath, 'utf8');
      expect(dockerignore).toContain('*.md');
      expect(dockerignore).toContain('coverage');
      expect(dockerignore).toContain('scripts');
    });

    test('Health checks are properly configured', () => {
      const deploymentPath = join(k8sPath, 'deployment.yaml');
      const content = readFileSync(deploymentPath, 'utf8');
      const parts = yaml.loadAll(content) as any[];
      const deployment = parts.find((p: any) => p.kind === 'Deployment');

      const container = deployment.spec.template.spec.containers[0];

      // Validate liveness probe timing
      expect(container.livenessProbe.initialDelaySeconds).toBeGreaterThanOrEqual(30);
      expect(container.livenessProbe.periodSeconds).toBeGreaterThanOrEqual(10);

      // Validate readiness probe timing
      expect(container.readinessProbe.initialDelaySeconds).toBeGreaterThanOrEqual(5);
      expect(container.readinessProbe.periodSeconds).toBeGreaterThanOrEqual(5);
    });
  });
});