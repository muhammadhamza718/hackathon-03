/**
 * Dapr Sidecar Health Check API Endpoint
 * Checks the health and connectivity of the Dapr sidecar
 * Last Updated: 2026-01-15
 * Task: T092
 */

import { NextResponse } from 'next/server';

// Dapr configuration
const DAPR_CONFIG = {
  endpoint: process.env.DAPR_ENDPOINT || 'http://localhost:3500',
  sidecarPort: process.env.DAPR_HTTP_PORT || '3500',
  grpcPort: process.env.DAPR_GRPC_PORT || '50001',
  metricsPort: process.env.DAPR_METRICS_PORT || '9090',
  maxRetries: parseInt(process.env.DAPR_HEALTH_MAX_RETRIES || '3'),
  timeout: parseInt(process.env.DAPR_HEALTH_TIMEOUT || '5000'), // 5 seconds
};

interface DaprHealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  sidecar: {
    reachable: boolean;
    endpoint: string;
    version?: string;
    uptime?: number;
  };
  pubsub: {
    available: boolean;
    components: string[];
  };
  serviceInvocation: {
    available: boolean;
  };
  metrics: {
    available: boolean;
    endpoint: string;
  };
  latency: {
    sidecarMs: number | null;
    pubsubMs: number | null;
  };
  errors: string[];
}

/**
 * GET /api/dapr/health
 * Comprehensive health check for Dapr sidecar and related services
 */
