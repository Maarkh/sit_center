import client from './client';
import type { DataSource, SourceCreate, SourceTestResult } from '@/types/sources';

const BASE = '/api/v1/data-sources';

export async function listSources(): Promise<DataSource[]> {
  const { data } = await client.get<DataSource[]>(BASE);
  return data;
}

export async function createSource(payload: SourceCreate): Promise<DataSource> {
  const { data } = await client.post<DataSource>(BASE, payload);
  return data;
}

export async function updateSource(id: string, payload: SourceCreate): Promise<DataSource> {
  const { data } = await client.put<DataSource>(`${BASE}/${id}`, payload);
  return data;
}

export async function deleteSource(id: string): Promise<void> {
  await client.delete(`${BASE}/${id}`);
}

export async function testSource(id: string): Promise<SourceTestResult> {
  const { data } = await client.post<SourceTestResult>(`${BASE}/${id}/test`);
  return data;
}
