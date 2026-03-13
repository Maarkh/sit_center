import EChart from '@/lib/EChart';

interface Props {
  value: number;
  title: string;
  max?: number;
  height?: number;
}

export default function GaugeChart({ value, title, max = 100, height = 200 }: Props) {
  const option = {
    series: [{
      type: 'gauge' as const,
      max,
      detail: { formatter: '{value}', fontSize: 20 },
      data: [{ value, name: title }],
      axisLine: {
        lineStyle: {
          width: 15,
          color: [[0.3, '#52c41a'], [0.7, '#faad14'], [1, '#ff4d4f']],
        },
      },
    }],
  };

  return <EChart option={option} style={{ height }} />;
}
