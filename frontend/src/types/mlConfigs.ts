export interface MLConfigRead {
  id: string;
  name: string;
  metric_name: string;
  group_by: string[];
  methods: string[];
  method_params: Record<string, unknown>;
  retrain_schedule: string;
  auto_alert: boolean;
  alert_severity: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MLConfigCreate {
  name: string;
  metric_name: string;
  group_by?: string[];
  methods: string[];
  method_params?: Record<string, unknown>;
  retrain_schedule?: string;
  auto_alert?: boolean;
  alert_severity?: string;
  is_active?: boolean;
}
