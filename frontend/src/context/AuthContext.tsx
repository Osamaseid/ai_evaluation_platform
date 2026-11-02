import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { TokenResponse, UserAccount, UserRole } from '../types/api';
import { api } from '../services/api';
import { useToast } from './ToastContext';

interface AuthContextType {
  user: TokenResponse | null;
  account: UserAccount | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isStudent: boolean;
  isInstructor: boolean;
  login: (emailOrUserId: string, password: string) => Promise<TokenResponse>;
  register: (payload: {
    user_id: string;
    email: string;
    password: string;
    role: 'student' | 'instructor';
    name: string;
  }) => Promise<UserAccount>;
  logout: () => Promise<void>;
  quickLogin: (role: 'student' | 'instructor') => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<TokenResponse | null>(() => {
    const cached = localStorage.getItem('autograde_user');
    return cached ? JSON.parse(cached) : null;
  });
  const [account, setAccount] = useState<UserAccount | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { success, error: showError } = useToast();

  const fetchCurrentAccount = useCallback(async () => {
    if (!api.getToken()) {
      setIsLoading(false);
      return;
    }
    try {
      const acc = await api.getCurrentUser();
      setAccount(acc);
    } catch (err) {
      console.warn('Could not fetch active account profile:', err);
      // If token expired or invalid, reset
      setUser(null);
      setAccount(null);
      api.setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentAccount();
  }, [fetchCurrentAccount]);

  const login = async (emailOrUserId: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await api.login({ email_or_user_id: emailOrUserId, password });
      setUser(resp);
      const acc = await api.getCurrentUser();
      setAccount(acc);
      success(`Welcome back, ${resp.name}!`, `Signed in as ${resp.role}`);
      return resp;
    } catch (err: any) {
      showError('Authentication Failed', err.message || 'Invalid credentials');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: {
    user_id: string;
    email: string;
    password: string;
    role: 'student' | 'instructor';
    name: string;
  }) => {
    setIsLoading(true);
    try {
      const acc = await api.register(payload);
      success('Account Created', `Successfully registered as ${payload.role}. Please log in.`);
      return acc;
    } catch (err: any) {
      showError('Registration Failed', err.message || 'Could not create account');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.warn('Logout notification error:', err);
    } finally {
      setUser(null);
      setAccount(null);
      success('Signed Out', 'You have been logged out.');
    }
  };

  // Quick provision & login helper for seamless testing of Student and Instructor roles
  const quickLogin = async (targetRole: 'student' | 'instructor') => {
    const demoCreds =
      targetRole === 'student'
        ? {
            user_id: 'student_ada',
            email: 'ada@university.edu',
            password: 'studentPassword123',
            name: 'Ada Lovelace',
            role: 'student' as const,
          }
        : {
            user_id: 'prof_turing',
            email: 'turing@university.edu',
            password: 'instructorPassword123',
            name: 'Prof. Alan Turing',
            role: 'instructor' as const,
          };

    try {
      // First try login directly
      await login(demoCreds.user_id, demoCreds.password);
    } catch {
      // If user doesn't exist yet, register first then login
      try {
        await api.register(demoCreds);
        await login(demoCreds.user_id, demoCreds.password);
      } catch (regErr: any) {
        showError('Quick Login Failed', regErr.message);
      }
    }
  };

  const refreshProfile = async () => {
    await fetchCurrentAccount();
  };

  const isStudent = user?.role === 'student';
  const isInstructor = user?.role === 'instructor' || user?.role === 'admin';

  return (
    <AuthContext.Provider
      value={{
        user,
        account,
        token: api.getToken(),
        isAuthenticated: !!user && !!api.getToken(),
        isLoading,
        isStudent,
        isInstructor,
        login,
        register,
        logout,
        quickLogin,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