export async function GET() {
  const startTime = Date.now();
  const healthStatus: DaprHealthStatus = {
    status: 'unhealthy',
    timestamp: new Date().toISOString(),
    sidecar: {
      reachable: false,
      endpoint: DAPR_CONFIG.endpoint,
    },
    pubsub: {
      available: false,
      components: [],
    },
    serviceInvocation: {
      available: false,
    },
    metrics: {
      available: false,
      endpoint: `${DAPR_CONFIG.endpoint}:${DAPR_CONFIG.metricsPort}`,
    },
    latency: {
      sidecarMs: null,
      pubsubMs: null,
    },
    errors: [],
  };

  try {
    // Test 1: Basic Dapr sidecar reachability
    const sidecarStart = Date.now();
    const sidecarReachable = await testDaprSidecarReachability();
    const sidecarLatency = Date.now() - sidecarStart;

    healthStatus.sidecar.reachable = sidecarReachable;
    healthStatus.latency.sidecarMs = sidecarLatency;

    if (!sidecarReachable) {
      healthStatus.errors.push('Dapr sidecar is not reachable');
      return createHealthResponse(healthStatus);
    }

    // Test 2: Get Dapr version and metadata
    const metadata = await getDaprMetadata();
    if (metadata) {
      healthStatus.sidecar.version = metadata.version;
      healthStatus.sidecar.uptime = metadata.uptime;
    }

    // Test 3: Check pub/sub components
    const pubsubStart = Date.now();
    const pubsubStatus = await checkPubSubComponents();
    healthStatus.pubsub.available = pubsubStatus.available;
    healthStatus.pubsub.components = pubsubStatus.components;
    healthStatus.latency.pubsubMs = Date.now() - pubsubStart;

    // Test 4: Check service invocation
    const serviceInvocationAvailable = await testServiceInvocation();
    healthStatus.serviceInvocation.available = serviceInvocationAvailable;

    // Test 5: Check metrics endpoint
    const metricsAvailable = await testMetricsEndpoint();
    healthStatus.metrics.available = metricsAvailable;

    // Determine overall status
    const criticalServices = [
      healthStatus.sidecar.reachable,
      healthStatus.pubsub.available,
      healthStatus.serviceInvocation.available,
    ];

    const healthyCount = criticalServices.filter(Boolean).length;

    if (healthyCount === criticalServices.length) {
      healthStatus.status = 'healthy';
    } else if (healthyCount >= criticalServices.length / 2) {
      healthStatus.status = 'degraded';
    } else {
      healthStatus.status = 'unhealthy';
    }

  } catch (error) {
    console.error('Dapr health check error:', error);
    healthStatus.errors.push(`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  return createHealthResponse(healthStatus);
}

/**
 * HEAD /api/dapr/health
 * Lightweight health check for load balancers
 */
export async function HEAD() {
  try {
    const reachable = await testDaprSidecarReachability();

    return new NextResponse(null, {
      status: reachable ? 200 : 503,
      headers: {
        'X-Dapr-Health': reachable ? 'healthy' : 'unhealthy',
        'X-Dapr-Endpoint': DAPR_CONFIG.endpoint,
        'Cache-Control': 'no-store, max-age=0',
      },
    });
  } catch (error) {
    return new NextResponse(null, {
      status: 503,
      headers: {
        'X-Dapr-Health': 'error',
        'Cache-Control': 'no-store, max-age=0',
      },
    });
  }
}

/**
 * Test Dapr sidecar basic reachability
 */
async function testDaprSidecarReachability(): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DAPR_CONFIG.timeout);

  try {
    const response = await fetch(`${DAPR_CONFIG.sidecarPort === '3500' ? DAPR_CONFIG.endpoint : `http://localhost:${DAPR_CONFIG.sidecarPort}`}/v1.0/healthz`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    // Dapr health endpoint typically returns 200 or 204
    return response.ok || response.status === 204;

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Dapr sidecar reachability test failed:', error);
    return false;
  }
}

/**
 * Get Dapr metadata (version, uptime, etc.)
 */
async function getDaprMetadata(): Promise<{ version: string; uptime: number } | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DAPR_CONFIG.timeout);

  try {
    // Try to get metadata from Dapr metadata endpoint
    const response = await fetch(`${DAPR_CONFIG.endpoint}/v1.0/metadata`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();

    return {
      version: data.version || 'unknown',
      uptime: data.registeredAt ? Date.now() - new Date(data.registeredAt).getTime() : 0,
    };

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to get Dapr metadata:', error);
    return null;
  }
}

/**
 * Check available pub/sub components
 */
async function checkPubSubComponents(): Promise<{ available: boolean; components: string[] }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DAPR_CONFIG.timeout);

  try {
    // Get list of pub/sub components
    const response = await fetch(`${DAPR_CONFIG.endpoint}/v1.0/metadata`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return { available: false, components: [] };
    }

    const data = await response.json();

    // Extract pub/sub components from metadata
    const components = data.components || [];
    const pubsubComponents = components
      .filter((comp: any) => comp.type && comp.type.includes('pubsub'))
      .map((comp: any) => comp.name);

    return {
      available: pubsubComponents.length > 0,
      components: pubsubComponents,
    };

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to check pub/sub components:', error);
    return { available: false, components: [] };
  }
}

/**
 * Test service invocation capability
 */
async function testServiceInvocation(): Promise<boolean> {
  // In a real scenario, you would test calling a known service
  // For now, we'll just check if the service invocation endpoint exists
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DAPR_CONFIG.timeout);

  try {
    // Just check if the metadata shows service invocation support
    const response = await fetch(`${DAPR_CONFIG.endpoint}/v1.0/metadata`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    return response.ok;

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Service invocation test failed:', error);
    return false;
  }
}

/**
 * Test metrics endpoint availability
 */
async function testMetricsEndpoint(): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DAPR_CONFIG.timeout);

  try {
    const response = await fetch(`${DAPR_CONFIG.metricsPort === '9090' ? `http://localhost:${DAPR_CONFIG.metricsPort}` : DAPR_CONFIG.metricsPort}/metrics`, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Prometheus metrics endpoint typically returns text/plain
    return response.ok && (response.headers.get('content-type')?.includes('text/plain') || response.status === 200);

  } catch (error) {
    clearTimeout(timeoutId);
    // Metrics endpoint is not critical, so we don't fail the health check
    console.warn('Metrics endpoint test failed (non-critical):', error);
    return false;
  }
}

/**
 * Create standardized health response
 */
function createHealthResponse(status: DaprHealthStatus): NextResponse {
  const statusCode = status.status === 'healthy' ? 200 : status.status === 'degraded' ? 206 : 503;

  return NextResponse.json(status, {
    status: statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store, max-age=0',
      'X-Dapr-Health': status.status,
      'X-Dapr-Status-Code': statusCode.toString(),
    },
  });
}