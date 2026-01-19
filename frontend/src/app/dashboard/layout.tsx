/**
 * Dashboard Layout Component
 * Provides navigation and main layout for dashboard pages
 * Last Updated: 2026-01-15
 */

"use client";

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useSSE } from '@/lib/sse';

// Dashboard navigation items
const NAV_ITEMS = [
  { name: 'Overview', href: '/dashboard', icon: '🏠' },
  { name: 'Code Editor', href: '/code-editor', icon: '💻' },
  { name: 'Progress', href: '/dashboard/progress', icon: '📊' },
  { name: 'Recommendations', href: '/dashboard/recommendations', icon: '🎯' },
  { name: 'Settings', href: '/dashboard/settings', icon: '⚙️' },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);

  // SSE connection for real-time notifications
  const sse = useSSE();

  // Track real-time events for notification badge
  useEffect(() => {
    const unsubscribe = sse.subscribeToAll((event) => {
      if (event.priority === 'high') {
        setNotificationCount(prev => prev + 1);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [sse]);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const clearNotifications = () => {
    setNotificationCount(0);
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
            aria-label="Toggle menu"
          >
            <span className="text-xl">☰</span>
          </button>
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Real-Time Platform
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearNotifications}
            className="relative p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
            aria-label="Notifications"
          >
            <span className="text-xl">🔔</span>
            {notificationCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {notificationCount}
              </span>
            )}
          </button>
          <div className="w-8 h-8 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-sm font-medium">
            {user?.name?.charAt(0) || 'U'}
          </div>
        </div>
      </div>

      <div className="flex min-h-screen">
        {/* Sidebar */}
        <aside
          className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 transform transition-transform duration-200 ease-in-out ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
        >
          <div className="h-full flex flex-col">
            {/* Logo Area */}
            <div className="hidden lg:flex items-center gap-3 px-6 py-4 border-b border-zinc-200 dark:border-zinc-800">
              <div className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 flex items-center justify-center">
                <span className="text-white dark:text-zinc-900 font-bold">R</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                  Real-Time Platform
                </h1>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Learning Dashboard
                </p>
              </div>
            </div>

            {/* User Info */}
            <div className="px-4 py-4 border-b border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-lg font-medium">
                  {user?.name?.charAt(0) || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate">
                    {user?.name || 'User'}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 truncate">
                    {user?.email || 'user@example.com'}
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
              {NAV_ITEMS.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      router.push(item.href);
                      setSidebarOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                        : 'text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800'
                    }`}
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.name}</span>
                  </button>
                );
              })}
            </nav>

            {/* Connection Status */}
            <div className="px-4 py-3 border-t border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${
                  sse.getConnectionStatus().isConnected
                    ? 'bg-green-500'
                    : sse.getConnectionStatus().isConnecting
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`} />
                <span className="text-zinc-600 dark:text-zinc-400">
                  {sse.getConnectionStatus().isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {sse.getConnectionStatus().error && (
                <p className="text-xs text-red-500 mt-1 truncate">
                  {sse.getConnectionStatus().error}
                </p>
              )}
            </div>

            {/* Logout Button */}
            <div className="px-2 py-3 border-t border-zinc-200 dark:border-zinc-800">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              >
                <span>🚪</span>
                <span>Logout</span>
              </button>
            </div>
          </div>
        </aside>

        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          {/* Top Bar */}
          <div className="hidden lg:flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
            <div>
              <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
                {NAV_ITEMS.find(item => item.href === pathname)?.name || 'Dashboard'}
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Welcome back, {user?.name?.split(' ')[0] || 'Learner'}!
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={clearNotifications}
                className="relative p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                aria-label="Clear notifications"
              >
                <span className="text-xl">🔔</span>
                {notificationCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
                    {notificationCount}
                  </span>
                )}
              </button>
              <div className="w-8 h-8 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center text-sm font-medium">
                {user?.name?.charAt(0) || 'U'}
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="p-4 lg:p-6">
            {children}
          </div>
        </main>
      </div>

      {/* Toast Notification Container */}
      <div
        className="fixed bottom-4 right-4 z-50 space-y-2 pointer-events-none"
        id="toast-container"
      />
    </div>
  );
}