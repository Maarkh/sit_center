import client from './client';
import type { Token, UserInfo } from '@/types/auth';

export async function login(username: string, password: string): Promise<Token> {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  // The server sets the JWT as an httpOnly cookie; the body token is ignored by
  // the SPA (it can't be stored safely). Identity comes from getMe() below.
  const { data } = await client.post<Token>('/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data;
}

export async function getMe(): Promise<UserInfo> {
  const { data } = await client.get<UserInfo>('/auth/me');
  return data;
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout');
}
