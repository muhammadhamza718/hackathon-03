/**
 * Health Check API Endpoint
 * Last Updated: 2026-01-15
 */

import { NextResponse } from 'next/server';

// In-memory store for health check status
const healthStatus = {
  status: 'healthy',
  timestamp: new Date().toISOString(),
  version: process.env.APP_VERSION || '1.0.0',
  environment: process.env.NODE_ENV || 'development',
};

/**
 * GET /api/health
 * Basic health check endpoint
 * Returns 200 OK if service is running
 */
export async function GET() {
  const status = {
    ...healthStatus,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
  };

  return NextResponse.json(status, {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}

/**
 * HEAD /api/health
 * Lightweight health check for load balancers
 */
export async function HEAD() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}