/**
 * Authentication Context and Provider
 * Last Updated: 2026-01-15
 */

'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import {
  AuthContextType,
  AuthState,
  LoginCredentials,
  RegisterData,
  User,
} from '@/types/auth';
import {
  getAuthToken,
  setAuthToken,
  clearAuthTokens,
  decodeJWT,
  isTokenNearExpiry,
  refreshToken,
  setUserData,
  getUserData,
} from '@/lib/auth';

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth Provider Component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  // Token refresh interval
  useEffect(() => {
    if (!authState.isAuthenticated) return;

    const interval = setInterval(() => {
      const token = getAuthToken();
      if (token && isTokenNearExpiry(token)) {
        handleRefreshToken();
      }
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [authState.isAuthenticated]);

  const initializeAuth = useCallback(async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        setAuthState((prev) => ({ ...prev, isLoading: false }));
        return;
      }

      if (isTokenNearExpiry(token)) {
        const newToken = await refreshToken();
        if (!newToken) {
          clearAuthTokens();
          setAuthState((prev) => ({
            ...prev,
            isLoading: false,
            isAuthenticated: false,
          }));
          return;
        }
      }

      const payload = decodeJWT(token);
      if (!payload) {
        clearAuthTokens();
        setAuthState((prev) => ({ ...prev, isLoading: false }));
        return;
      }

      // Get user data from localStorage or create from JWT
      let user = getUserData();
      if (!user) {
        user = {
          id: payload.sub,
          email: payload.email,
          username: payload.username,
          role: payload.role,
        };
        setUserData(user);
      }

      setAuthState({
        user,
        tokens: { accessToken: token, expiresIn: payload.exp },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Auth initialization failed:', error);
      clearAuthTokens();
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        isAuthenticated: false,
        error: 'Failed to initialize authentication',
      }));
    }
  }, []);

  const handleRefreshToken = useCallback(async () => {
    try {
      const newToken = await refreshToken();
      if (newToken) {
        const payload = decodeJWT(newToken);
        if (payload) {
          setAuthState((prev) => ({
            ...prev,
            tokens: { accessToken: newToken, expiresIn: payload.exp },
          }));
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      handleLogout();
    }
  }, []);

  const handleLogin = useCallback(async (credentials: LoginCredentials) => {
    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(credentials),
      // });

      // Mock API response for development
      const mockResponse = {
        accessToken: 'mock-jwt-token',
        user: {
          id: 'student_001',
          email: credentials.email,
          username: credentials.email.split('@')[0],
          role: 'student',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      };

      // In production, use actual response:
      // if (!response.ok) throw new Error('Login failed');
      // const data = await response.json();

      const data = mockResponse;

      // Store token and user data
      setAuthToken(data.accessToken);
      setUserData(data.user);

      setAuthState({
        user: data.user,
        tokens: { accessToken: data.accessToken, expiresIn: Math.floor(Date.now() / 1000) + 3600 },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Login failed:', error);
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Invalid credentials. Please try again.',
      }));
      throw error;
    }
  }, []);

  const handleLogout = useCallback(() => {
    clearAuthTokens();
    setAuthState({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);

  const handleRegister = useCallback(async (data: RegisterData) => {
    setAuthState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      // TODO: Replace with actual API call
      // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(data),
      // });

      // Mock API response for development
      const mockResponse = {
        accessToken: 'mock-jwt-token',
        user: {
          id: 'student_new',
          email: data.email,
          username: data.username,
          role: (data.role as 'student' | 'instructor') || 'student',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        },
      };

      // In production, use actual response:
      // if (!response.ok) throw new Error('Registration failed');
      // const data = await response.json();

      const responseData = mockResponse;

      // Store token and user data
      setAuthToken(responseData.accessToken);
      setUserData(responseData.user);

      setAuthState({
        user: responseData.user,
        tokens: { accessToken: responseData.accessToken, expiresIn: Math.floor(Date.now() / 1000) + 3600 },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      console.error('Registration failed:', error);
      setAuthState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Registration failed. Please try again.',
      }));
      throw error;
    }
  }, []);

  const contextValue: AuthContextType = {
    user: authState.user,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    error: authState.error,
    login: handleLogin,
    logout: handleLogout,
    register: handleRegister,
    refreshToken: handleRefreshToken,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Protected route HOC
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  requiredRole?: string[]
) {
  return function WithAuthWrapper(props: P) {
    const { isAuthenticated, user, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    if (requiredRole && user && !requiredRole.includes(user.role)) {
      // Redirect to unauthorized page
      if (typeof window !== 'undefined') {
        window.location.href = '/unauthorized';
      }
      return null;
    }

    return <Component {...props} />;
  };
}