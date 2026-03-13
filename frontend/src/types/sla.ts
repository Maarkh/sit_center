export interface SlaPolicyRead {
  id: string;
  tenant_id: string;
  name: string;
  priority: string;
  response_time_minutes: number;
  resolution_time_minutes: number;
  escalation_after_minutes: number;
  is_active: boolean;
  created_at: string;
}

export interface SlaPolicyCreate {
  name: string;
  priority: string;
  response_time_minutes: number;
  resolution_time_minutes: number;
  escalation_after_minutes: number;
}
