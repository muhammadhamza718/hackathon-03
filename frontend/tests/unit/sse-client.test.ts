/**
 * Unit Tests for SSE Client
 * Task: T144
 *
 * Last Updated: 2026-01-15
 */

import { renderHook, act } from '@testing-library/react';
import { useSSEStore } from '@/lib/sse';

// Mock EventSource
class MockEventSource {
  url: string;
  readyState: number;
  onopen: ((this: EventSource, ev: Event) => any) | null = null;
  onmessage: ((this: EventSource, ev: MessageEvent) => any) | null = null;
  onerror: ((this: EventSource, ev: Event) => any) | null = null;
  onclose: ((this: EventSource, ev: CloseEvent) => any) | null = null;

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSED = 2;

  constructor(url: string) {
    this.url = url;
    this.readyState = MockEventSource.CONNECTING;
  }

  close(): void {
    this.readyState = MockEventSource.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  // Methods to simulate events for testing
  simulateOpen(): void {
    this.readyState = MockEventSource.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  simulateMessage(data: any): void {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }

  simulateError(error: any): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Mock EventSource globally
(global as any).EventSource = MockEventSource;

describe('SSE Client - T144', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the SSE store to initial state
    act(() => {
      useSSEStore.getState().reset();
    });
  });

  describe('Initial State', () => {
    it('should initialize with correct default state', () => {
      const state = useSSEStore.getState();

      expect(state.status).toBe('disconnected');
      expect(state.eventQueue).toEqual([]);
      expect(state.eventListeners).toBeInstanceOf(Map);
      expect(state.reconnectAttempts).toBe(0);
      expect(state.error).toBeNull();
      expect(state.eventCount).toBe(0);
      expect(state.filteredTopics).toBeInstanceOf(Set);
      expect(state.priorityFilter).toBeInstanceOf(Set);
      expect(state.studentId).toBeNull();
      expect(state.subscriptionId).toBeNull();
      expect(state.lastEvent).toBeNull();
      expect(state.connectionHealth).toBeNull();
    });
  });

  describe('Connection Management', () => {
    it('should connect to SSE endpoint', async () => {
      const { result } = renderHook(() => useSSEStore());

      await act(async () => {
        await result.current.connect();
      });

      expect(result.current.status).toBe('connecting');
    });

    it('should disconnect from SSE', async () => {
      const { result } = renderHook(() => useSSEStore());

      await act(async () => {
        await result.current.connect();
        result.current.disconnect();
      });

      expect(result.current.status).toBe('disconnected');
    });

    it('should handle connection establishment', async () => {
      const { result } = renderHook(() => useSSEStore());

      await act(async () => {
        await result.current.connect();
      });

      // Simulate successful connection
      await act(async () => {
        result.current.handleConnectionEstablished();
      });

      expect(result.current.status).toBe('connected');
      expect(result.current.reconnectAttempts).toBe(0);
    });

    it('should handle connection errors', async () => {
      const { result } = renderHook(() => useSSEStore());

      await act(async () => {
        await result.current.connect();
      });

      // Simulate connection error
      await act(async () => {
        result.current.handleError(new Error('Connection failed'));
      });

      expect(result.current.status).toBe('error');
      expect(result.current.error).toBe('Connection failed');
    });

    it('should handle reconnection', async () => {
      const { result } = renderHook(() => useSSEStore());

      await act(async () => {
        await result.current.connect();
        result.current.disconnect();
      });

      expect(result.current.status).toBe('disconnected');

      await act(async () => {
        await result.current.reconnect();
      });

      expect(result.current.status).toBe('connecting');
    });
  });

  describe('Event Handling', () => {
    it('should add event listeners', () => {
      const { result } = renderHook(() => useSSEStore());

      const mockCallback = jest.fn();
      let unsubscribe: () => void;

      act(() => {
        unsubscribe = result.current.subscribe('test-topic', mockCallback);
      });

      // Verify listener was added
      const listeners = result.current.eventListeners.get('test-topic');
      expect(listeners).toContain(mockCallback);

      // Verify unsubscribe works
      act(() => {
        unsubscribe();
      });

      const updatedListeners = result.current.eventListeners.get('test-topic');
      expect(updatedListeners).not.toContain(mockCallback);
    });

    it('should publish events to subscribers', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      const testEvent = {
        id: 'test-123',
        topic: 'test-topic',
        type: 'test-event',
        data: { message: 'test data' },
        priority: 'normal' as const,
        timestamp: new Date().toISOString(),
      };

      act(() => {
        result.current.subscribe('test-topic', mockCallback);
        result.current.publishEvent(testEvent);
      });

      expect(mockCallback).toHaveBeenCalledWith(testEvent);
      expect(result.current.eventQueue).toContain(testEvent);
      expect(result.current.eventCount).toBe(1);
    });

    it('should filter events by topic', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallbackA = jest.fn();
      const mockCallbackB = jest.fn();

      act(() => {
        result.current.subscribe('topic-a', mockCallbackA);
        result.current.subscribe('topic-b', mockCallbackB);

        // Publish event for topic-a (should only trigger callbackA)
        result.current.publishEvent({
          id: '1',
          topic: 'topic-a',
          type: 'test-event',
          data: { message: 'data-a' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });

        // Publish event for topic-b (should only trigger callbackB)
        result.current.publishEvent({
          id: '2',
          topic: 'topic-b',
          type: 'test-event',
          data: { message: 'data-b' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallbackA).toHaveBeenCalledTimes(1);
      expect(mockCallbackA).toHaveBeenCalledWith(expect.objectContaining({ id: '1' }));

      expect(mockCallbackB).toHaveBeenCalledTimes(1);
      expect(mockCallbackB).toHaveBeenCalledWith(expect.objectContaining({ id: '2' }));
    });

    it('should filter events by priority', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.subscribe('test-topic', mockCallback);
        result.current.setPriorityFilter(['high']);

        // Publish high priority event (should be received)
        result.current.publishEvent({
          id: '1',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'high-pri' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        // Publish normal priority event (should be filtered out)
        result.current.publishEvent({
          id: '2',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'normal-pri' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({ id: '1', priority: 'high' }));
    });

    it('should handle malformed events gracefully', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.subscribe('test-topic', mockCallback);

        // Publish malformed event (missing required fields)
        result.current.publishEvent({
          id: 'malformed',
          // Missing topic, type, data, priority, timestamp
        } as any);

        // Publish valid event (should still work)
        result.current.publishEvent({
          id: 'valid',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'valid' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      // Valid event should still be received
      expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({ id: 'valid' }));
    });

    it('should process incoming messages', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.subscribe('mastery-updated', mockCallback);
      });

      const incomingData = {
        id: 'incoming-123',
        topic: 'mastery-updated',
        type: 'mastery-updated',
        data: { score: 0.85, topic: 'algebra' },
        priority: 'high' as const,
        timestamp: new Date().toISOString(),
      };

      act(() => {
        result.current.handleMessage(incomingData);
      });

      expect(mockCallback).toHaveBeenCalledWith(incomingData);
      expect(result.current.eventQueue).toContain(incomingData);
    });

    it('should handle message parsing errors', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.handleError(new Error('Parse error'));
      });

      expect(result.current.status).toBe('error');
      expect(result.current.error).toBe('Parse error');
    });
  });

