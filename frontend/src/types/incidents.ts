export type IncidentStatus = 'new' | 'in_progress' | 'escalated' | 'resolved' | 'closed';
export type Priority = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface IncidentRead {
  id: number;
  alert_message: string;
  metric: string;
  region: string;
  value: string | null;
  priority: string;
  status: IncidentStatus;
  detected_at: string;
  assigned_to: string | null;
  started_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  description: string | null;
  alert_event_id: string | null;
  response_deadline: string | null;
  resolution_deadline: string | null;
  response_breached: boolean;
  resolution_breached: boolean;
  escalation_level: number;
  last_escalated_at: string | null;
  external_id: string | null;
  external_system: string | null;
  external_url: string | null;
}

export interface IncidentCreate {
  alert_message: string;
  metric: string;
  region: string;
  value?: string;
  priority: string;
  description?: string;
  assigned_to?: string;
}

export interface IncidentStatusUpdate {
  status: IncidentStatus;
  comment?: string;
}

export interface IncidentCommentRead {
  id: number;
  incident_id: number;
  author: string;
  content: string;
  created_at: string;
}

export interface IncidentListResponse {
  items: IncidentRead[];
  total: number;
}

export const VALID_TRANSITIONS: Record<IncidentStatus, IncidentStatus[]> = {
  new: ['in_progress', 'closed'],
  in_progress: ['escalated', 'resolved', 'closed'],
  escalated: ['in_progress', 'resolved', 'closed'],
  resolved: ['closed', 'in_progress'],
  closed: [],
};
