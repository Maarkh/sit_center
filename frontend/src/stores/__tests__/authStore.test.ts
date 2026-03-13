import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { TokenData } from '@/types/auth';

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
}));

vi.mock('@/utils/jwt', () => ({
  decodeToken: vi.fn(),
  isTokenExpired: vi.fn(),
}));

import { useAuthStore } from '../authStore';
import { login as apiLogin } from '@/api/auth';
import { decodeToken, isTokenExpired } from '@/utils/jwt';

const mockUser: TokenData = {
  sub: 'testuser',
  scopes: ['user'],
  tenant_id: 'tenant-1',
  roles: ['operator'],
  permissions: ['read:alerts', 'write:alerts'],
  exp: Math.floor(Date.now() / 1000) + 3600,
};

const mockAdminUser: TokenData = {
  sub: 'admin',
  scopes: ['admin'],
  tenant_id: 'tenant-1',
  roles: ['admin'],
  permissions: [],
  exp: Math.floor(Date.now() / 1000) + 3600,
};

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    useAuthStore.setState({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  });

  it('has correct initial state', () => {
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('login sets token, user, and isAuthenticated', async () => {
    vi.mocked(apiLogin).mockResolvedValue({ access_token: 'tok123', token_type: 'bearer' });
    vi.mocked(decodeToken).mockReturnValue(mockUser);

    await useAuthStore.getState().login('testuser', 'pass');

    const state = useAuthStore.getState();
    expect(state.token).toBe('tok123');
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(localStorage.getItem('token')).toBe('tok123');
  });

  it('logout clears state and localStorage', () => {
    useAuthStore.setState({ token: 'tok', user: mockUser, isAuthenticated: true });
    localStorage.setItem('token', 'tok');

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('initFromStorage restores from valid token', () => {
    localStorage.setItem('token', 'valid-token');
    vi.mocked(isTokenExpired).mockReturnValue(false);
    vi.mocked(decodeToken).mockReturnValue(mockUser);

    useAuthStore.getState().initFromStorage();

    const state = useAuthStore.getState();
    expect(state.token).toBe('valid-token');
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
  });

  it('initFromStorage clears expired token', () => {
    localStorage.setItem('token', 'expired-token');
    vi.mocked(isTokenExpired).mockReturnValue(true);

    useAuthStore.getState().initFromStorage();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('initFromStorage does nothing when no token in storage', () => {
    useAuthStore.getState().initFromStorage();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('hasPermission returns false when not logged in', () => {
    expect(useAuthStore.getState().hasPermission('read:alerts')).toBe(false);
  });

  it('hasPermission returns true for matching permission', () => {
    useAuthStore.setState({ token: 'tok', user: mockUser, isAuthenticated: true });
    expect(useAuthStore.getState().hasPermission('read:alerts')).toBe(true);
  });

  it('hasPermission returns false for non-matching permission', () => {
    useAuthStore.setState({ token: 'tok', user: mockUser, isAuthenticated: true });
    expect(useAuthStore.getState().hasPermission('delete:system')).toBe(false);
  });

  it('hasPermission returns true for admin regardless of specific permission', () => {
    useAuthStore.setState({ token: 'tok', user: mockAdminUser, isAuthenticated: true });
    expect(useAuthStore.getState().hasPermission('anything')).toBe(true);
  });

  it('isAdmin returns true when user has admin scope', () => {
    useAuthStore.setState({ token: 'tok', user: mockAdminUser, isAuthenticated: true });
    expect(useAuthStore.getState().isAdmin()).toBe(true);
  });

  it('isAdmin returns false when user lacks admin scope', () => {
    useAuthStore.setState({ token: 'tok', user: mockUser, isAuthenticated: true });
    expect(useAuthStore.getState().isAdmin()).toBe(false);
  });

  it('isAdmin returns false when not logged in', () => {
    expect(useAuthStore.getState().isAdmin()).toBe(false);
  });
});