  describe('Event Queue Management', () => {
    it('should maintain event buffer', () => {
      const { result } = renderHook(() => useSSEStore());

      // Add many events
      act(() => {
        for (let i = 0; i < 25; i++) {
          result.current.publishEvent({
            id: `event-${i}`,
            topic: 'test-topic',
            type: 'test-event',
            data: { index: i },
            priority: 'normal' as const,
            timestamp: new Date().toISOString(),
          });
        }
      });

      expect(result.current.eventQueue.length).toBe(25);
    });

    it('should limit event buffer size', () => {
      const { result } = renderHook(() => useSSEStore());

      // Add more events than buffer size (20)
      act(() => {
        for (let i = 0; i < 30; i++) {
          result.current.publishEvent({
            id: `event-${i}`,
            topic: 'test-topic',
            type: 'test-event',
            data: { index: i },
            priority: 'normal' as const,
            timestamp: new Date().toISOString(),
          });
        }
      });

      expect(result.current.eventQueue.length).toBe(20); // Should be limited to buffer size
    });

    it('should clear events', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.publishEvent({
          id: 'test',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'test' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(result.current.eventQueue.length).toBe(1);

      act(() => {
        result.current.clearEvents();
      });

      expect(result.current.eventQueue.length).toBe(0);
      expect(result.current.eventCount).toBe(0);
    });

    it('should get events by topic', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        // Add events for different topics
        result.current.publishEvent({
          id: '1',
          topic: 'mastery-updated',
          type: 'mastery-updated',
          data: { score: 0.85 },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        result.current.publishEvent({
          id: '2',
          topic: 'feedback-received',
          type: 'feedback-received',
          data: { message: 'Good job!' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });

        result.current.publishEvent({
          id: '3',
          topic: 'mastery-updated',
          type: 'mastery-updated',
          data: { score: 0.9 },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });
      });

      const masteryEvents = result.current.getEventsByTopic('mastery-updated');
      expect(masteryEvents.length).toBe(2);
      expect(masteryEvents).toContainEqual(expect.objectContaining({ id: '1' }));
      expect(masteryEvents).toContainEqual(expect.objectContaining({ id: '3' }));

      const feedbackEvents = result.current.getEventsByTopic('feedback-received');
      expect(feedbackEvents.length).toBe(1);
      expect(feedbackEvents).toContainEqual(expect.objectContaining({ id: '2' }));
    });

    it('should get events by priority', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        // Add events with different priorities
        result.current.publishEvent({
          id: '1',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'high' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        result.current.publishEvent({
          id: '2',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'normal' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });

        result.current.publishEvent({
          id: '3',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'low' },
          priority: 'low' as const,
          timestamp: new Date().toISOString(),
        });
      });

      const highPriorityEvents = result.current.getEventsByPriority('high');
      expect(highPriorityEvents.length).toBe(1);
      expect(highPriorityEvents[0].id).toBe('1');

      const normalPriorityEvents = result.current.getEventsByPriority('normal');
      expect(normalPriorityEvents.length).toBe(1);
      expect(normalPriorityEvents[0].id).toBe('2');

      const lowPriorityEvents = result.current.getEventsByPriority('low');
      expect(lowPriorityEvents.length).toBe(1);
      expect(lowPriorityEvents[0].id).toBe('3');
    });
  });

  describe('Filtering and Configuration', () => {
    it('should set topic filters', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.setTopicFilter(['mastery-updated', 'feedback-received']);
      });

      expect(result.current.filteredTopics).toContain('mastery-updated');
      expect(result.current.filteredTopics).toContain('feedback-received');
      expect(result.current.filteredTopics.size).toBe(2);
    });

    it('should set priority filters', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.setPriorityFilter(['high', 'normal']);
      });

      expect(result.current.priorityFilter).toContain('high');
      expect(result.current.priorityFilter).toContain('normal');
      expect(result.current.priorityFilter.size).toBe(2);
    });

    it('should set student ID', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.setStudentId('student-123');
      });

      expect(result.current.studentId).toBe('student-123');
    });

    it('should set subscription ID', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.setSubscriptionId('sub-456');
      });

      expect(result.current.subscriptionId).toBe('sub-456');
    });

    it('should apply filters to events', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.subscribe('test-topic', mockCallback);
        result.current.setTopicFilter(['test-topic']); // Only allow test-topic
        result.current.setPriorityFilter(['high']); // Only allow high priority

        // This event should pass both filters
        result.current.publishEvent({
          id: '1',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'allowed' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        // This event should be filtered out (wrong topic)
        result.current.publishEvent({
          id: '2',
          topic: 'other-topic',
          type: 'test-event',
          data: { message: 'filtered' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        // This event should be filtered out (wrong priority)
        result.current.publishEvent({
          id: '3',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'filtered' },
          priority: 'low' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({ id: '1' }));
    });
  });

  describe('Connection Health', () => {
    it('should report healthy connection when events are flowing', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        // Add recent event
        result.current.publishEvent({
          id: 'recent',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'recent' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
      });

      const health = result.current.getConnectionHealth();
      expect(health.isHealthy).toBe(true);
      expect(health.eventCount).toBe(1);
      expect(health.lastEventTime).toBeDefined();
    });

    it('should report unhealthy when no recent events', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        // Set last event to long ago
        result.current.lastEvent = new Date(Date.now() - 120000); // 2 minutes ago
      });

      const health = result.current.getConnectionHealth();
      expect(health.isHealthy).toBe(false);
      expect(health.eventCount).toBe(0);
      expect(health.lastEventTime).toBeDefined();
    });

    it('should track connection statistics', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.publishEvent({
            id: `event-${i}`,
            topic: 'test-topic',
            type: 'test-event',
            data: { index: i },
            priority: 'normal' as const,
            timestamp: new Date().toISOString(),
          });
        }
      });

      const health = result.current.getConnectionHealth();
      expect(health.eventCount).toBe(10);
      expect(health.isHealthy).toBe(true);
    });
  });

  describe('Reconnection Logic', () => {
    it('should increment reconnect attempts on error', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.incrementReconnectAttempts();
      });

      expect(result.current.reconnectAttempts).toBe(1);

      act(() => {
        result.current.incrementReconnectAttempts();
      });

      expect(result.current.reconnectAttempts).toBe(2);
    });

    it('should reset reconnect attempts on successful connection', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.incrementReconnectAttempts();
        result.current.incrementReconnectAttempts();
      });

      expect(result.current.reconnectAttempts).toBe(2);

      act(() => {
        result.current.handleConnectionEstablished();
      });

      expect(result.current.reconnectAttempts).toBe(0);
    });

    it('should respect maximum reconnection attempts', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        // Increment past max attempts (10)
        for (let i = 0; i < 15; i++) {
          result.current.incrementReconnectAttempts();
        }
      });

      expect(result.current.reconnectAttempts).toBe(10); // Should cap at max
    });
  });

  describe('Error Handling', () => {
    it('should handle connection errors gracefully', () => {
      const { result } = renderHook(() => useSSEStore());

      const error = new Error('Network error');

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.status).toBe('error');
      expect(result.current.error).toBe('Network error');
    });

    it('should clear errors', () => {
      const { result } = renderHook(() => useSSEStore());

      act(() => {
        result.current.handleError(new Error('Test error'));
        expect(result.current.error).toBe('Test error');

        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });

    it('should handle event processing errors', () => {
      const { result } = renderHook(() => useSSEStore());

      // Test with malformed event data
      const malformedEvent = {
        // Missing required properties
      } as any;

      act(() => {
        result.current.publishEvent(malformedEvent);
      });

      // Should not crash and should continue working
      expect(result.current.eventCount).toBe(0); // Malformed events should be filtered
    });
  });

  describe('Cleanup and Reset', () => {
    it('should reset to initial state', () => {
      const { result } = renderHook(() => useSSEStore());

      // Modify state
      act(() => {
        result.current.setStudentId('student-123');
        result.current.setSubscriptionId('sub-456');
        result.current.publishEvent({
          id: 'test',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'test' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        });
        result.current.subscribe('test-topic', jest.fn());
      });

      expect(result.current.studentId).toBe('student-123');
      expect(result.current.eventQueue.length).toBe(1);
      expect(result.current.eventListeners.size).toBe(1);

      // Reset
      act(() => {
        result.current.reset();
      });

      // Verify reset
      expect(result.current.studentId).toBeNull();
      expect(result.current.subscriptionId).toBeNull();
      expect(result.current.eventQueue.length).toBe(0);
      expect(result.current.eventListeners.size).toBe(0);
      expect(result.current.status).toBe('disconnected');
    });

    it('should clear all event listeners', () => {
      const { result } = renderHook(() => useSSEStore());

      const callback1 = jest.fn();
      const callback2 = jest.fn();

      act(() => {
        result.current.subscribe('topic-1', callback1);
        result.current.subscribe('topic-2', callback2);
      });

      expect(result.current.eventListeners.size).toBe(2);

      act(() => {
        result.current.clearListeners();
      });

      expect(result.current.eventListeners.size).toBe(0);
    });
  });

  describe('Performance and Edge Cases', () => {
    it('should handle high volume of events efficiently', () => {
      const { result } = renderHook(() => useSSEStore());

      const startTime = Date.now();

      // Simulate high volume of events
      act(() => {
        for (let i = 0; i < 100; i++) {
          result.current.publishEvent({
            id: `high-vol-${i}`,
            topic: 'test-topic',
            type: 'test-event',
            data: { index: i },
            priority: 'normal' as const,
            timestamp: new Date().toISOString(),
          });
        }
      });

      const endTime = Date.now();
      const processingTime = endTime - startTime;

      // Should process efficiently (under 100ms for 100 events)
      expect(processingTime).toBeLessThan(100);

      // Should maintain buffer size limit
      expect(result.current.eventQueue.length).toBeLessThanOrEqual(20);
    });

    it('should handle duplicate event IDs', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.subscribe('test-topic', mockCallback);

        // Publish same event twice
        const event = {
          id: 'duplicate-event',
          topic: 'test-topic',
          type: 'test-event',
          data: { message: 'test' },
          priority: 'normal' as const,
          timestamp: new Date().toISOString(),
        };

        result.current.publishEvent(event);
        result.current.publishEvent(event); // Duplicate
      });

      // Should handle duplicates gracefully
      expect(mockCallback).toHaveBeenCalledTimes(2); // Both events processed
    });

    it('should handle extremely large events', () => {
      const { result } = renderHook(() => useSSEStore());

      const largeData = {
        id: 'large-event',
        topic: 'test-topic',
        type: 'test-event',
        data: {
          largeArray: Array.from({ length: 10000 }, (_, i) => `item-${i}`),
          largeString: 'x'.repeat(100000), // 100KB string
        },
        priority: 'normal' as const,
        timestamp: new Date().toISOString(),
      };

      act(() => {
        result.current.publishEvent(largeData);
      });

      // Should handle large events without crashing
      expect(result.current.eventQueue.length).toBe(1);
    });
  });

  describe('Student-specific Filtering', () => {
    it('should filter events by student ID', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.setStudentId('student-123');
        result.current.subscribe('mastery-updated', mockCallback);

        // Event for correct student (should pass)
        result.current.publishEvent({
          id: '1',
          topic: 'mastery-updated',
          type: 'mastery-updated',
          data: { studentId: 'student-123', score: 0.85 },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });

        // Event for different student (should be filtered)
        result.current.publishEvent({
          id: '2',
          topic: 'mastery-updated',
          type: 'mastery-updated',
          data: { studentId: 'student-456', score: 0.9 },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallback).toHaveBeenCalledTimes(1);
      expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({ id: '1' }));
    });

    it('should handle events without student ID', () => {
      const { result } = renderHook(() => useSSEStore());
      const mockCallback = jest.fn();

      act(() => {
        result.current.setStudentId('student-123');
        result.current.subscribe('system-alert', mockCallback);

        // Event without student ID (should pass through)
        result.current.publishEvent({
          id: 'system-1',
          topic: 'system-alert',
          type: 'system-alert',
          data: { message: 'System alert' },
          priority: 'high' as const,
          timestamp: new Date().toISOString(),
        });
      });

      expect(mockCallback).toHaveBeenCalledTimes(1);
    });
  });
});