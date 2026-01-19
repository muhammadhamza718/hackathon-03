/**
 * Kong Gateway Health Check API Endpoint
 * Checks the health and connectivity of Kong Gateway
 * Last Updated: 2026-01-15
 * Task: T103
 */

import { NextResponse } from 'next/server';

// Kong configuration
const KONG_CONFIG = {
  adminUrl: process.env.KONG_ADMIN_URL || 'http://localhost:8001',
  proxyUrl: process.env.KONG_PROXY_URL || 'http://localhost:8000',
  timeout: parseInt(process.env.KONG_HEALTH_TIMEOUT || '5000'), // 5 seconds
};

interface KongHealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  gateway: {
    reachable: boolean;
    adminUrl: string;
    proxyUrl: string;
    version?: string;
  };
  plugins: {
    total: number;
    enabled: string[];
    jwt?: boolean;
    rateLimiting?: boolean;
    cors?: boolean;
  };
  services: {
    total: number;
    frontendService?: boolean;
  };
  routes: {
    total: number;
    frontendRoutes?: number;
  };
  latency: {
    adminMs: number | null;
    proxyMs: number | null;
  };
  errors: string[];
}

/**
 * GET /api/health/kong
 * Comprehensive health check for Kong Gateway
 */
export async function GET() {
  const startTime = Date.now();
  const healthStatus: KongHealthStatus = {
    status: 'unhealthy',
    timestamp: new Date().toISOString(),
    gateway: {
      reachable: false,
      adminUrl: KONG_CONFIG.adminUrl,
      proxyUrl: KONG_CONFIG.proxyUrl,
    },
    plugins: {
      total: 0,
      enabled: [],
    },
    services: {
      total: 0,
    },
    routes: {
      total: 0,
    },
    latency: {
      adminMs: null,
      proxyMs: null,
    },
    errors: [],
  };

  try {
    // Test 1: Kong Admin API reachability
    const adminStart = Date.now();
    const adminReachable = await testKongAdmin();
    const adminLatency = Date.now() - adminStart;

    healthStatus.gateway.reachable = adminReachable;
    healthStatus.latency.adminMs = adminLatency;

    if (!adminReachable) {
      healthStatus.errors.push('Kong Admin API is not reachable');
      return createHealthResponse(healthStatus);
    }

    // Test 2: Kong Proxy reachability
    const proxyStart = Date.now();
    const proxyReachable = await testKongProxy();
    const proxyLatency = Date.now() - proxyStart;

    healthStatus.latency.proxyMs = proxyLatency;

    // Test 3: Get Kong version and metadata
    const metadata = await getKongMetadata();
    if (metadata) {
      healthStatus.gateway.version = metadata.version;
    }

    // Test 4: Check enabled plugins
    const pluginsStatus = await checkPlugins();
    healthStatus.plugins.total = pluginsStatus.total;
    healthStatus.plugins.enabled = pluginsStatus.enabled;
    healthStatus.plugins.jwt = pluginsStatus.enabled.includes('jwt');
    healthStatus.plugins.rateLimiting = pluginsStatus.enabled.includes('rate-limiting');
    healthStatus.plugins.cors = pluginsStatus.enabled.includes('cors');

    // Test 5: Check services
    const servicesStatus = await checkServices();
    healthStatus.services.total = servicesStatus.total;
    healthStatus.services.frontendService = servicesStatus.frontendService;

    // Test 6: Check routes
    const routesStatus = await checkRoutes();
    healthStatus.routes.total = routesStatus.total;
    healthStatus.routes.frontendRoutes = routesStatus.frontendRoutes;

    // Determine overall status
    const criticalComponents = [
      healthStatus.gateway.reachable,
      healthStatus.plugins.jwt === true,
      healthStatus.plugins.rateLimiting === true,
      healthStatus.services.frontendService === true,
    ];

    const healthyCount = criticalComponents.filter(Boolean).length;

    if (healthyCount === criticalComponents.length) {
      healthStatus.status = 'healthy';
    } else if (healthyCount >= criticalComponents.length / 2) {
      healthStatus.status = 'degraded';
    } else {
      healthStatus.status = 'unhealthy';
    }

  } catch (error) {
    console.error('Kong health check error:', error);
    healthStatus.errors.push(`Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  return createHealthResponse(healthStatus);
}

/**
 * HEAD /api/health/kong
 * Lightweight health check for load balancers
 */
export async function HEAD() {
  try {
    const adminReachable = await testKongAdmin();

    return new NextResponse(null, {
      status: adminReachable ? 200 : 503,
      headers: {
        'X-Kong-Health': adminReachable ? 'healthy' : 'unhealthy',
        'X-Kong-Admin-Url': KONG_CONFIG.adminUrl,
        'Cache-Control': 'no-store, max-age=0',
      },
    });
  } catch (error) {
    return new NextResponse(null, {
      status: 503,
      headers: {
        'X-Kong-Health': 'error',
        'Cache-Control': 'no-store, max-age=0',
      },
    });
  }
}

/**
 * Test Kong Admin API reachability
 */
async function testKongAdmin(): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.adminUrl}/status`, {
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
    console.error('Kong Admin API reachability test failed:', error);
    return false;
  }
}

/**
 * Test Kong Proxy reachability
 */
async function testKongProxy(): Promise<boolean> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.proxyUrl}/status`, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Kong proxy typically returns 404 for root path, but that means it's running
    return response.ok || response.status === 404;

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Kong Proxy reachability test failed:', error);
    return false;
  }
}

/**
 * Get Kong metadata (version, etc.)
 */
async function getKongMetadata(): Promise<{ version: string; database: string } | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.adminUrl}/`, {
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
      database: data.database || 'unknown',
    };

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to get Kong metadata:', error);
    return null;
  }
}

