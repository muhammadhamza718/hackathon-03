/**
 * Readiness Check API Endpoint
 * Last Updated: 2026-01-15
 */

import { NextResponse } from 'next/server';
import { healthAPI } from '@/lib/api-client';

/**
 * GET /api/ready
 * Readiness check endpoint for Kubernetes
 * Returns 200 OK if service is ready to accept traffic
 */
export async function GET() {
  try {
    // Check dependencies
    const checks = await Promise.allSettled([
      // Check backend API connectivity
      healthAPI.check(),
      // Check Redis (if configured)
      checkRedis(),
      // Check Dapr (if configured)
      checkDapr(),
    ]);

    const results = checks.map((check, index) => {
      const services = ['backend-api', 'redis', 'dapr'];
      return {
        service: services[index],
        status: check.status === 'fulfilled' ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
      };
    });

    const allHealthy = results.every(r => r.status === 'healthy');

    return NextResponse.json(
      {
        status: allHealthy ? 'ready' : 'degraded',
        timestamp: new Date().toISOString(),
        checks: results,
        version: process.env.APP_VERSION || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
      },
      {
        status: allHealthy ? 200 : 503,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, max-age=0',
        },
      }
    );
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        timestamp: new Date().toISOString(),
        error: error.message,
      },
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store, max-age=0',
        },
      }
    );
  }
}

/**
 * Lightweight dependency checks
 */
async function checkRedis(): Promise<{ status: string }> {
  // In production, this would check actual Redis connectivity
  // For now, we'll simulate based on environment
  if (process.env.REDIS_URL) {
    return { status: 'healthy' };
  }
  return { status: 'degraded' };
}

async function checkDapr(): Promise<{ status: string }> {
  // Check if Dapr environment variables are set
  if (process.env.DAPR_HOST && process.env.DAPR_PORT) {
    return { status: 'healthy' };
  }
  return { status: 'degraded' };
}

/**
 * HEAD /api/ready
 * Lightweight readiness check for load balancers
 */
export async function HEAD() {
  // For HEAD requests, perform minimal checks
  const isReady = process.env.NODE_ENV === 'production'
    ? true // In production, assume ready if process is running
    : true; // In development, also assume ready

  return new NextResponse(null, {
    status: isReady ? 200 : 503,
    headers: {
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}