/**
 * API Integration Tests
 * Tests for all API hooks created in T110-T116
 * Last Updated: 2026-01-15
 * Task: T116
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

// Mock API client
jest.mock('@/lib/api-client', () => ({
  api: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

// Mock auth context
jest.mock('@/store/auth-context', () => ({
  useAuth: () => ({
    state: {
      isAuthenticated: true,
      user: { id: 'test-student-123' },
    },
  }),
}));

import { api } from '@/lib/api-client';
import { useMasteryCalculation, useMasteryHistory, useUpdateMastery } from '@/lib/hooks/useMastery';
import { useBatchProcessing, useBatchStatus, useBatchResults } from '@/lib/hooks/useBatch';
import { usePredictiveAnalytics, usePerformanceMetrics } from '@/lib/hooks/useAnalytics';
import { useRecommendations, useRecommendationFeedback } from '@/lib/hooks/useRecommendations';
import { useHistoricalAnalytics } from '@/lib/hooks/useHistorical';
import { useCohortComparison } from '@/lib/hooks/useCohort';

// Test utilities
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('API Integration Tests - T110-T116', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('T110: Mastery Calculation Hooks', () => {
    it('useMasteryCalculation should fetch mastery data', async () => {
      const mockResponse = {
        studentId: 'test-123',
        topic: 'algebra',
        currentScore: 0.85,
        confidence: 0.9,
        trend: 'improving' as const,
        recommendations: ['Practice more', 'Review basics'],
        lastUpdated: '2026-01-15T10:00:00Z',
        metadata: { samples: 10, avgScore: 0.75, bestScore: 0.9, timeSpent: 3600 },
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(
        () => useMasteryCalculation({
          studentId: 'test-123',
          topic: 'algebra',
          timeSpent: 3600,
          attempts: 10,
          difficulty: 'medium',
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/mastery/calculate', {
        studentId: 'test-123',
        topic: 'algebra',
        timeSpent: 3600,
        attempts: 10,
        difficulty: 'medium',
      });
      expect(result.current.data).toEqual(mockResponse);
    });

    it('useMasteryHistory should fetch mastery history', async () => {
      const mockHistory = {
        studentId: 'test-123',
        topic: 'algebra',
        entries: [
          { timestamp: '2026-01-14', score: 0.8, event: 'exercise-completed' },
          { timestamp: '2026-01-13', score: 0.75, event: 'quiz-completed' },
        ],
        summary: {
          totalEntries: 2,
          averageScore: 0.775,
          trend: 'improving' as const,
          bestScore: 0.8,
          worstScore: 0.75,
        },
      };

      (api.get as jest.Mock).mockResolvedValue(mockHistory);

      const { result } = renderHook(
        () => useMasteryHistory('test-123', 'algebra'),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith(
        '/api/mastery/history?studentId=test-123&topic=algebra'
      );
      expect(result.current.data).toEqual(mockHistory);
    });

    it('useUpdateMastery should update mastery data', async () => {
      const mockResponse = {
        studentId: 'test-123',
        topic: 'calculus',
        currentScore: 0.7,
        confidence: 0.8,
        trend: 'stable' as const,
        recommendations: [],
        lastUpdated: '2026-01-15T11:00:00Z',
        metadata: { samples: 5, avgScore: 0.65, bestScore: 0.7, timeSpent: 1800 },
      };

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useUpdateMastery(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        studentId: 'test-123',
        topic: 'calculus',
        timeSpent: 1800,
        attempts: 5,
        difficulty: 'hard',
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/mastery/update', {
        studentId: 'test-123',
        topic: 'calculus',
        timeSpent: 1800,
        attempts: 5,
        difficulty: 'hard',
      });
    });
  });

  describe('T111: Batch Processing Hooks', () => {
    it('useBatchProcessing should submit batch for processing', async () => {
      const mockResponse = {
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

      (api.post as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useBatchProcessing(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        studentId: 'test-123',
        assignments: [
          {
            id: 'assignment-1',
            type: 'exercise',
            content: { problem: 'Solve x^2 = 4' },
            difficulty: 'easy',
            estimatedTime: 300,
          },
        ],
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/batch/process', expect.objectContaining({
        studentId: 'test-123',
        assignments: expect.arrayContaining([
          expect.objectContaining({
            id: 'assignment-1',
            type: 'exercise',
          }),
        ]),
      }));
    });

    it('useBatchStatus should poll for batch status', async () => {
      const mockStatus = {
        batchId: 'batch-123',
        status: 'processing' as const,
        progress: 50,
        currentAssignment: 'assignment-2',
        errors: [],
        estimatedCompletion: '2026-01-15T10:05:00Z',
      };

      (api.get as jest.Mock).mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useBatchStatus('batch-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith('/api/batch/status?batchId=batch-123');
      expect(result.current.data).toEqual(mockStatus);
    });

    it('useBatchResults should fetch completed batch results', async () => {
      const mockResults = {
        batchId: 'batch-123',
        status: 'completed' as const,
        results: [
          {
            assignmentId: 'assignment-1',
            status: 'completed' as const,
            score: 0.9,
            feedback: 'Great work!',
            masteryChange: 0.05,
            executionTime: 280,
          },
        ],
        summary: {
          totalAssignments: 1,
          completedCount: 1,
          failedCount: 0,
          skippedCount: 0,
          averageScore: 0.9,
          totalProcessingTime: 280,
        },
        metadata: {
          submittedAt: '2026-01-15T10:00:00Z',
          completedAt: '2026-01-15T10:04:40Z',
          processingTime: 280,
        },
      };

      (api.get as jest.Mock).mockResolvedValue(mockResults);

      const { result } = renderHook(() => useBatchResults('batch-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith('/api/batch/results?batchId=batch-123');
      expect(result.current.data).toEqual(mockResults);
    });
  });

  describe('T112: Analytics Hooks', () => {
    it('usePredictiveAnalytics should fetch predictions', async () => {
      const mockPrediction = {
        studentId: 'test-123',
        timeframe: '7d',
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

      (api.get as jest.Mock).mockResolvedValue(mockPrediction);

      const { result } = renderHook(
        () => usePredictiveAnalytics({
          studentId: 'test-123',
          timeframe: '7d',
          topics: ['algebra'],
          includeConfidence: true,
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith(
        '/api/analytics/predictions?studentId=test-123&timeframe=7d&topics=algebra&includeConfidence=true'
      );
      expect(result.current.data).toEqual(mockPrediction);
    });

    it('usePerformanceMetrics should fetch performance data', async () => {
      const mockMetrics = {
        studentId: 'test-123',
        metrics: {
          engagement: 0.85,
          mastery: 0.75,
          consistency: 0.8,
          efficiency: 0.7,
          resilience: 0.9,
        },
        percentiles: {
          engagement: 85,
          mastery: 75,
          consistency: 80,
        },
        benchmarks: [
          {
            name: 'Math Proficiency',
            studentValue: 0.75,
            peerAverage: 0.68,
            percentile: 75,
            category: 'academic',
          },
        ],
      };

      (api.get as jest.Mock).mockResolvedValue(mockMetrics);

      const { result } = renderHook(() => usePerformanceMetrics('test-123'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith('/api/analytics/metrics?studentId=test-123');
      expect(result.current.data).toEqual(mockMetrics);
    });
  });

  describe('T113: Recommendations Hooks', () => {
    it('useRecommendations should fetch personalized recommendations', async () => {
      const mockRecommendations = {
        studentId: 'test-123',
        generatedAt: '2026-01-15T10:00:00Z',
        recommendations: [
          {
            id: 'rec-1',
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

      const { result } = renderHook(
        () => useRecommendations({
          studentId: 'test-123',
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
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/recommendations/generate', expect.objectContaining({
        studentId: 'test-123',
        context: expect.objectContaining({
          recentTopics: ['algebra'],
        }),
      }));
    });

    it('useRecommendationFeedback should submit feedback', async () => {
      (api.post as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useRecommendationFeedback(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({
        recommendationId: 'rec-1',
        studentId: 'test-123',
        feedback: {
          helpful: true,
          difficultyRating: 4,
          completed: true,
          completionTime: 25,
          notes: 'Great exercise!',
        },
        timestamp: '2026-01-15T10:30:00Z',
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/recommendations/feedback', {
        recommendationId: 'rec-1',
        studentId: 'test-123',
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
  });

  describe('T114: Historical Analytics Hooks', () => {
    it('useHistoricalAnalytics should fetch historical data', async () => {
      const mockHistorical = {
        studentId: 'test-123',
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
            type: 'improvement',
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

      (api.post as jest.Mock).mockResolvedValue(mockHistorical);

      const { result } = renderHook(
        () => useHistoricalAnalytics({
          studentId: 'test-123',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          granularity: 'day',
          metrics: ['mastery', 'engagement'],
          groupBy: ['topic'],
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith('/api/analytics/historical', expect.objectContaining({
        studentId: 'test-123',
        timeframe: {
          start: '2026-01-01',
          end: '2026-01-15',
        },
      }));
    });
  });

  describe('T115: Cohort Comparison Hooks', () => {
    it('useCohortComparison should fetch cohort data', async () => {
      const mockCohort = {
        studentId: 'test-123',
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

      (api.get as jest.Mock).mockResolvedValue(mockCohort);

      const { result } = renderHook(
        () => useCohortComparison({
          studentId: 'test-123',
          cohortId: 'cohort-abc',
          timeframe: {
            start: '2026-01-01',
            end: '2026-01-15',
          },
          metrics: ['mastery', 'engagement'],
          comparisonType: 'peer',
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.get).toHaveBeenCalledWith(
        '/api/analytics/cohort-comparison?studentId=test-123&cohortId=cohort-abc&start=2026-01-01&end=2026-01-15&metrics=mastery,engagement&type=peer'
      );
    });
  });

  describe('Authentication and Error Handling', () => {
    it('should handle unauthenticated state', async () => {
      const mockAuth = require('@/store/auth-context');
      mockAuth.useAuth.mockReturnValue({
        state: { isAuthenticated: false },
      });

      const { result } = renderHook(
        () => useMasteryCalculation({
          studentId: 'test-123',
          topic: 'algebra',
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(new Error('User not authenticated'));
    });

    it('should handle API errors', async () => {
      (api.post as jest.Mock).mockRejectedValue(new Error('API Error'));

      const { result } = renderHook(
        () => useMasteryCalculation({
          studentId: 'test-123',
          topic: 'algebra',
        }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toEqual(new Error('API Error'));
    });
  });

  describe('Utility Functions', () => {
    it('should format mastery score correctly', async () => {
      const { useMasteryCalculation } = require('@/lib/hooks/useMastery');
      const { formatMasteryScore, getMasteryColor, getTrendIndicator } = useMasteryCalculation;

      // Test formatMasteryScore
      expect(formatMasteryScore(0.95)).toBe('Expert');
      expect(formatMasteryScore(0.8)).toBe('Proficient');
      expect(formatMasteryScore(0.7)).toBe('Competent');
      expect(formatMasteryScore(0.5)).toBe('Developing');
      expect(formatMasteryScore(0.25)).toBe('Novice');
      expect(formatMasteryScore(0.1)).toBe('Beginner');

      // Test getMasteryColor
      expect(getMasteryColor(0.85)).toBe('#10b981'); // Green
      expect(getMasteryColor(0.7)).toBe('#3b82f6'); // Blue
      expect(getMasteryColor(0.5)).toBe('#f59e0b'); // Yellow
      expect(getMasteryColor(0.2)).toBe('#ef4444'); // Red

      // Test getTrendIndicator
      expect(getTrendIndicator('improving')).toEqual({ icon: '📈', color: '#10b981' });
      expect(getTrendIndicator('stable')).toEqual({ icon: '➡️', color: '#6b7280' });
      expect(getTrendIndicator('declining')).toEqual({ icon: '📉', color: '#ef4444' });
    });

    it('should format duration correctly', async () => {
      const { formatDuration } = require('@/lib/hooks/useBatch');

      expect(formatDuration(0.5)).toBe('< 1 min');
      expect(formatDuration(1)).toBe('1 min');
      expect(formatDuration(30)).toBe('30 mins');
      expect(formatDuration(60)).toBe('1 hour');
      expect(formatDuration(90)).toBe('1h 30m');
      expect(formatDuration(1440)).toBe('1 day');
      expect(formatDuration(2880)).toBe('2 days');
    });

    it('should format percentile correctly', async () => {
      const { formatPercentile } = require('@/lib/hooks/useCohort');

      expect(formatPercentile(0.95)).toBe('Top 10%');
      expect(formatPercentile(0.8)).toBe('Top 25%');
      expect(formatPercentile(0.6)).toBe('Top 50%');
      expect(formatPercentile(0.3)).toBe('Top 75%');
      expect(formatPercentile(0.1)).toBe('Bottom 25%');
    });
  });
});