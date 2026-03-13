import client from './client';
import type { AuditLogEntry } from '@/types/audit';

export interface AuditFilters {
  action?: string;
  resource_type?: string;
  username?: string;
  limit?: number;
  offset?: number;
}

export async function listAuditLogs(params: AuditFilters = {}): Promise<AuditLogEntry[]> {
  const { data } = await client.get<AuditLogEntry[]>('/api/v1/audit/logs', { params });
  return data;
}
