/**
 * Dapr Subscription Management API Route
 * Handles frontend subscriptions to Dapr pub/sub topics
 * Last Updated: 2026-01-15
 * Task: T090
 * Enhanced with request validation (T105)
 */

import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { validateSubscriptionRequest, createValidationErrorResponse } from '@/lib/validation/api-validator';

// Types for subscription management
interface DaprSubscriptionRequest {
  topics: string[];
  studentId: string;
  metadata?: Record<string, string>;
}

interface DaprSubscriptionResponse {
  subscriptionId: string;
  topics: string[];
  studentId: string;
  status: 'active' | 'pending' | 'error';
  createdAt: string;
  metadata?: {
    daprEndpoint: string;
    ttlSeconds: number;
  };
}

interface Subscription {
  id: string;
  topics: string[];
  studentId: string;
  status: 'active' | 'pending' | 'error';
  createdAt: Date;
  lastHeartbeat: Date;
  metadata: {
    daprEndpoint: string;
    ttlSeconds: number;
  };
}

// In-memory subscription store (replace with Redis in production)
const subscriptionStore = new Map<string, Subscription>();

// Dapr configuration
const DAPR_CONFIG = {
  pubsubName: process.env.DAPR_PUBSUB_NAME || 'kafka-pubsub',
  maxSubscriptions: parseInt(process.env.DAPR_MAX_SUBSCRIPTIONS || '100'),
  ttlSeconds: parseInt(process.env.DAPR_TTL_SECONDS || '3600'), // 1 hour default
  endpoint: process.env.DAPR_ENDPOINT || 'http://localhost:3500',
};

/**
 * POST /api/dapr/subscribe
 * Creates a new subscription to Dapr topics for a student
 *
 * Request Body:
 * {
 *   "topics": ["mastery-updated", "feedback-received"],
 *   "studentId": "student-123",
 *   "metadata": { "priority": "high" }
 * }
 *
 * Response:
 * {
 *   "subscriptionId": "sub-uuid",
 *   "topics": ["mastery-updated", "feedback-received"],
 *   "studentId": "student-123",
 *   "status": "active",
 *   "createdAt": "2026-01-15T10:30:00Z",
 *   "metadata": {
 *     "daprEndpoint": "http://localhost:3500",
 *     "ttlSeconds": 3600
 *   }
 * }
 */
