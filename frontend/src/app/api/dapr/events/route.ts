/**
 * Dapr Event Processing API Route
 * Receives events from Dapr pub/sub and routes them to SSE clients
 * Last Updated: 2026-01-15
 * Task: T093
 */

import { NextRequest, NextResponse } from 'next/server';
import { transformDaprEvent } from '@/lib/dapr/transformer';

// Event types and interfaces
interface DaprEvent {
  id: string;
  source: string;
  type: string;
  specversion: string;
  datacontenttype?: string;
  data: any;
  timestamp?: string;
  metadata?: Record<string, string>;
}

interface ProcessedEvent {
  id: string;
  topic: string;
  type: 'mastery-updated' | 'feedback-received' | 'learning-recommendation' | 'progress-submitted';
  data: any;
  priority: 'high' | 'normal' | 'low';
  timestamp: string;
  metadata: {
    source: string;
    rawPayload?: string;
    studentId?: string;
    daprEventId: string;
  };
}

// SSE connection manager (in-memory for now, should be Redis in production)
const sseConnections = new Map<string, SSEConnection>();

interface SSEConnection {
  studentId: string;
  topics: Set<string>;
  lastHeartbeat: Date;
  connection: ReadableStreamDefaultController | null;
}

/**
 * POST /api/dapr/events
 * Receive events from Dapr pub/sub and route to SSE clients
 * This is the webhook endpoint that Dapr will call when events are published
 * Implements proper event acknowledgment (T095)
 */
export async function POST(request: NextRequest) {
  const startTime = Date.now();
  const correlationId = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  try {
    // Verify Dapr signature (in production, you'd validate the request)
    const signature = request.headers.get('dapr-signature');
    const daprStatus = request.headers.get('dapr-status');

    if (!signature && process.env.NODE_ENV === 'success') {
      return createDaprResponse(correlationId, {
        status: 'failure',
        error: 'Unauthorized: Missing Dapr signature',
        statusCode: 401,
        processingTime: Date.now() - startTime,
      });
    }

    // Parse the Dapr event
    const rawEvent = await request.json().catch((error) => {
      throw new Error(`Invalid JSON: ${error.message}`);
    });

    if (!rawEvent) {
      return createDaprResponse(correlationId, {
        status: 'failure',
        error: 'Bad Request: Invalid event payload',
        statusCode: 400,
        processingTime: Date.now() - startTime,
      });
    }

    // Validate Dapr event structure
    const validationError = validateDaprEvent(rawEvent);
    if (validationError) {
      return createDaprResponse(correlationId, {
        status: 'failure',
        error: validationError,
        statusCode: 400,
        processingTime: Date.now() - startTime,
        eventId: rawEvent.id,
      });
    }

    // Log received event for debugging
    console.log(`📨 Dapr event received [${correlationId}]:`, {
      id: rawEvent.id,
      type: rawEvent.type,
      source: rawEvent.source,
      timestamp: rawEvent.timestamp,
    });

    // Process and transform the event
    const processedEvent = transformDaprEvent(rawEvent);

    if (!processedEvent) {
      return createDaprResponse(correlationId, {
        status: 'failure',
        error: 'Event transformation failed',
        statusCode: 400,
        processingTime: Date.now() - startTime,
        eventId: rawEvent.id,
      });
    }

    // Route event to appropriate SSE connections
    const routingResult = await routeEventToSSE(processedEvent);

    // Create acknowledgment based on routing result
    const acknowledgment = createEventAcknowledgment(
      correlationId,
      rawEvent,
      processedEvent,
      routingResult,
      Date.now() - startTime
    );

    // Return acknowledgment to Dapr
    return createDaprResponse(correlationId, acknowledgment);

  } catch (error) {
    console.error(`[${correlationId}] Error processing Dapr event:`, error);

    return createDaprResponse(correlationId, {
      status: 'failure',
      error: 'Internal Server Error',
      message: error instanceof Error ? error.message : 'Unknown error',
      statusCode: 500,
      processingTime: Date.now() - startTime,
    });
  }
}


/**
 * Map Dapr event types to frontend event types
 */
