import client from './client';

export interface RegionMetricValue {
  region: string;
  value: number;
}

export async function getLatestMetricByRegion(metricName: string): Promise<RegionMetricValue[]> {
  const { data } = await client.get<RegionMetricValue[]>('/api/v1/data/latest-by-region', {
    params: { metric_name: metricName },
  });
  return data;
}
