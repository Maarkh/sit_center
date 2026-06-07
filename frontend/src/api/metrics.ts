import client from './client';
import type { MetricRead, MetricCreate } from '@/types/metrics';

export async function listMetrics(activeOnly = true): Promise<MetricRead[]> {
  // Trailing slash avoids a 307 → absolute cross-origin redirect → CORS error.
  const { data } = await client.get<MetricRead[]>('/api/v1/metrics/', { params: { active_only: activeOnly } });
  return data;
}

export async function createMetric(payload: MetricCreate): Promise<MetricRead> {
  const { data } = await client.post<MetricRead>('/api/v1/metrics/', payload);
  return data;
}

export async function updateMetric(name: string, payload: MetricCreate): Promise<MetricRead> {
  const { data } = await client.put<MetricRead>(`/api/v1/metrics/${encodeURIComponent(name)}`, payload);
  return data;
}

export async function deleteMetric(name: string): Promise<void> {
  await client.delete(`/api/v1/metrics/${encodeURIComponent(name)}`);
}

export async function getMetricNames(): Promise<string[]> {
  const { data } = await client.get('/api/v1/data/prometheus/api/v1/label/__name__/values');
  return data.data || data;
}

export async function getDimensionValues(label: string): Promise<string[]> {
  const { data } = await client.get(`/api/v1/data/prometheus/api/v1/label/${label}/values`);
  return data.data || data;
}
