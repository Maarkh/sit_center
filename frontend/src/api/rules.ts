import client from './client';
import type { RuleRead, RuleCreate } from '@/types/rules';

export async function listRules(): Promise<RuleRead[]> {
  const { data } = await client.get<RuleRead[]>('/api/v1/rules');
  return data;
}

export async function getRule(id: string): Promise<RuleRead> {
  const { data } = await client.get<RuleRead>(`/api/v1/rules/${id}`);
  return data;
}

export async function createRule(payload: RuleCreate): Promise<RuleRead> {
  const { data } = await client.post<RuleRead>('/api/v1/rules', payload);
  return data;
}

export async function updateRule(id: string, payload: RuleCreate): Promise<RuleRead> {
  const { data } = await client.put<RuleRead>(`/api/v1/rules/${id}`, payload);
  return data;
}

export async function deleteRule(id: string): Promise<void> {
  await client.delete(`/api/v1/rules/${id}`);
}
