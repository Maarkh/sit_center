export interface ForecastPoint {
  timestamp: string;
  value: number;
  lower: number;
  upper: number;
}

export interface ForecastResponse {
  metric_name: string;
  dimensions: Record<string, string>;
  horizon_hours: number;
  points: ForecastPoint[];
}
