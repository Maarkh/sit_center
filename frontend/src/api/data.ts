import client from './client';
import type { DataPoint } from '@/types/metrics';

export interface RegionMetricValue {
  region: string;
  value: number;
}

/**
 * Time series of a metric over the last `hours`, from canonical_metrics (TimescaleDB),
 * via the Prometheus-compatible range query. The metric may have many dimension series
 * (service×dc...) — they're aggregated to ONE mean line per time bin so the explorer
 * shows a clean overview by default.
 */
export async function getMetricSeries(metricName: string, hours = 24, step = '15m'): Promise<DataPoint[]> {
  const end = Math.floor(Date.now() / 1000);
  const start = end - hours * 3600;
  const { data } = await client.get('/api/v1/data/prometheus/api/v1/query_range', {
    params: { query: metricName, start, end, step },
  });
  const result = (data?.data?.result ?? []) as Array<{ values?: [number, string][] }>;
  const byTs = new Map<number, number[]>();
  for (const s of result) {
    for (const [ts, v] of s.values ?? []) {
      const arr = byTs.get(ts) ?? [];
      arr.push(parseFloat(v));
      byTs.set(ts, arr);
    }
  }
  return [...byTs.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([ts, vals]) => ({
      timestamp: new Date(ts * 1000).toISOString(),
      value: vals.reduce((sum, x) => sum + x, 0) / vals.length,
      dimensions: {},
      tags: {},
    }));
}

export async function getLatestMetricByRegion(metricName: string): Promise<RegionMetricValue[]> {
  const { data } = await client.get<RegionMetricValue[]>('/api/v1/data/latest-by-region', {
    params: { metric_name: metricName },
  });
  return data;
}
