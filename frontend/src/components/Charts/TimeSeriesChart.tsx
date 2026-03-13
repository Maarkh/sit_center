import ReactECharts from 'echarts-for-react';
import type { DataPoint } from '@/types/metrics';

interface Props {
  data: DataPoint[];
  title?: string;
  height?: number;
}

export default function TimeSeriesChart({ data, title, height = 400 }: Props) {
  const option = {
    title: title ? { text: title, left: 'center' } : undefined,
    tooltip: { trigger: 'axis' as const },
    xAxis: {
      type: 'time' as const,
    },
    yAxis: {
      type: 'value' as const,
    },
    series: [{
      type: 'line',
      data: data.map((p) => [p.timestamp, p.value]),
      smooth: true,
      areaStyle: { opacity: 0.1 },
    }],
    grid: { left: 60, right: 30, top: 40, bottom: 40 },
    dataZoom: [{ type: 'inside' }, { type: 'slider' }],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