/**
 * Check enabled plugins
 */
async function checkPlugins(): Promise<{ total: number; enabled: string[] }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.adminUrl}/plugins/enabled`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return { total: 0, enabled: [] };
    }

    const data = await response.json();
    const enabled = data.enabled_plugins || [];

    return {
      total: enabled.length,
      enabled,
    };

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to check plugins:', error);
    return { total: 0, enabled: [] };
  }
}

/**
 * Check services
 */
async function checkServices(): Promise<{ total: number; frontendService: boolean }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.adminUrl}/services`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return { total: 0, frontendService: false };
    }

    const data = await response.json();
    const services = data.data || [];
    const frontendService = services.some((s: any) =>
      s.name === 'frontend-service' || s.host === 'frontend-service'
    );

    return {
      total: services.length,
      frontendService,
    };

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to check services:', error);
    return { total: 0, frontendService: false };
  }
}

/**
 * Check routes
 */
async function checkRoutes(): Promise<{ total: number; frontendRoutes: number }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.adminUrl}/routes`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return { total: 0, frontendRoutes: 0 };
    }

    const data = await response.json();
    const routes = data.data || [];

    // Count routes that look like frontend routes
    const frontendRoutes = routes.filter((r: any) => {
      const paths = r.paths || [];
      const hosts = r.hosts || [];
      return paths.some((p: string) => p.includes('frontend') || p.includes('/api/')) ||
             hosts.some((h: string) => h.includes('frontend'));
    }).length;

    return {
      total: routes.length,
      frontendRoutes,
    };

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to check routes:', error);
    return { total: 0, frontendRoutes: 0 };
  }
}

/**
 * Create standardized health response
 */
function createHealthResponse(status: KongHealthStatus): NextResponse {
  const statusCode = status.status === 'healthy' ? 200 : status.status === 'degraded' ? 206 : 503;

  return NextResponse.json(status, {
    status: statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store, max-age=0',
      'X-Kong-Health': status.status,
      'X-Kong-Status-Code': statusCode.toString(),
    },
  });
}

/**
 * Additional utility endpoints
 */

/**
 * GET /api/health/kong/plugins
 * Get detailed information about Kong plugins
 */
export async function GETPlugins() {
  try {
    const plugins = await checkPlugins();
    const pluginDetails = await getPluginDetails();

    return NextResponse.json({
      ...plugins,
      details: pluginDetails,
      timestamp: new Date().toISOString(),
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, max-age=0',
      },
    });

  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to get plugin details',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

/**
 * Get detailed plugin information
 */
async function getPluginDetails(): Promise<any[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), KONG_CONFIG.timeout);

  try {
    const response = await fetch(`${KONG_CONFIG.adminUrl}/plugins`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    return data.data || [];

  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Failed to get plugin details:', error);
    return [];
  }
}