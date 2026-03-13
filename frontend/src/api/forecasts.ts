import client from './client';
import type { ForecastResponse } from '@/types/forecasts';

export async function predict(metricName: string, horizonHours = 24): Promise<ForecastResponse> {
  const { data } = await client.get<ForecastResponse>('/api/v1/forecasts/predict', {
    params: { metric_name: metricName, horizon_hours: horizonHours },
  });
  return data;
}
