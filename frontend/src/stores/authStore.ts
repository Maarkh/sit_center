import { create } from 'zustand';
import { login as apiLogin } from '@/api/auth';
import { decodeToken, isTokenExpired } from '@/utils/jwt';
import type { TokenData } from '@/types/auth';

interface AuthState {
  token: string | null;
  user: TokenData | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  initFromStorage: () => void;
  hasPermission: (perm: string) => boolean;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  login: async (username, password) => {
    const result = await apiLogin(username, password);
    const decoded = decodeToken(result.access_token);
    localStorage.setItem('token', result.access_token);
    set({ token: result.access_token, user: decoded, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null, isAuthenticated: false });
  },

  initFromStorage: () => {
    const token = localStorage.getItem('token');
    if (token && !isTokenExpired(token)) {
      const decoded = decodeToken(token);
      set({ token, user: decoded, isAuthenticated: true });
    } else {
      localStorage.removeItem('token');
    }
  },

  hasPermission: (perm) => {
    const { user } = get();
    if (!user) return false;
    if (user.scopes?.includes('admin')) return true;
    return user.permissions?.includes(perm) ?? false;
  },

  isAdmin: () => {
    const { user } = get();
    return user?.scopes?.includes('admin') ?? false;
  },
}));
