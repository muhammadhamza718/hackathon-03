/**
 * API Hooks - Collection of React Query hooks for API endpoints
 * Last Updated: 2026-01-15
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { useAuth } from '@/store/auth-context';

// Export all API hooks for convenience
export {
  useMasteryCalculation,
  useBatchProcessing,
  usePredictiveAnalytics,
  useRecommendations,
  useHistoricalAnalytics,
  useCohortComparison,
  useMasteryHistory,
  useUpdateMastery,
  useBatchStatus,
  useBatchResults,
  usePerformanceMetrics,
  useRecommendationFeedback,
} from '@/lib/hooks';