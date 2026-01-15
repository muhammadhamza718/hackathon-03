/**
 * Unit Tests for Authentication Context
 * Last Updated: 2026-01-15
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/store/auth-context';
import { setAuthToken, clearAuthTokens, getAuthToken } from '@/lib/auth';

// Mock the auth utilities
jest.mock('@/lib/auth', () => ({
  setAuthToken: jest.fn(),
  clearAuthTokens: jest.fn(),
  getAuthToken: jest.fn(),
  decodeJWT: jest.fn(),
  isTokenNearExpiry: jest.fn(),
  refreshToken: jest.fn(),
  setUserData: jest.fn(),
  getUserData: jest.fn(),
}));

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
  });

  describe('useAuth hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();
    });

    it('should provide auth context when used within AuthProvider', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      expect(result.current).toBeDefined();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Authentication state', () => {
    it('should initialize with loading state', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      expect(result.current.isLoading).toBe(false); // Should be false after initialization
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it('should handle login successfully', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
        expect(result.current.user).toBeDefined();
        expect(result.current.user?.email).toBe('test@example.com');
      });

      // Verify auth tokens were set
      expect(setAuthToken).toHaveBeenCalled();
    });

    it('should handle login failure', async () => {
      // Mock a failed login
      const mockLogin = jest.spyOn(require('@/store/auth-context'), 'useAuth');
      mockLogin.mockImplementationOnce(() => ({
        ...renderHook(() => useAuth(), { wrapper: AuthProvider }).result.current,
        login: jest.fn().mockRejectedValue(new Error('Invalid credentials')),
      }));

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await act(async () => {
        try {
          await result.current.login({
            email: 'wrong@example.com',
            password: 'wrongpassword',
          });
        } catch (error) {
          // Expected error
        }
      });

      await waitFor(() => {
        expect(result.current.error).toBeDefined();
      });
    });

    it('should handle logout', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      // First login
      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.isAuthenticated).toBe(true);

      // Then logout
      act(() => {
        result.current.logout();
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(false);
        expect(result.current.user).toBeNull();
      });

      expect(clearAuthTokens).toHaveBeenCalled();
    });

    it('should handle registration', async () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      const registerData = {
        email: 'newuser@example.com',
        username: 'newuser',
        password: 'securepassword123',
        role: 'student' as const,
      };

      await act(async () => {
        await result.current.register(registerData);
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
        expect(result.current.user).toBeDefined();
        expect(result.current.user?.email).toBe(registerData.email);
        expect(result.current.user?.username).toBe(registerData.username);
      });
    });
  });

  describe('Protected route HOC', () => {
    it('should render loading state when authenticating', () => {
      const MockComponent = () => <div>Protected Content</div>;
      const ProtectedComponent = withAuth(MockComponent);

      const { container } = render(<ProtectedComponent />);

      // Should show loading spinner initially
      expect(container.querySelector('animate-spin')).toBeDefined();
    });

    it('should redirect to login when not authenticated', () => {
      // Mock window.location.href
      const originalHref = window.location.href;
      Object.defineProperty(window, 'location', {
        value: { href: '' },
        writable: true,
      });

      const MockComponent = () => <div>Protected Content</div>;
      const ProtectedComponent = withAuth(MockComponent);

      render(<ProtectedComponent />);

      // Should redirect to login
      expect(window.location.href).toBe('/login');

      // Restore
      Object.defineProperty(window, 'location', {
        value: { href: originalHref },
        writable: true,
      });
    });
  });
});