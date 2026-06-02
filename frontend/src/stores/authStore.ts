import { create } from 'zustand';
import { login as apiLogin, getMe, logout as apiLogout } from '@/api/auth';
import type { UserInfo } from '@/types/auth';

interface AuthState {
  user: UserInfo | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  hasPermission: (perm: string) => boolean;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  // Start in loading state: on first paint we don't yet know if the auth cookie
  // is valid. checkAuth() resolves it; ProtectedRoute shows a spinner meanwhile.
  loading: true,

  login: async (username, password) => {
    await apiLogin(username, password); // server sets the httpOnly auth cookie
    const user = await getMe();
    set({ user, isAuthenticated: true, loading: false });
  },

  logout: async () => {
    try {
      await apiLogout();
    } catch {
      /* best-effort: clear local state regardless of the network result */
    }
    set({ user: null, isAuthenticated: false, loading: false });
  },

  checkAuth: async () => {
    try {
      const user = await getMe();
      set({ user, isAuthenticated: true, loading: false });
    } catch {
      set({ user: null, isAuthenticated: false, loading: false });
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
