import client from './client';
import type { MLConfigRead, MLConfigCreate } from '@/types/mlConfigs';

export async function listMLConfigs(): Promise<MLConfigRead[]> {
  const { data } = await client.get<MLConfigRead[]>('/api/v1/ml/configs/');
  return data;
}

export async function createMLConfig(payload: MLConfigCreate): Promise<MLConfigRead> {
  const { data } = await client.post<MLConfigRead>('/api/v1/ml/configs/', payload);
  return data;
}

export async function updateMLConfig(id: string, payload: MLConfigCreate): Promise<MLConfigRead> {
  const { data } = await client.put<MLConfigRead>(`/api/v1/ml/configs/${id}`, payload);
  return data;
}

export async function deleteMLConfig(id: string): Promise<void> {
  await client.delete(`/api/v1/ml/configs/${id}`);
}
