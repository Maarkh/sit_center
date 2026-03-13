import ReactECharts from 'echarts-for-react';
import type { ForecastPoint } from '@/types/forecasts';
import type { DataPoint } from '@/types/metrics';

interface Props {
  historical: DataPoint[];
  forecast: ForecastPoint[];
  title?: string;
  height?: number;
}

export default function ForecastChart({ historical, forecast, title, height = 400 }: Props) {
  const option = {
    title: title ? { text: title, left: 'center' } : undefined,
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['Historical', 'Forecast', 'Confidence Band'], bottom: 0 },
    xAxis: { type: 'time' as const },
    yAxis: { type: 'value' as const },
    series: [
      {
        name: 'Historical',
        type: 'line',
        data: historical.map((p) => [p.timestamp, p.value]),
        smooth: true,
      },
      {
        name: 'Forecast',
        type: 'line',
        data: forecast.map((p) => [p.timestamp, p.value]),
        lineStyle: { type: 'dashed' },
        smooth: true,
      },
      {
        name: 'Confidence Band',
        type: 'line',
        data: forecast.map((p) => [p.timestamp, p.upper]),
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0 },
        stack: 'band',
        symbol: 'none',
      },
      {
        name: 'Lower',
        type: 'line',
        data: forecast.map((p) => [p.timestamp, p.lower]),
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0.15, color: '#1677ff' },
        stack: 'band',
        symbol: 'none',
      },
    ],
    grid: { left: 60, right: 30, top: 40, bottom: 60 },
    dataZoom: [{ type: 'inside' }],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