export async function POST(request: NextRequest) {
  try {
    // Validate request headers
    const authHeader = headers().get('authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Unauthorized: Missing or invalid JWT token' },
        { status: 401 }
      );
    }

    // Parse and validate request body using validation library
    const rawBody = await request.json().catch((error) => {
      throw new Error(`Invalid JSON: ${error.message}`);
    });
    if (!rawBody) {
      return NextResponse.json(
        { error: 'Bad Request: Invalid JSON body' },
        { status: 400 }
      );
    }

    // Use validation library (T105)
    const validation = validateSubscriptionRequest(rawBody);
    if (!validation.isValid) {
      return createValidationErrorResponse(validation.errors);
    }

    const { topics, studentId, metadata }: DaprSubscriptionRequest = validation.sanitizedData;

    // Check subscription limits (application-level limit)
    const studentSubscriptions = Array.from(subscriptionStore.values())
      .filter(sub => sub.studentId === studentId);

    if (studentSubscriptions.length >= DAPR_CONFIG.maxSubscriptions) {
      return NextResponse.json(
        { error: `Too Many Requests: Maximum ${DAPR_CONFIG.maxSubscriptions} subscriptions per student` },
        { status: 429 }
      );
    }

    // Generate subscription ID
    const subscriptionId = `sub-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Create subscription
    const subscription: Subscription = {
      id: subscriptionId,
      topics: validTopics,
      studentId,
      status: 'active',
      createdAt: new Date(),
      lastHeartbeat: new Date(),
      metadata: {
        daprEndpoint: DAPR_CONFIG.endpoint,
        ttlSeconds: DAPR_CONFIG.ttlSeconds,
      },
    };

    // Store subscription
    subscriptionStore.set(subscriptionId, subscription);

    // In production, you would also call Dapr sidecar to create actual subscriptions
    // await createDaprSubscriptions(validTopics, studentId);

    // Schedule cleanup for expired subscriptions
    setTimeout(() => {
      const sub = subscriptionStore.get(subscriptionId);
      if (sub && Date.now() - sub.lastHeartbeat.getTime() > DAPR_CONFIG.ttlSeconds * 1000) {
        subscriptionStore.delete(subscriptionId);
      }
    }, DAPR_CONFIG.ttlSeconds * 1000);

    const response: DaprSubscriptionResponse = {
      subscriptionId: subscription.id,
      topics: subscription.topics,
      studentId: subscription.studentId,
      status: subscription.status,
      createdAt: subscription.createdAt.toISOString(),
      metadata: {
        daprEndpoint: subscription.metadata.daprEndpoint,
        ttlSeconds: subscription.metadata.ttlSeconds,
      },
    };

    return NextResponse.json(response, {
      status: 201,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      },
    });

  } catch (error) {
    console.error('Dapr subscription error:', error);

    return NextResponse.json(
      {
        error: 'Internal Server Error',
        message: 'Failed to create subscription',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/dapr/subscribe
 * Get active subscriptions for a student
 */
export async function GET(request: NextRequest) {
  try {
    // Validate authentication
    const authHeader = headers().get('authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Unauthorized: Missing or invalid JWT token' },
        { status: 401 }
      );
    }

    // Extract studentId from query parameters
    const { searchParams } = new URL(request.url);
    const studentId = searchParams.get('studentId');

    if (!studentId) {
      return NextResponse.json(
        { error: 'Bad Request: studentId query parameter is required' },
        { status: 400 }
      );
    }

    // Get subscriptions for student
    const subscriptions = Array.from(subscriptionStore.values())
      .filter(sub => sub.studentId === studentId && sub.status === 'active')
      .map(sub => ({
        subscriptionId: sub.id,
        topics: sub.topics,
        status: sub.status,
        createdAt: sub.createdAt.toISOString(),
        lastHeartbeat: sub.lastHeartbeat.toISOString(),
      }));

    return NextResponse.json({
      studentId,
      subscriptions,
      count: subscriptions.length,
      timestamp: new Date().toISOString(),
    }, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store, max-age=0',
      },
    });

  } catch (error) {
    console.error('Error fetching subscriptions:', error);

    return NextResponse.json(
      {
        error: 'Internal Server Error',
        message: 'Failed to fetch subscriptions',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/dapr/subscribe
 * Delete a subscription
 */
export async function DELETE(request: NextRequest) {
  try {
    // Validate authentication
    const authHeader = headers().get('authorization');
    if (!authHeader?.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Unauthorized: Missing or invalid JWT token' },
        { status: 401 }
      );
    }

    // Parse request body
    const body = await request.json().catch(() => null);
    if (!body?.subscriptionId) {
      return NextResponse.json(
        { error: 'Bad Request: subscriptionId is required' },
        { status: 400 }
      );
    }

    const { subscriptionId } = body;

    // Delete subscription
    const deleted = subscriptionStore.delete(subscriptionId);

    if (!deleted) {
      return NextResponse.json(
        { error: 'Not Found: Subscription not found or already deleted' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      message: 'Subscription deleted successfully',
      subscriptionId,
      timestamp: new Date().toISOString(),
    }, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });

  } catch (error) {
    console.error('Error deleting subscription:', error);

    return NextResponse.json(
      {
        error: 'Internal Server Error',
        message: 'Failed to delete subscription',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * Health check endpoint for Dapr subscriptions
 * GET /api/dapr/subscribe/health
 */
export async function HEAD() {
  const subscriptionCount = subscriptionStore.size;

  return new NextResponse(null, {
    status: 200,
    headers: {
      'X-Subscription-Count': subscriptionCount.toString(),
      'X-Dapr-Endpoint': DAPR_CONFIG.endpoint,
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}

/**
 * Helper function to create Dapr subscriptions (placeholder for production)
 * This would call the Dapr sidecar to create actual pub/sub subscriptions
 */
async function createDaprSubscriptions(topics: string[], studentId: string) {
  // In production, this would make HTTP calls to Dapr sidecar:
  // POST http://localhost:3500/subscribe
  // with the subscription configuration

  console.log(`Creating Dapr subscriptions for student ${studentId}:`, topics);

  // Placeholder implementation
  // const daprResponse = await fetch(`${DAPR_CONFIG.endpoint}/subscribe`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({
  //     topic: topic,
  //     route: `/api/dapr/events/${studentId}/${topic}`,
  //     metadata: { studentId }
  //   })
  // });

  return true;
}