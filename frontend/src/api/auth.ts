import client from './client';
import type { Token } from '@/types/auth';

export async function login(username: string, password: string): Promise<Token> {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  const { data } = await client.post<Token>('/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data;
}
