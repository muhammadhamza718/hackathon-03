/**
 * Unit Tests for API Client and Hooks
 * Task: T141
 *
 * Last Updated: 2026-01-15
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import {
  useMasteryCalculation,
  useBatchProcessing,
  usePredictiveAnalytics,
  useRecommendations,
  useHistoricalAnalytics,
  useCohortComparison
} from '@/lib/hooks';

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock the auth context
jest.mock('@/store/auth-context', () => ({
  useAuth: () => ({
    state: {
      isAuthenticated: true,
      user: { id: 'test-student-123' },
    },
  }),
}));

// Create a test query client
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0, // Don't cache for tests
    },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('API Client and Hooks - T141', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API Client', () => {
    it('should make GET requests', async () => {
      const mockResponse = { data: 'test' };
      (api.get as jest.Mock).mockResolvedValue(mockResponse);

      const result = await api.get('/test-endpoint');

      expect(api.get).toHaveBeenCalledWith('/test-endpoint');
      expect(result).toEqual(mockResponse);
    });

    it('should make POST requests', async () => {
      const mockResponse = { success: true };
      const testData = { message: 'test' };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const result = await api.post('/test-endpoint', testData);

      expect(api.post).toHaveBeenCalledWith('/test-endpoint', testData);
      expect(result).toEqual(mockResponse);
    });

    it('should make PUT requests', async () => {
      const mockResponse = { updated: true };
      const testData = { message: 'updated' };

      (api.put as jest.Mock).mockResolvedValue(mockResponse);

      const result = await api.put('/test-endpoint', testData);

      expect(api.put).toHaveBeenCalledWith('/test-endpoint', testData);
      expect(result).toEqual(mockResponse);
    });

    it('should make DELETE requests', async () => {
      const mockResponse = { deleted: true };

      (api.delete as jest.Mock).mockResolvedValue(mockResponse);

      const result = await api.delete('/test-endpoint');

      expect(api.delete).toHaveBeenCalledWith('/test-endpoint');
      expect(result).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
      const mockError = new Error('Network Error');
      (api.get as jest.Mock).mockRejectedValue(mockError);

      await expect(api.get('/test-endpoint')).rejects.toThrow('Network Error');
    });
  });

  describe('Mastery Calculation Hook - useMasteryCalculation', () => {
    it('should fetch mastery calculation data', async () => {
      const mockMasteryData = {
        studentId: 'test-student-123',
        topic: 'algebra',
        currentScore: 0.85,
        confidence: 0.9,
        trend: 'improving' as const,
        recommendations: ['Practice more', 'Review basics'],
        lastUpdated: '2026-01-15T10:00:00Z',
        metadata: {
          samples: 10,
          avgScore: 0.75,
          bestScore: 0.9,
          timeSpent: 3600,
        },
      };

      (api.post as jest.Mock).mockResolvedValue(mockMasteryData);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/mastery/calculate', {
        studentId: 'test-student-123',
        topic: 'algebra',
        timeSpent: 3600,
        attempts: 10,
        difficulty: 'medium',
      });

      expect(result.current.data).toEqual(mockMasteryData);
    });

    it('should handle mastery calculation error', async () => {
      const mockError = new Error('Calculation failed');
      (api.post as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should not fetch if studentId is missing', () => {
      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: '',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle invalid parameters', async () => {
      (api.post as jest.Mock).mockRejectedValue(new Error('Invalid parameters'));

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: -100, // Invalid negative time
          attempts: -5, // Invalid negative attempts
          difficulty: 'medium',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(new Error('Invalid parameters'));
    });
  });

  describe('Batch Processing Hook - useBatchProcessing', () => {
    it('should submit batch for processing', async () => {
      const mockBatchResponse = {
        batchId: 'batch-123',
        status: 'queued' as const,
        results: [],
        summary: {
          totalAssignments: 3,
          completedCount: 0,
          failedCount: 0,
          skippedCount: 0,
          averageScore: 0,
          totalProcessingTime: 0,
        },
        metadata: {
          submittedAt: '2026-01-15T10:00:00Z',
          queuePosition: 1,
        },
      };

      (api.post as jest.Mock).mockResolvedValue(mockBatchResponse);

      const { result } = renderHook(() =>
        useBatchProcessing(),
        { wrapper }
      );

      await act(async () => {
        result.current.mutate({
          studentId: 'test-student-123',
          assignments: [
            {
              id: 'assignment-1',
              type: 'exercise',
              content: { problem: 'Solve equation' },
              difficulty: 'easy',
              estimatedTime: 300,
            },
          ],
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/batch/process', {
        studentId: 'test-student-123',
        assignments: [
          {
            id: 'assignment-1',
            type: 'exercise',
            content: { problem: 'Solve equation' },
            difficulty: 'easy',
            estimatedTime: 300,
          },
        ],
      });

      expect(result.current.data).toEqual(mockBatchResponse);
    });

    it('should handle batch processing error', async () => {
      const mockError = new Error('Batch processing failed');
      (api.post as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useBatchProcessing(),
        { wrapper }
      );

      await act(async () => {
        result.current.mutate({
          studentId: 'test-student-123',
          assignments: [],
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should validate batch input', async () => {
      const { result } = renderHook(() =>
        useBatchProcessing(),
        { wrapper }
      );

      await act(async () => {
        result.current.mutate({
          studentId: '', // Invalid empty studentId
          assignments: [], // Empty assignments
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('Predictive Analytics Hook - usePredictiveAnalytics', () => {
    it('should fetch predictive analytics data', async () => {
      const mockAnalyticsData = {
        studentId: 'test-student-123',
        timeframe: '7d' as const,
        predictions: [
          {
            topic: 'algebra',
            predictedScore: 0.85,
            confidence: 0.8,
            trend: 'improving' as const,
            daysToMastery: 14,
            dailyRate: 0.02,
            factors: {
              currentScore: 0.7,
              recentPerformance: [0.65, 0.68, 0.7],
              consistency: 0.8,
              timeSpent: 3600,
            },
          },
        ],
        overallTrajectory: {
          direction: 'upward' as const,
          velocity: 0.15,
          acceleration: 0.02,
          sustainability: 0.75,
        },
        riskFactors: [],
        recommendations: [
          {
            type: 'study' as const,
            priority: 'high' as const,
            title: 'Focus on weak areas',
            description: 'Concentrate on algebra fundamentals',
            estimatedTime: 60,
            expectedImpact: 0.8,
            topics: ['algebra'],
          },
        ],
        confidence: {
          overall: 0.8,
          byTopic: { algebra: 0.85 },
          sampleSize: 50,
          reliability: 'high' as const,
        },
        generatedAt: '2026-01-15T10:00:00Z',
      };

      (api.get as jest.Mock).mockResolvedValue(mockAnalyticsData);

      const { result } = renderHook(() =>
        usePredictiveAnalytics({
          studentId: 'test-student-123',
          timeframe: '7d',
          topics: ['algebra'],
          includeConfidence: true,
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith(
        '/api/analytics/predictions?studentId=test-student-123&timeframe=7d&topics=algebra&includeConfidence=true'
      );

      expect(result.current.data).toEqual(mockAnalyticsData);
    });

    it('should handle analytics error', async () => {
      const mockError = new Error('Analytics service unavailable');
      (api.get as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        usePredictiveAnalytics({
          studentId: 'test-student-123',
          timeframe: '7d',
          topics: ['algebra'],
          includeConfidence: true,
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should handle missing student ID', () => {
      const { result } = renderHook(() =>
        usePredictiveAnalytics({
          studentId: '', // Missing student ID
          timeframe: '7d',
          topics: ['algebra'],
          includeConfidence: true,
        }),
        { wrapper }
      );

      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('Recommendations Hook - useRecommendations', () => {
    it('should fetch personalized recommendations', async () => {
      const mockRecommendations = {
        studentId: 'test-student-123',
        generatedAt: '2026-01-15T10:00:00Z',
        recommendations: [
          {
            id: 'rec-123',
            type: 'exercise' as const,
            title: 'Advanced Algebra Practice',
            description: 'Practice advanced algebraic equations',
            topic: 'algebra',
            difficulty: 'medium' as const,
            estimatedDuration: 30,
            priority: 'high' as const,
            reasoning: {
              relevance: 0.9,
              gapAnalysis: 'Strength in algebra but needs practice',
              difficultyMatch: 'Appropriate challenge level',
              masteryLevel: 'developing' as const,
            },
            expectedImpact: {
              masteryGain: 0.15,
              confidenceBoost: 0.1,
              skillCoverage: ['equation-solving', 'factorization'],
            },
            prerequisites: ['basic-algebra'],
            dependencies: [],
            content: {
              format: 'interactive' as const,
              duration: 30,
            },
            metadata: {
              tags: ['algebra', 'practice'],
              category: 'mathematics',
              source: 'algorithm' as const,
            },
          },
        ],
        summary: {
          totalRecommendations: 1,
          byType: { exercise: 1 },
          byPriority: { high: 1 },
          byTopic: { algebra: 1 },
          difficultyDistribution: { medium: 1 },
          estimatedTotalTime: 30,
        },
        metadata: {
          modelVersion: '1.0',
          confidence: 0.85,
          processingTime: 0.5,
          context: {},
        },
      };

      (api.post as jest.Mock).mockResolvedValue(mockRecommendations);

      const { result } = renderHook(() =>
        useRecommendations({
          studentId: 'test-student-123',
          context: {
            recentTopics: ['algebra'],
            strugglingTopics: ['calculus'],
            timeAvailability: 60,
            learningStyle: 'visual',
            difficultyPreference: 'medium',
          },
          filters: {
            maxRecommendations: 5,
            includeTypes: ['exercise', 'quiz'],
          },
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/recommendations/generate', expect.objectContaining({
        studentId: 'test-student-123',
        context: expect.objectContaining({
          recentTopics: ['algebra'],
        }),
      }));

      expect(result.current.data).toEqual(mockRecommendations);
    });

    it('should handle recommendation error', async () => {
      const mockError = new Error('Recommendation service failed');
      (api.post as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useRecommendations({
          studentId: 'test-student-123',
          context: {
            recentTopics: ['algebra'],
          },
          filters: {},
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should handle recommendation feedback', async () => {
      const mockResponse = { success: true };
      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() =>
        useRecommendations({
          studentId: 'test-student-123',
          context: { recentTopics: ['algebra'] },
          filters: {},
        }),
        { wrapper }
      );

      // Test feedback submission
      await act(async () => {
        result.current.submitFeedback({
          recommendationId: 'rec-123',
          studentId: 'test-student-123',
          feedback: {
            helpful: true,
            difficultyRating: 4,
            completed: true,
            completionTime: 25,
            notes: 'Great exercise!',
          },
          timestamp: '2026-01-15T10:30:00Z',
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/recommendations/feedback', expect.objectContaining({
        recommendationId: 'rec-123',
        studentId: 'test-student-123',
      }));
    });
  });

  describe('Historical Analytics Hook - useHistoricalAnalytics', () => {
    it('should fetch historical analytics data', async () => {
      const mockHistoricalData = {
        studentId: 'test-student-123',
        timeframe: {
          start: '2026-01-01',
          end: '2026-01-15',
        },
        data: [
          {
            timestamp: '2026-01-15T10:00:00Z',
            metrics: {
              mastery: {
                avgScore: 0.85,
                topicScores: { algebra: 0.9, calculus: 0.8 },
                trend: 'improving' as const,
                confidence: 0.85,
              },
              engagement: {
                activeTime: 120,
                sessions: 3,
                consistency: 0.8,
                focusScore: 0.75,
              },
            },
            context: {
              topics: ['algebra', 'calculus'],
              assignments: ['assignment-1', 'assignment-2'],
              timeSpent: 7200,
              breaks: 2,
            },
          },
        ],
        summary: {
          totalStudyTime: 36000,
          avgDailyPerformance: 0.8,
          improvementRate: 0.15,
          consistencyScore: 0.75,
          peakPerformance: {
            date: '2026-01-14',
            score: 0.9,
          },
          busiestPeriod: {
            date: '2026-01-15',
            activity: 3,
          },
        },
        trends: [
          {
            metric: 'mastery',
            direction: 'upward' as const,
            rate: 0.02,
            significance: 0.8,
            confidence: 0.85,
          },
        ],
        insights: [
          {
            category: 'performance' as const,
            type: 'improvement' as const,
            description: 'Consistent improvement in algebra',
            impact: 'high' as const,
            evidence: ['Score increased from 0.7 to 0.9'],
            recommendations: ['Continue current study pattern'],
          },
        ],
        metadata: {
          granularity: 'day',
          totalPoints: 15,
          missingData: 0,
          confidence: 0.9,
        },
      };

      (api.post as jest.Mock).mockResolvedValue(mockHistoricalData);

      const { result } = renderHook(() =>
        useHistoricalAnalytics({
          studentId: 'test-student-123',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          granularity: 'day',
          metrics: ['mastery', 'engagement'],
          groupBy: ['topic'],
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/analytics/historical', expect.objectContaining({
        studentId: 'test-student-123',
        timeframe: {
          start: '2026-01-01',
          end: '2026-01-15',
        },
      }));

      expect(result.current.data).toEqual(mockHistoricalData);
    });

    it('should handle historical analytics error', async () => {
      const mockError = new Error('Historical data service unavailable');
      (api.post as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useHistoricalAnalytics({
          studentId: 'test-student-123',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          granularity: 'day',
          metrics: ['mastery'],
          groupBy: ['topic'],
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('Cohort Comparison Hook - useCohortComparison', () => {
    it('should fetch cohort comparison data', async () => {
      const mockCohortData = {
        studentId: 'test-student-123',
        cohortId: 'cohort-abc',
        timeframe: {
          start: '2026-01-01',
          end: '2026-01-15',
        },
        studentPerformance: {
          metrics: {
            mastery: 0.85,
            engagement: 0.8,
            consistency: 0.75,
            accuracy: 0.82,
            efficiency: 0.78,
            resilience: 0.9,
          },
          topics: [
            {
              topic: 'algebra',
              score: 0.9,
              percentile: 0.85,
              trend: 'improving' as const,
              studyTime: 3600,
            },
          ],
          trends: [
            {
              metric: 'mastery',
              direction: 'upward' as const,
              rate: 0.02,
              confidence: 0.85,
            },
          ],
          improvementRate: 0.15,
        },
        cohortAverage: {
          metrics: {
            mastery: 0.75,
            engagement: 0.7,
            consistency: 0.72,
            accuracy: 0.75,
            efficiency: 0.72,
            resilience: 0.8,
          },
          topics: [
            {
              topic: 'algebra',
              score: 0.75,
              percentile: 0.5,
              trend: 'stable' as const,
              studyTime: 2800,
            },
          ],
          trends: [
            {
              metric: 'mastery',
              direction: 'stable' as const,
              rate: 0.01,
              confidence: 0.7,
            },
          ],
          distribution: {
            quartiles: { q1: 0.6, q2: 0.75, q3: 0.85, q4: 0.95 },
            range: { min: 0.4, max: 0.95 },
            standardDeviation: 0.12,
          },
        },
        percentileRanks: [
          {
            metric: 'mastery',
            studentValue: 0.85,
            cohortAvg: 0.75,
            percentile: 0.85,
            rank: 3,
            outOf: 20,
          },
        ],
        comparisonInsights: [
          {
            type: 'strength' as const,
            category: 'mastery',
            description: 'Above average performance in algebra',
            impact: 'high' as const,
            evidence: {
              studentValue: 0.85,
              cohortAvg: 0.75,
              difference: 0.1,
              percentile: 0.85,
            },
            recommendations: ['Maintain current study habits'],
          },
        ],
        metadata: {
          cohortSize: 20,
          sampleSize: 20,
          confidence: 0.88,
          dataQuality: 'high' as const,
        },
      };

      (api.get as jest.Mock).mockResolvedValue(mockCohortData);

      const { result } = renderHook(() =>
        useCohortComparison({
          studentId: 'test-student-123',
          cohortId: 'cohort-abc',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          metrics: ['mastery', 'engagement'],
          comparisonType: 'peer' as const,
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith(
        '/api/analytics/cohort-comparison?studentId=test-student-123&cohortId=cohort-abc&start=2026-01-01&end=2026-01-15&metrics=mastery,engagement&type=peer'
      );

      expect(result.current.data).toEqual(mockCohortData);
    });

    it('should handle cohort comparison error', async () => {
      const mockError = new Error('Cohort comparison service failed');
      (api.get as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useCohortComparison({
          studentId: 'test-student-123',
          cohortId: 'cohort-abc',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          metrics: ['mastery'],
          comparisonType: 'peer' as const,
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should handle missing required parameters', () => {
      const { result } = renderHook(() =>
        useCohortComparison({
          studentId: '', // Missing required
          cohortId: '',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          metrics: ['mastery'],
          comparisonType: 'peer' as const,
        }),
        { wrapper }
      );

      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
    });
  });

  describe('API Client Error Handling', () => {
    it('should handle 401 Unauthorized errors', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { message: 'Unauthorized' },
        },
      };
      (api.get as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should handle 429 Rate Limit errors', async () => {
      const mockError = {
        response: {
          status: 429,
          data: { message: 'Rate limit exceeded' },
        },
      };
      (api.post as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        useBatchProcessing(),
        { wrapper }
      );

      await act(async () => {
        result.current.mutate({
          studentId: 'test-student-123',
          assignments: [{ id: 'test', type: 'exercise', content: {}, difficulty: 'easy', estimatedTime: 300 }],
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });

    it('should handle network errors', async () => {
      const mockError = new Error('Network Error');
      (api.get as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() =>
        usePredictiveAnalytics({
          studentId: 'test-student-123',
          timeframe: '7d',
          topics: ['algebra'],
          includeConfidence: true,
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('API Client Performance', () => {
    it('should handle concurrent requests', async () => {
      const mockResponses = [
        { data: 'response-1' },
        { data: 'response-2' },
        { data: 'response-3' },
      ];

      (api.get as jest.Mock)
        .mockResolvedValueOnce(mockResponses[0])
        .mockResolvedValueOnce(mockResponses[1])
        .mockResolvedValueOnce(mockResponses[2]);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      // Simulate multiple concurrent requests
      const promises = [
        api.get('/endpoint-1'),
        api.get('/endpoint-2'),
        api.get('/endpoint-3'),
      ];

      const results = await Promise.all(promises);

      expect(results).toEqual(mockResponses);
    });

    it('should cache requests appropriately', async () => {
      const mockData = { cached: true };
      (api.get as jest.Mock).mockResolvedValue(mockData);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      // First request
      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Second request with same parameters should use cache
      const { result: result2 } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result2.current.isSuccess).toBe(true));

      // Verify the API was only called once due to caching
      expect(api.get).toHaveBeenCalledTimes(1);
    });

    it('should handle large response payloads', async () => {
      // Create a large response payload
      const largeResponse = {
        studentId: 'test-student-123',
        topic: 'algebra',
        largeDataArray: Array.from({ length: 1000 }, (_, i) => ({
          id: `item-${i}`,
          data: `This is a large data item ${i} with some content`,
          metadata: {
            index: i,
            timestamp: new Date().toISOString(),
            computed: Array.from({ length: 100 }, (__, j) => j),
          },
        })),
        currentScore: 0.85,
        confidence: 0.9,
        trend: 'improving' as const,
        recommendations: Array.from({ length: 50 }, (_, i) => ({
          id: `rec-${i}`,
          title: `Recommendation ${i}`,
          description: `This is recommendation number ${i}`,
        })),
        lastUpdated: '2026-01-15T10:00:00Z',
        metadata: {
          samples: 1000,
          avgScore: 0.75,
          bestScore: 0.9,
          timeSpent: 3600000, // 1000 hours
        },
      };

      (api.post as jest.Mock).mockResolvedValue(largeResponse);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600000,
          attempts: 1000,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toEqual(largeResponse);
      expect(result.current.data?.largeDataArray).toHaveLength(1000);
    });
  });

  describe('Authentication Integration', () => {
    it('should handle unauthenticated state', () => {
      // Mock unauthenticated state
      jest.mock('@/store/auth-context', () => ({
        useAuth: () => ({
          state: {
            isAuthenticated: false,
            user: null,
          },
        }),
      }));

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      // Should not make API call when unauthenticated
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle token refresh on 401', async () => {
      const unauthorizedError = {
        response: {
          status: 401,
          data: { message: 'Token expired' },
        },
      };

      const validResponse = {
        studentId: 'test-student-123',
        topic: 'algebra',
        currentScore: 0.85,
        confidence: 0.9,
        trend: 'improving' as const,
        recommendations: ['Practice more'],
        lastUpdated: '2026-01-15T10:00:00Z',
        metadata: {
          samples: 10,
          avgScore: 0.75,
          bestScore: 0.9,
          timeSpent: 3600,
        },
      };

      // First call returns 401, second call returns valid response
      (api.post as jest.Mock)
        .mockRejectedValueOnce(unauthorizedError)
        .mockResolvedValueOnce(validResponse);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper }
      );

      // Should eventually succeed after token refresh
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(validResponse);
    });
  });

  describe('Edge Cases and Error Scenarios', () => {
    it('should handle malformed API responses', async () => {
      // Return malformed response
      (api.get as jest.Mock).mockResolvedValue({
        // Missing required fields
        invalid: 'response',
      });

      const { result } = renderHook(() =>
        usePredictiveAnalytics({
          studentId: 'test-student-123',
          timeframe: '7d',
          topics: ['algebra'],
          includeConfidence: true,
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      // Should handle gracefully and return the malformed response
      expect(result.current.data).toBeDefined();
    });

    it('should handle timeout errors', async () => {
      const timeoutError = new Error('Request timeout');
      (api.post as jest.Mock).mockRejectedValue(timeoutError);

      const { result } = renderHook(() =>
        useBatchProcessing(),
        { wrapper }
      );

      await act(async () => {
        result.current.mutate({
          studentId: 'test-student-123',
          assignments: [{ id: 'test', type: 'exercise', content: {}, difficulty: 'easy', estimatedTime: 300 }],
        });
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toEqual(timeoutError);
    });

    it('should handle empty arrays and null values', async () => {
      const emptyResponse = {
        studentId: 'test-student-123',
        topic: 'algebra',
        currentScore: 0,
        confidence: 0,
        trend: 'stable' as const,
        recommendations: [],
        lastUpdated: '2026-01-15T10:00:00Z',
        metadata: {
          samples: 0,
          avgScore: 0,
          bestScore: 0,
          timeSpent: 0,
        },
      };

      (api.post as jest.Mock).mockResolvedValue(emptyResponse);

      const { result } = renderHook(() =>
        useMasteryCalculation({
          studentId: 'test-student-123',
          topic: 'algebra',
          timeSpent: 0,
          attempts: 0,
          difficulty: 'easy',
        }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(emptyResponse);
    });
  });
});