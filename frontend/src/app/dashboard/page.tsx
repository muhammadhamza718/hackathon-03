/**
 * Dashboard Overview Page
 * Displays mastery score, recent activity, and predictions
 * Last Updated: 2026-01-15
 */

"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useSSE } from '@/lib/sse';
import { useMastery } from '@/hooks/useApi';

// Mock data for dashboard (will be replaced with real API data)
const MOCK_MASTERY_DATA = {
  currentScore: 78.5,
  weeklyTrend: +12.3,
  cohortAverage: 72.1,
  rank: 23,
  totalStudents: 156,
  completedAssignments: 12,
  totalAssignments: 18,
};

const MOCK_RECENT_ACTIVITY = [
  {
    id: '1',
    type: 'feedback',
    title: 'Python Function Review',
    description: 'Received detailed feedback on your recursion function',
    timestamp: '5 minutes ago',
    priority: 'high',
  },
  {
    id: '2',
    type: 'mastery',
    title: 'Algorithm Mastery',
    description: 'You reached 85% mastery in sorting algorithms',
    timestamp: '1 hour ago',
    priority: 'normal',
  },
  {
    id: '3',
    type: 'recommendation',
    title: 'New Learning Path',
    description: 'Based on your progress, try advanced data structures',
    timestamp: '2 hours ago',
    priority: 'low',
  },
  {
    id: '4',
    type: 'progress',
    title: 'Assignment Submitted',
    description: 'Binary Search Tree implementation submitted',
    timestamp: '3 hours ago',
    priority: 'normal',
  },
];

const MOCK_PREDICTIONS = [
  {
    day: 'Mon',
    score: 80,
    confidence: 0.85,
  },
  {
    day: 'Tue',
    score: 82,
    confidence: 0.88,
  },
  {
    day: 'Wed',
    score: 83,
    confidence: 0.82,
  },
  {
    day: 'Thu',
    score: 85,
    confidence: 0.90,
  },
  {
    day: 'Fri',
    score: 86,
    confidence: 0.92,
  },
  {
    day: 'Sat',
    score: 87,
    confidence: 0.88,
  },
  {
    day: 'Sun',
    score: 88,
    confidence: 0.85,
  },
];

