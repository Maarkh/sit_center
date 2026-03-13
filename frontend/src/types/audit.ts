export interface AuditLogEntry {
  id: number;
  username: string;
  tenant_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  changes: Record<string, unknown> | null;
  ip_address: string | null;
  timestamp: string;
}
