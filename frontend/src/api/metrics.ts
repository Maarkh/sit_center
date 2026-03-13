import client from './client';
import type { MetricRead } from '@/types/metrics';

export async function listMetrics(): Promise<MetricRead[]> {
  const { data } = await client.get<MetricRead[]>('/api/v1/metrics');
  return data;
}

export async function getMetricNames(): Promise<string[]> {
  const { data } = await client.get('/api/v1/data/prometheus/api/v1/label/__name__/values');
  return data.data || data;
}

export async function getDimensionValues(label: string): Promise<string[]> {
  const { data } = await client.get(`/api/v1/data/prometheus/api/v1/label/${label}/values`);
  return data.data || data;
}
