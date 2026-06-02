import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { UserInfo } from '@/types/auth';

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  getMe: vi.fn(),
  logout: vi.fn(),
}));

import { useAuthStore } from '../authStore';
import { login as apiLogin, getMe, logout as apiLogout } from '@/api/auth';

const mockUser: UserInfo = {
  username: 'testuser',
  scopes: ['user'],
  tenant_id: 'tenant-1',
  roles: ['operator'],
  permissions: ['read:alerts', 'write:alerts'],
};

const mockAdminUser: UserInfo = {
  username: 'admin',
  scopes: ['admin'],
  tenant_id: 'tenant-1',
  roles: ['admin'],
  permissions: [],
};

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({ user: null, isAuthenticated: false, loading: true });
  });

  it('has correct initial state', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('login sets the cookie (via apiLogin) then hydrates user from getMe', async () => {
    vi.mocked(apiLogin).mockResolvedValue({ access_token: 'tok123', token_type: 'bearer' });
    vi.mocked(getMe).mockResolvedValue(mockUser);

    await useAuthStore.getState().login('testuser', 'pass');

    expect(apiLogin).toHaveBeenCalledWith('testuser', 'pass');
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.loading).toBe(false);
  });

  it('logout calls the logout endpoint and clears state', async () => {
    vi.mocked(apiLogout).mockResolvedValue(undefined);
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, loading: false });

    await useAuthStore.getState().logout();

    expect(apiLogout).toHaveBeenCalled();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('logout clears state even if the network call fails', async () => {
    vi.mocked(apiLogout).mockRejectedValue(new Error('network'));
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, loading: false });

    await useAuthStore.getState().logout();

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it('checkAuth authenticates when the cookie is valid', async () => {
    vi.mocked(getMe).mockResolvedValue(mockUser);

    await useAuthStore.getState().checkAuth();

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.loading).toBe(false);
  });

  it('checkAuth clears auth when getMe rejects (no/invalid cookie)', async () => {
    vi.mocked(getMe).mockRejectedValue(new Error('401'));

    await useAuthStore.getState().checkAuth();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.loading).toBe(false);
  });

  it('hasPermission returns false when not logged in', () => {
    expect(useAuthStore.getState().hasPermission('read:alerts')).toBe(false);
  });

  it('hasPermission returns true for matching permission', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, loading: false });
    expect(useAuthStore.getState().hasPermission('read:alerts')).toBe(true);
  });

  it('hasPermission returns false for non-matching permission', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, loading: false });
    expect(useAuthStore.getState().hasPermission('delete:system')).toBe(false);
  });

  it('hasPermission returns true for admin regardless of specific permission', () => {
    useAuthStore.setState({ user: mockAdminUser, isAuthenticated: true, loading: false });
    expect(useAuthStore.getState().hasPermission('anything')).toBe(true);
  });

  it('isAdmin returns true when user has admin scope', () => {
    useAuthStore.setState({ user: mockAdminUser, isAuthenticated: true, loading: false });
    expect(useAuthStore.getState().isAdmin()).toBe(true);
  });

  it('isAdmin returns false when user lacks admin scope', () => {
    useAuthStore.setState({ user: mockUser, isAuthenticated: true, loading: false });
    expect(useAuthStore.getState().isAdmin()).toBe(false);
  });

  it('isAdmin returns false when not logged in', () => {
    expect(useAuthStore.getState().isAdmin()).toBe(false);
  });
});
