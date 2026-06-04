import client from './client';
import type { EscalationChain, EscalationChainCreate } from '@/types/escalation';

export async function listChains(): Promise<EscalationChain[]> {
  const { data } = await client.get<EscalationChain[]>('/api/v1/escalation/chains');
  return data;
}

export async function createChain(payload: EscalationChainCreate): Promise<EscalationChain> {
  const { data } = await client.post<EscalationChain>('/api/v1/escalation/chains', payload);
  return data;
}

export async function updateChain(id: string, payload: EscalationChainCreate): Promise<EscalationChain> {
  const { data } = await client.put<EscalationChain>(`/api/v1/escalation/chains/${id}`, payload);
  return data;
}

export async function deleteChain(id: string): Promise<void> {
  await client.delete(`/api/v1/escalation/chains/${id}`);
}