function mapDaprTypeToFrontendType(daprType: string): ProcessedEvent['type'] | null {
  const mapping: Record<string, ProcessedEvent['type']> = {
    'mastery.updated': 'mastery-updated',
    'mastery_update': 'mastery-updated',
    'feedback.received': 'feedback-received',
    'feedback_received': 'feedback-received',
    'learning.recommendation': 'learning-recommendation',
    'learning_recommendation': 'learning-recommendation',
    'progress.submitted': 'progress-submitted',
    'progress_submitted': 'progress-submitted',
  };

  // Try direct mapping
  if (mapping[daprType]) {
    return mapping[daprType];
  }

  // Try converting snake_case or camelCase to our format
  const normalized = daprType.toLowerCase().replace(/[_-]/g, '.');
  if (mapping[normalized]) {
    return mapping[normalized];
  }

  return null;
}

/**
 * Determine event priority based on event content
 */
function determineEventPriority(daprEvent: DaprEvent): 'high' | 'normal' | 'low' {
  // High priority events
  if (
    daprEvent.type.includes('critical') ||
    daprEvent.data?.priority === 'high' ||
    daprEvent.data?.urgency === 'high' ||
    daprEvent.data?.severity === 'error'
  ) {
    return 'high';
  }

  // Low priority events
  if (
    daprEvent.type.includes('info') ||
    daprEvent.data?.priority === 'low' ||
    daprEvent.data?.urgency === 'low'
  ) {
    return 'low';
  }

  // Default to normal
  return 'normal';
}


/**
 * Count connections that would receive this event
 */
function countRoutedConnections(event: ProcessedEvent): number {
  let count = 0;
  for (const connection of sseConnections.values()) {
    if (connection.topics.has(event.topic)) {
      if (!event.metadata.studentId || connection.studentId === event.metadata.studentId) {
        count++;
      }
    }
  }
  return count;
}

/**
 * SSE Stream endpoint - clients connect here to receive events
 * GET /api/dapr/events/stream
 */
