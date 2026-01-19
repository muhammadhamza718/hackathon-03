/**
 * Next.js Middleware for CORS, Security Headers, and Request Processing
 * Implements Kong-compatible CORS configuration (T104)
 * Last Updated: 2026-01-15
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// CORS configuration matching Kong frontend-cors plugin
const CORS_CONFIG = {
  origins: [
    'http://localhost:3000',
    'https://localhost:3000',
    'http://127.0.0.1:3000',
    'https://127.0.0.1:3000',
    // Production domains (uncomment as needed)
    // 'https://app.learnflow.com',
    // 'https://staging.learnflow.com',
  ],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  headers: [
    'Accept',
    'Authorization',
    'Content-Type',
    'X-Requested-With',
    'X-Correlation-ID',
    'X-Request-ID',
    'X-User-ID',
  ],
  exposedHeaders: [
    'X-RateLimit-Limit',
    'X-RateLimit-Remaining',
    'X-RateLimit-Reset',
    'X-Correlation-ID',
    'X-Request-ID',
    'X-Kong-Health',
    'X-Dapr-Health',
  ],
  credentials: true,
  maxAge: 3600,
};

// Security headers configuration
const SECURITY_HEADERS = {
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), clipboard-read=(), clipboard-write=()',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', // HSTS
};

/**
 * Main middleware function
 */
export default async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Apply CORS headers
  applyCORSHeaders(request, response);

  // Apply security headers
  applySecurityHeaders(response);

  // Add correlation ID
  addCorrelationID(request, response);

  // Rate limiting (basic implementation)
  const rateLimitResponse = await checkRateLimit(request);
  if (rateLimitResponse) {
    return rateLimitResponse;
  }

  // Health check shortcut (bypass auth)
  if (request.nextUrl.pathname.startsWith('/api/health/')) {
    return response;
  }

  // Authentication for protected routes
  const authResponse = await checkAuthentication(request);
  if (authResponse) {
    return authResponse;
  }

  return response;
}

/**
 * Apply CORS headers to response
 */
function applyCORSHeaders(request: NextRequest, response: NextResponse) {
  const origin = request.headers.get('origin');

  // Check if origin is allowed
  if (origin && CORS_CONFIG.origins.includes(origin)) {
    response.headers.set('Access-Control-Allow-Origin', origin);
  } else if (CORS_CONFIG.origins.includes('*')) {
    response.headers.set('Access-Control-Allow-Origin', '*');
  }

  // Credentials
  if (CORS_CONFIG.credentials) {
    response.headers.set('Access-Control-Allow-Credentials', 'true');
  }

  // Methods
  response.headers.set('Access-Control-Allow-Methods', CORS_CONFIG.methods.join(', '));

  // Headers
  response.headers.set('Access-Control-Allow-Headers', CORS_CONFIG.headers.join(', '));

  // Exposed headers
  response.headers.set('Access-Control-Expose-Headers', CORS_CONFIG.exposedHeaders.join(', '));

  // Max age
  response.headers.set('Access-Control-Max-Age', CORS_CONFIG.maxAge.toString());
}

/**
 * Apply security headers
 */
function applySecurityHeaders(response: NextResponse) {
  Object.entries(SECURITY_HEADERS).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  // Content Security Policy (CSP)
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com", // Monaco needs unsafe-eval
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self' http://localhost:3500 http://localhost:8000", // Dapr, Kong, API
    "frame-src 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');

  response.headers.set('Content-Security-Policy', csp);
}

/**
 * Add correlation ID to request and response
 */
function addCorrelationID(request: NextRequest, response: NextResponse) {
  // Try to get existing correlation ID from request
  let correlationId = request.headers.get('X-Correlation-ID') || request.headers.get('X-Request-ID');

  // Generate new one if not present
  if (!correlationId) {
    correlationId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Add to response headers
  response.headers.set('X-Correlation-ID', correlationId);
  response.headers.set('X-Request-ID', correlationId);

  // Log the request (in production, send to logging service)
  if (process.env.NODE_ENV !== 'production') {
    console.log(`🌐 ${request.method} ${request.nextUrl.pathname} [${correlationId}]`);
  }
}

/**
 * Basic rate limiting implementation
 * In production, use Redis-based rate limiting
 */
async function checkRateLimit(request: NextRequest): Promise<NextResponse | null> {
  // Skip rate limiting for health checks and GET requests
  if (request.nextUrl.pathname.startsWith('/api/health/') || request.method === 'GET') {
    return null;
  }

  // Rate limiting configuration
  const RATE_LIMIT = {
    requests: 60,
    window: 60 * 1000, // 60 seconds
  };

  const clientIP = request.headers.get('x-forwarded-for') || request.ip || 'unknown';
  const key = `ratelimit:${clientIP}:${request.nextUrl.pathname}`;

  // In production, use Redis to track rate limits
  // For now, we'll use a simple in-memory store (not suitable for production)
  const now = Date.now();

  // This is a placeholder - in production, use Redis with atomic operations
  if (process.env.REDIS_URL) {
    // TODO: Implement Redis-based rate limiting
    return null;
  }

  // Simple in-memory rate limiting (development only)
  if (process.env.NODE_ENV === 'development') {
    return null; // Skip rate limiting in development
  }

  return null; // No rate limiting for this implementation
}

/**
 * Check authentication for protected routes
 */
async function checkAuthentication(request: NextRequest): Promise<NextResponse | null> {
  const path = request.nextUrl.pathname;

  // Public routes that don't require authentication
  const publicRoutes = [
    '/api/health',
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/refresh',
    '/login',
    '/register',
    '/',
  ];

  if (publicRoutes.some(route => path.startsWith(route))) {
    return null;
  }

  // Check for JWT token in cookies or headers
  const token = request.cookies.get('auth_token')?.value ||
                request.cookies.get('jwt')?.value ||
                request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    // For API routes, return JSON error
    if (path.startsWith('/api/')) {
      return NextResponse.json(
        {
          error: 'Unauthorized',
          message: 'Authentication token is required',
          code: 'AUTH_TOKEN_MISSING',
        },
        {
          status: 401,
          headers: {
            'WWW-Authenticate': 'Bearer realm="API", error="invalid_token"',
          },
        }
      );
    }

    // For frontend routes, redirect to login
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // TODO: Add token validation in production
  // For now, we trust the token if it exists
  return null;
}

/**
 * Configuration for middleware routing
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
};