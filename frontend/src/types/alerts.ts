export type AlertStatus = 'firing' | 'acknowledged' | 'resolved';

export interface AlertRead {
  id: string;
  rule_id: string | null;
  ml_config_id: string | null;
  metric_name: string;
  dimensions: Record<string, string>;
  value: number;
  event_time: string;
  detected_at: string;
  status: AlertStatus;
  sent: boolean;
  fingerprint: string;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  resolved_by: string | null;
}