export default function DashboardPage() {
  const { user, state } = useAuth();
  const sse = useSSEStore();
  const { data: masteryData, isLoading: isMasteryLoading } = useMasteryCalculation({
    studentId: state.user?.id || '',
    topic: 'overall',
    timeSpent: 0,
    attempts: 0,
    difficulty: 'medium',
  });

  const [realTimeEvents, setRealTimeEvents] = useState<any[]>([]);
  const [isUpdating, setIsUpdating] = useState(false);

  // Subscribe to real-time mastery updates
  useEffect(() => {
    if (!state.isAuthenticated) return;

    const unsubscribe = sse.subscribe('mastery-updated', (event) => {
      console.log('Mastery update received:', event);
      setIsUpdating(true);

      // Add to real-time events list
      setRealTimeEvents(prev => {
        const newEvents = [event, ...prev];
        return newEvents.slice(0, 5); // Keep last 5
      });

      // Simulate UI update
      setTimeout(() => setIsUpdating(false), 1000);

      // Show toast notification
      showToast('Mastery score updated!', 'success');
    });

    // Subscribe to feedback events
    const unsubscribeFeedback = sse.subscribe('feedback-received', (event) => {
      showToast('New feedback available!', 'info');
    });

    return () => {
      if (typeof unsubscribe === 'function') unsubscribe();
      if (typeof unsubscribeFeedback === 'function') unsubscribeFeedback();
    };
  }, [sse, state.isAuthenticated]);


  // Calculate progress percentage
  const progressPercentage = (masteryData.completedAssignments / masteryData.totalAssignments) * 100;

  // Format trend indicator
  const getTrendIndicator = (trend: number) => {
    if (trend > 0) {
      return { icon: '📈', color: 'text-green-600', bg: 'bg-green-100 dark:bg-green-900/20' };
    } else if (trend < 0) {
      return { icon: '📉', color: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/20' };
    }
    return { icon: '➡️', color: 'text-zinc-600', bg: 'bg-zinc-100 dark:bg-zinc-800' };
  };

  const trend = getTrendIndicator(masteryData.weeklyTrend);

  // Get recent activity combining mock data with real-time events
  const combinedActivity = [...MOCK_RECENT_ACTIVITY, ...realTimeEvents.map(event => ({
    id: event.id,
    type: event.type,
    title: event.data?.title || 'Real-time Update',
    description: event.data?.message || 'New event received',
    timestamp: 'Just now',
    priority: event.priority || 'normal',
  }))].slice(0, 8); // Limit to 8 total

  return (
    <div className="space-y-6">
      {/* Real-time Update Indicator */}
      {isUpdating && (
        <div className="flex items-center gap-2 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-4 py-2 rounded-lg animate-pulse">
          <span>🔄</span>
          <span className="text-sm font-medium">Real-time update in progress...</span>
        </div>
      )}

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Mastery Score Card */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl p-6 border border-zinc-200 dark:border-zinc-800">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400">Mastery Score</h3>
            <span className={`text-lg ${trend.bg} ${trend.color} px-2 py-1 rounded-full text-xs font-bold`}>
              {trend.icon} {Math.abs(masteryData.weeklyTrend)}%
            </span>
          </div>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
              {masteryData.currentScore}
            </span>
            <span className="text-lg font-medium text-zinc-500 dark:text-zinc-400 mb-1">%</span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
            <span>🎯</span>
            <span>Rank #{masteryData.rank} of {masteryData.totalStudents}</span>
          </div>
        </div>

        {/* Progress Card */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl p-6 border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400 mb-2">
            Assignment Progress
          </h3>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
              {masteryData.completedAssignments}
            </span>
            <span className="text-lg font-medium text-zinc-500 dark:text-zinc-400 mb-1">
              / {masteryData.totalAssignments}
            </span>
          </div>
          {/* Progress Bar */}
          <div className="mt-3 h-2 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
            {progressPercentage.toFixed(0)}% Complete
          </p>
        </div>

        {/* Cohort Comparison Card */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl p-6 border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400 mb-2">
            Cohort Average
          </h3>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
              {masteryData.cohortAverage}
            </span>
            <span className="text-lg font-medium text-zinc-500 dark:text-zinc-400 mb-1">%</span>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <div className="flex-1 h-2 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                style={{ width: `${(masteryData.currentScore - masteryData.cohortAverage + 10) * 2}%` }}
              />
            </div>
            <span className={`text-xs font-bold ${
              masteryData.currentScore > masteryData.cohortAverage
                ? 'text-green-600 dark:text-green-400'
                : 'text-zinc-600 dark:text-zinc-400'
            }`}>
              {masteryData.currentScore > masteryData.cohortAverage ? '+' : ''}
              {(masteryData.currentScore - masteryData.cohortAverage).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Connection Status Card */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl p-6 border border-zinc-200 dark:border-zinc-800">
          <h3 className="text-sm font-medium text-zinc-600 dark:text-zinc-400 mb-2">
            Real-Time Status
          </h3>
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${
              sse.getConnectionStatus().isConnected
                ? 'bg-green-500 animate-pulse'
                : 'bg-red-500'
            }`} />
            <span className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
              {sse.getConnectionStatus().isConnected ? 'Connected' : 'Offline'}
            </span>
          </div>
          <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
            {sse.getConnectionStatus().isConnected ? 'Live updates active' : 'Connection lost'}
          </p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Feed */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Recent Activity</h2>
            <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
              View All
            </button>
          </div>

          <div className="space-y-3">
            {combinedActivity.map((activity) => (
              <div
                key={activity.id}
                className="bg-white dark:bg-zinc-900 rounded-lg p-4 border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${
                    activity.priority === 'high'
                      ? 'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                      : activity.priority === 'normal'
                      ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                      : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                  }`}>
                    {activity.type === 'feedback' && '💬'}
                    {activity.type === 'mastery' && '🎯'}
                    {activity.type === 'recommendation' && '✨'}
                    {activity.type === 'progress' && '✅'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                        {activity.title}
                      </h3>
                      <span className="text-xs text-zinc-500 dark:text-zinc-400 whitespace-nowrap ml-2">
                        {activity.timestamp}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
                      {activity.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-6">
          {/* 7-Day Prediction */}
          <div>
            <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              7-Day Prediction
            </h2>
            <div className="bg-white dark:bg-zinc-900 rounded-xl p-4 border border-zinc-200 dark:border-zinc-800">
              <div className="space-y-4">
                {MOCK_PREDICTIONS.map((prediction, index) => (
                  <div key={prediction.day} className="flex items-center gap-3">
                    <span className="w-8 text-sm font-medium text-zinc-600 dark:text-zinc-400">
                      {prediction.day}
                    </span>
                    <div className="flex-1 h-2 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                        style={{ width: `${prediction.score}%` }}
                      />
                    </div>
                    <span className="w-12 text-sm font-bold text-zinc-900 dark:text-zinc-100 text-right">
                      {prediction.score}%
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-zinc-200 dark:border-zinc-800">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-600 dark:text-zinc-400">Confidence</span>
                  <span className="font-bold text-green-600 dark:text-green-400">
                    87% Average
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div>
            <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              Quick Actions
            </h2>
            <div className="space-y-2">
              <button
                className="w-full flex items-center gap-3 px-4 py-3 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-lg font-medium hover:opacity-90 transition-opacity"
                onClick={() => window.location.href = '/code-editor'}
              >
                <span>💻</span>
                <span>Start Coding</span>
              </button>
              <button className="w-full flex items-center gap-3 px-4 py-3 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-700 rounded-lg font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">
                <span>📊</span>
                <span>View Analytics</span>
              </button>
              <button className="w-full flex items-center gap-3 px-4 py-3 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-700 rounded-lg font-medium hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">
                <span>🎯</span>
                <span>View Recommendations</span>
              </button>
            </div>
          </div>

          {/* System Status */}
          <div>
            <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
              System Status
            </h2>
            <div className="bg-white dark:bg-zinc-900 rounded-xl p-4 border border-zinc-200 dark:border-zinc-800 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-zinc-600 dark:text-zinc-400">SSE Connection</span>
                <span className={`font-bold ${
                  sse.getConnectionStatus().isConnected
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {sse.getConnectionStatus().isConnected ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-zinc-600 dark:text-zinc-400">Events Received</span>
                <span className="font-bold text-zinc-900 dark:text-zinc-100">
                  {sse.state.eventCount}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-zinc-600 dark:text-zinc-400">Last Update</span>
                <span className="font-bold text-zinc-900 dark:text-zinc-100">
                  {sse.state.lastEvent
                    ? new Date(sse.state.lastEvent.timestamp).toLocaleTimeString()
                    : 'Never'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper function to show toast notifications
function showToast(message: string, type: 'success' | 'info' | 'warning' | 'error' = 'info') {
  // Create toast container if it doesn't exist
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed top-4 right-4 z-50 space-y-2';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const colors = {
    success: 'bg-green-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  };

  toast.className = `${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-y-0 opacity-100 pointer-events-auto`;
  toast.innerHTML = `
    <div class="flex items-center gap-2">
      <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
      <span>${message}</span>
    </div>
  `;

  container.appendChild(toast);

  // Remove after 3 seconds
  setTimeout(() => {
    toast.style.transform = 'translateY(20px) translateX(100%)';
    toast.style.opacity = '0';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, 3000);
}