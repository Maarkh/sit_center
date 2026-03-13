import client from './client';
import type { AlertRead } from '@/types/alerts';

export interface AlertFilters {
  status?: string;
  metric_name?: string;
  limit?: number;
  offset?: number;
}

export async function listAlerts(params: AlertFilters = {}): Promise<AlertRead[]> {
  const { data } = await client.get<AlertRead[]>('/api/v1/alerts', { params });
  return data;
}

export async function getAlert(id: string): Promise<AlertRead> {
  const { data } = await client.get<AlertRead>(`/api/v1/alerts/${id}`);
  return data;
}
