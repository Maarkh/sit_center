import client from './client';
import type {
  IncidentRead, IncidentCreate, IncidentStatusUpdate,
  IncidentCommentRead, IncidentListResponse,
} from '@/types/incidents';
import type { SlaPolicyRead, SlaPolicyCreate } from '@/types/sla';

export interface IncidentFilters {
  status?: string;
  priority?: string;
  assigned_to?: string;
  metric?: string;
  region?: string;
  active?: boolean;
  breached?: boolean;
  limit?: number;
  offset?: number;
}

export async function listIncidents(params: IncidentFilters = {}): Promise<IncidentListResponse> {
  // Trailing slash matters: '/api/v1/incidents' 307-redirects to '/api/v1/incidents/'
  // with an absolute backend URL, which the browser then follows cross-origin → CORS error.
  const { data } = await client.get<IncidentListResponse>('/api/v1/incidents/', { params });
  return data;
}

export async function getIncident(id: number): Promise<IncidentRead> {
  const { data } = await client.get<IncidentRead>(`/api/v1/incidents/${id}`);
  return data;
}

export async function createIncident(payload: IncidentCreate): Promise<IncidentRead> {
  const { data } = await client.post<IncidentRead>('/api/v1/incidents/', payload);
  return data;
}

export async function updateIncidentStatus(id: number, payload: IncidentStatusUpdate): Promise<IncidentRead> {
  // Backend route is PATCH /{id}/status — PUT/POST return 405 Method Not Allowed.
  const { data } = await client.patch<IncidentRead>(`/api/v1/incidents/${id}/status`, payload);
  return data;
}

export async function assignIncident(id: number, assigned_to: string, comment?: string): Promise<IncidentRead> {
  // Backend route is PATCH /{id}/assign — POST returns 405.
  const { data } = await client.patch<IncidentRead>(`/api/v1/incidents/${id}/assign`, { assigned_to, comment });
  return data;
}

export async function listComments(id: number): Promise<IncidentCommentRead[]> {
  const { data } = await client.get<IncidentCommentRead[]>(`/api/v1/incidents/${id}/comments`);
  return data;
}

export async function addComment(id: number, content: string): Promise<IncidentCommentRead> {
  const { data } = await client.post<IncidentCommentRead>(`/api/v1/incidents/${id}/comments`, { content });
  return data;
}

export async function listSlaPolicies(): Promise<SlaPolicyRead[]> {
  // Backend route is /sla/policies (not /sla-policies) — wrong path returns 404.
  const { data } = await client.get<SlaPolicyRead[]>('/api/v1/incidents/sla/policies');
  return data;
}

export async function createSlaPolicy(payload: SlaPolicyCreate): Promise<SlaPolicyRead> {
  const { data } = await client.post<SlaPolicyRead>('/api/v1/incidents/sla/policies', payload);
  return data;
}

export async function updateSlaPolicy(id: string, payload: SlaPolicyCreate): Promise<SlaPolicyRead> {
  const { data } = await client.put<SlaPolicyRead>(`/api/v1/incidents/sla/policies/${id}`, payload);
  return data;
}

export async function deleteSlaPolicy(id: string): Promise<void> {
  await client.delete(`/api/v1/incidents/sla/policies/${id}`);
}
