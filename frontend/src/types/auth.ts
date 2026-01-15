/**
 * Authentication Type Definitions
 * Last Updated: 2026-01-15
 */

export interface User {
  id: string;
  email: string;
  username: string;
  role: 'student' | 'instructor' | 'admin';
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresIn: number;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  role?: 'student' | 'instructor';
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
  refreshToken: () => Promise<void>;
}

export interface JWTPayload {
  sub: string;
  email: string;
  username: string;
  role: 'student' | 'instructor' | 'admin';
  iat: number;
  exp: number;
}

export interface APIError {
  message: string;
  status: number;
  code?: string;
  details?: Record<string, string[]>;
}