export async function GET(request: NextRequest) {
  // Extract student ID from query params or auth token
  const { searchParams } = new URL(request.url);
  const studentId = searchParams.get('studentId');

  if (!studentId) {
    return NextResponse.json(
      { error: 'studentId query parameter is required' },
      { status: 400 }
    );
  }

  // Get subscribed topics from query params
  const topicsParam = searchParams.get('topics') || '';
  const topics = topicsParam.split(',').filter(t => t.trim());

  if (topics.length === 0) {
    return NextResponse.json(
      { error: 'At least one topic must be specified' },
      { status: 400 }
    );
  }

  // Generate connection ID
  const connectionId = `sse-${studentId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Create SSE stream
  const stream = new ReadableStream({
    start(controller) {
      // Store connection
      sseConnections.set(connectionId, {
        studentId,
        topics: new Set(topics),
        lastHeartbeat: new Date(),
        connection: controller,
      });

      console.log(`🔗 SSE connection established: ${connectionId} for student ${studentId}`);

      // Send initial connection message
      const welcomeEvent = {
        type: 'connection_established',
        connectionId,
        topics,
        timestamp: new Date().toISOString(),
      };
      controller.enqueue(`data: ${JSON.stringify(welcomeEvent)}\n\n`);

      // Send periodic keep-alive
      const keepAlive = setInterval(() => {
        if (controller) {
          controller.enqueue(': keep-alive\n\n');
        }
      }, 30000);

      // Clean up on close
      controller.signal.addEventListener('abort', () => {
        clearInterval(keepAlive);
        sseConnections.delete(connectionId);
        console.log(`🔗 SSE connection closed: ${connectionId}`);
      });
    },
    cancel() {
      sseConnections.delete(connectionId);
      console.log(`🔗 SSE connection cancelled: ${connectionId}`);
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no', // Disable nginx buffering
    },
  });
}

/**
 * DELETE /api/dapr/events/stream
 * Close an SSE connection
 */
export async function DELETE(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const connectionId = body?.connectionId;

    if (!connectionId) {
      return NextResponse.json(
        { error: 'connectionId is required' },
        { status: 400 }
      );
    }

    const connection = sseConnections.get(connectionId);
    if (!connection) {
      return NextResponse.json(
        { error: 'Connection not found' },
        { status: 404 }
      );
    }

    // Close the connection
    if (connection.connection) {
      connection.connection.close();
    }

    sseConnections.delete(connectionId);

    return NextResponse.json({
      message: 'Connection closed',
      connectionId,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Error closing SSE connection:', error);

    return NextResponse.json(
      {
        error: 'Internal Server Error',
        message: 'Failed to close connection',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/dapr/events/stats
 * Get statistics about active SSE connections
 */
export async function HEAD() {
  const activeConnections = sseConnections.size;
  const topics = new Set<string>();
  const students = new Set<string>();

  for (const connection of sseConnections.values()) {
    connection.topics.forEach(t => topics.add(t));
    students.add(connection.studentId);
  }

  return new NextResponse(null, {
    status: 200,
    headers: {
      'X-SSE-Connections': activeConnections.toString(),
      'X-SSE-Topics': Array.from(topics).join(','),
      'X-SSE-Students': students.size.toString(),
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}

/**
 * Clean up stale connections (run periodically)
 */
export function cleanupStaleConnections(maxAge: number = 300000) {
  const now = Date.now();
  let cleaned = 0;

  for (const [connectionId, connection] of sseConnections.entries()) {
    const age = now - connection.lastHeartbeat.getTime();
    if (age > maxAge) {
      // Close stale connection
      if (connection.connection) {
        connection.connection.close();
      }
      sseConnections.delete(connectionId);
      cleaned++;
      console.log(`🧹 Cleaned up stale connection: ${connectionId}`);
    }
  }

  return cleaned;
}

// Auto-cleanup every 5 minutes (in production, this should be a separate cron job)
if (typeof setInterval !== 'undefined') {
  setInterval(() => {
    const cleaned = cleanupStaleConnections();
    if (cleaned > 0) {
      console.log(`🧹 Cleaned up ${cleaned} stale SSE connections`);
    }
  }, 5 * 60 * 1000); // Every 5 minutes
}

/**
 * Dapr Event Acknowledgment Functions (T095)
 */

interface DaprAcknowledgment {
  status: 'success' | 'failure' | 'retry';
  error?: string;
  message?: string;
  statusCode?: number;
  eventId?: string;
  correlationId: string;
  processingTime: number;
  retryAfter?: number;
  routing?: {
    connections: number;
    studentId?: string;
    topics: string[];
  };
}

/**
 * Validate Dapr event structure
 */
function validateDaprEvent(event: any): string | null {
  if (!event.id) {
    return 'Missing required field: id';
  }
  if (!event.type) {
    return 'Missing required field: type';
  }
  if (!event.data) {
    return 'Missing required field: data';
  }
  if (!event.source) {
    return 'Missing required field: source';
  }
  if (event.specversion && event.specversion !== '1.0') {
    return `Unsupported specversion: ${event.specversion}`;
  }

  // Validate event data structure
  if (typeof event.data !== 'object') {
    return 'Event data must be an object';
  }

  return null;
}

/**
 * Create Dapr acknowledgment response
 */
function createDaprResponse(correlationId: string, acknowledgment: DaprAcknowledgment): NextResponse {
  const statusCode = acknowledgment.statusCode || (acknowledgment.status === 'success' ? 200 : 500);

  const responseHeaders = {
    'Content-Type': 'application/json',
    'X-Dapr-Correlation-Id': correlationId,
    'X-Dapr-Processing-Time': acknowledgment.processingTime.toString(),
  };

  // Add retry headers if needed
  if (acknowledgment.status === 'retry' && acknowledgment.retryAfter) {
    responseHeaders['Retry-After'] = acknowledgment.retryAfter.toString();
  }

  return NextResponse.json(acknowledgment, {
    status: statusCode,
    headers: responseHeaders,
  });
}

/**
 * Create event acknowledgment based on routing results
 */
function createEventAcknowledgment(
  correlationId: string,
  rawEvent: any,
  processedEvent: any,
  routingResult: { routedTo: number; studentId?: string; topics: string[] },
  processingTime: number
): DaprAcknowledgment {
  // Determine if we should retry based on routing results
  if (routingResult.routedTo === 0 && routingResult.studentId) {
    // Event was for a specific student but no connections found
    // This might indicate the student hasn't connected yet - don't retry
    return {
      status: 'success', // We successfully processed it, just no one was listening
      message: 'Event processed but no active connections',
      statusCode: 200,
      eventId: rawEvent.id,
      correlationId,
      processingTime,
      routing: {
        connections: 0,
        studentId: routingResult.studentId,
        topics: routingResult.topics,
      },
    };
  }

  if (routingResult.routedTo === 0) {
    // General event with no connections - this is fine, might just be no listeners currently
    return {
      status: 'success',
      message: 'Event processed successfully, no active connections',
      statusCode: 200,
      eventId: rawEvent.id,
      correlationId,
      processingTime,
      routing: {
        connections: 0,
        topics: routingResult.topics,
      },
    };
  }

  // Success case - event was routed to connections
  return {
    status: 'success',
    message: 'Event processed and routed successfully',
    statusCode: 200,
    eventId: rawEvent.id,
    correlationId,
    processingTime,
    routing: {
      connections: routingResult.routedTo,
      studentId: routingResult.studentId,
      topics: routingResult.topics,
    },
  };
}

/**
 * Enhanced routeEventToSSE with detailed result reporting
 */
async function routeEventToSSE(event: ProcessedEvent): Promise<{ routedTo: number; studentId?: string; topics: string[] }> {
  const routedConnections: string[] = [];
  const topics = [event.topic];

  // Iterate through all active SSE connections
  for (const [connectionId, connection] of sseConnections.entries()) {
    // Check if connection is interested in this topic
    if (connection.topics.has(event.topic)) {
      // Check if student-specific filtering is needed
      if (event.metadata.studentId && connection.studentId !== event.metadata.studentId) {
        continue; // Skip this connection - not the intended student
      }

      // Send event to connection
      if (connection.connection) {
        try {
          const eventData = JSON.stringify(event);
          connection.connection.enqueue(`data: ${eventData}\n\n`);
          routedConnections.push(connectionId);
          connection.lastHeartbeat = new Date(); // Update heartbeat

          console.log(`📤 Routed event ${event.id} to connection ${connectionId}`);
        } catch (error) {
          console.error(`Failed to send event to connection ${connectionId}:`, error);
          // Clean up failed connection
          sseConnections.delete(connectionId);
        }
      }
    }
  }

  console.log(`📨 Event ${event.id} routed to ${routedConnections.length} connections`);

  return {
    routedTo: routedConnections.length,
    studentId: event.metadata.studentId,
    topics,
  };
}

/**
 * Negative acknowledgment for failed events (DLQ pattern)
 */
function createNegativeAcknowledgment(
  correlationId: string,
  error: string,
  retry: boolean = false,
  retryAfter: number = 60000
): DaprAcknowledgment {
  return {
    status: retry ? 'retry' : 'failure',
    error,
    statusCode: retry ? 503 : 500,
    correlationId,
    processingTime: 0,
    retryAfter: retry ? retryAfter : undefined,
  };
}

/**
 * Event processing metrics (for monitoring)
 */
const eventMetrics = {
  processed: 0,
  failed: 0,
  retried: 0,
  lastProcessed: null as Date | null,
  byType: new Map<string, number>(),
};

/**
 * Update event processing metrics
 */
function updateMetrics(success: boolean, eventType: string) {
  eventMetrics.processed++;
  if (!success) eventMetrics.failed++;
  eventMetrics.lastProcessed = new Date();

  const count = eventMetrics.byType.get(eventType) || 0;
  eventMetrics.byType.set(eventType, count + 1);
}

/**
 * Get event processing metrics
 */
export function getEventMetrics() {
  return {
    ...eventMetrics,
    byType: Object.fromEntries(eventMetrics.byType),
    successRate: eventMetrics.processed > 0
      ? ((eventMetrics.processed - eventMetrics.failed) / eventMetrics.processed * 100).toFixed(2)
      : 0,
  };
}

/**
 * GET /api/dapr/events/metrics
 * Get event processing metrics (separate endpoint)
 * Note: This would be a different route: /api/dapr/events/metrics
 */
export async function metricsEndpoint(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const reset = searchParams.get('reset') === 'true';

  const metrics = getEventMetrics();

  if (reset) {
    // Reset metrics (admin only in production)
    eventMetrics.processed = 0;
    eventMetrics.failed = 0;
    eventMetrics.retried = 0;
    eventMetrics.lastProcessed = null;
    eventMetrics.byType.clear();
  }

  return NextResponse.json(metrics, {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}