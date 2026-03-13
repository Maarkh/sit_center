export interface MetricRead {
  metric_name: string;
  display_name: string;
  description: string;
  unit: string;
  default_threshold: number | null;
  default_critical_threshold: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataPoint {
  timestamp: string;
  value: number;
  dimensions: Record<string, string>;
  tags: Record<string, string>;
}

export interface DataQueryResponse {
  metric_name: string;
  points: DataPoint[];
  total: number;
}
