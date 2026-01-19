/**
 * Authentication Hook - Bridge to Auth Context
 * Provides authentication functionality to components
 * Last Updated: 2026-01-15
 */

import { useAuth as useAuthContext } from '@/store/auth-context';

// Re-export the useAuth hook from auth context
export const useAuth = useAuthContext;

export default useAuth;