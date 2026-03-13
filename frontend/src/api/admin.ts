import client from './client';
import type { TenantRead, TenantCreate, UserRead, UserCreate, RoleRead, RoleCreate } from '@/types/admin';

export async function listTenants(): Promise<TenantRead[]> {
  const { data } = await client.get<TenantRead[]>('/api/v1/admin/tenants');
  return data;
}

export async function createTenant(payload: TenantCreate): Promise<TenantRead> {
  const { data } = await client.post<TenantRead>('/api/v1/admin/tenants', payload);
  return data;
}

export async function listUsers(): Promise<UserRead[]> {
  const { data } = await client.get<UserRead[]>('/api/v1/admin/users');
  return data;
}

export async function createUser(payload: UserCreate): Promise<UserRead> {
  const { data } = await client.post<UserRead>('/api/v1/admin/users', payload);
  return data;
}

export async function listRoles(): Promise<RoleRead[]> {
  const { data } = await client.get<RoleRead[]>('/api/v1/admin/roles');
  return data;
}

export async function createRole(payload: RoleCreate): Promise<RoleRead> {
  const { data } = await client.post<RoleRead>('/api/v1/admin/roles', payload);
  return data;
}

export async function assignRole(userId: string, roleId: string): Promise<void> {
  await client.post(`/api/v1/admin/users/${userId}/roles/${roleId}`);
}
