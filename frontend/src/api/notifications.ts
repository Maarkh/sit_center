import client from './client';
import type { NotificationChannel, ChannelCreate } from '@/types/notifications';

export async function listChannels(): Promise<NotificationChannel[]> {
  const { data } = await client.get<NotificationChannel[]>('/api/v1/notifications/channels');
  return data;
}

export async function createChannel(payload: ChannelCreate): Promise<NotificationChannel> {
  const { data } = await client.post<NotificationChannel>('/api/v1/notifications/channels', payload);
  return data;
}

export async function updateChannel(id: string, payload: ChannelCreate): Promise<NotificationChannel> {
  const { data } = await client.put<NotificationChannel>(`/api/v1/notifications/channels/${id}`, payload);
  return data;
}

export async function deleteChannel(id: string): Promise<void> {
  await client.delete(`/api/v1/notifications/channels/${id}`);
}

export async function testChannel(id: string): Promise<{ ok: boolean; error?: string }> {
  const { data } = await client.post<{ ok: boolean; error?: string }>(`/api/v1/notifications/channels/${id}/test`);
  return data;
}
