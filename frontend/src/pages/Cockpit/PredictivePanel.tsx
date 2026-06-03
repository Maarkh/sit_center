import { useEffect, useState, useMemo } from 'react';
import { Card, Table, Tag, Button, Space, Empty, Typography, App } from 'antd';
import { ReloadOutlined, CheckOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import EChart from '@/lib/EChart';
import { formatDate } from '@/utils/formatters';
import client from '@/api/client';
import { listPredictiveAlerts, getIndicatorTree, getLatestForecast } from '@/api/dss';
import type {
  PredictiveAlertRead, IndicatorTreeResponse, ForecastRead, IndicatorTreeNode,
} from '@/types/dss';

const { Text } = Typography;

function flatten(tree: IndicatorTreeResponse): Map<string, IndicatorTreeNode> {
  const m = new Map<string, IndicatorTreeNode>();
  tree.goals.forEach((g) => g.indicators.forEach((i) => m.set(i.id, i)));
  tree.unassigned.forEach((i) => m.set(i.id, i));
  return m;
}

export default function PredictivePanel() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [alerts, setAlerts] = useState<PredictiveAlertRead[]>([]);
  const [indicators, setIndicators] = useState<Map<string, IndicatorTreeNode>>(new Map());
  const [forecast, setForecast] = useState<ForecastRead | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [al, tr] = await Promise.all([listPredictiveAlerts({ active_only: false }), getIndicatorTree()]);
      setAlerts(al);
      setIndicators(flatten(tr));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const showForecast = async (indicatorId: string) => {
    setSelected(indicatorId);
    try {
      setForecast(await getLatestForecast(indicatorId));
    } catch {
      setForecast(null);
    }
  };

  const ack = async (id: string, action: 'acknowledge' | 'resolve') => {
    await client.post(`/api/v1/predictions/${id}/${action}`, {});
    message.success(t('cockpit.statusUpdated'));
    fetchAll();
  };

  const chartOption = useMemo(() => {
    if (!forecast) return null;
    const ind = selected ? indicators.get(selected) : undefined;
    const pts = forecast.points;
    const low = ind?.target_low ?? null;
    const high = ind?.target_high ?? null;
    const markData: Array<Record<string, unknown>> = [];
    if (low != null) markData.push({ yAxis: low, lineStyle: { color: '#52c41a' }, label: { formatter: `${t('cockpit.corridorLow')} ${low}` } });
    if (high != null) markData.push({ yAxis: high, lineStyle: { color: '#cf1322' }, label: { formatter: `${t('cockpit.corridorHigh')} ${high}` } });
    return {
      tooltip: { trigger: 'axis' as const },
      legend: { data: [t('cockpit.forecast'), t('cockpit.band')], bottom: 0 },
      xAxis: { type: 'time' as const },
      yAxis: { type: 'value' as const },
      grid: { left: 55, right: 20, top: 20, bottom: 50 },
      series: [
        {
          name: t('cockpit.forecast'), type: 'line' as const, smooth: true, symbol: 'none',
          data: pts.map((p) => [p.ts, p.yhat]),
          markLine: markData.length ? { silent: true, symbol: 'none', data: markData } : undefined,
        },
        {
          name: '_low', type: 'line' as const, stack: 'band', symbol: 'none', lineStyle: { opacity: 0 },
          data: pts.map((p) => [p.ts, p.yhat_low ?? p.yhat]),
        },
        {
          name: t('cockpit.band'), type: 'line' as const, stack: 'band', symbol: 'none',
          lineStyle: { opacity: 0 }, areaStyle: { opacity: 0.15, color: '#1677ff' },
          data: pts.map((p) => [p.ts, (p.yhat_high ?? p.yhat) - (p.yhat_low ?? p.yhat)]),
        },
      ],
    };
  }, [forecast, selected, indicators, t]);

  const columns = [
    { title: t('cockpit.indicator'), key: 'indicator', ellipsis: true,
      render: (_: unknown, r: PredictiveAlertRead) => indicators.get(r.indicator_id)?.name ?? r.indicator_id.slice(0, 8) },
    { title: t('cockpit.direction'), dataIndex: 'direction', key: 'direction', width: 90 },
    { title: t('cockpit.projected'), dataIndex: 'projected_value', key: 'projected_value', width: 110,
      render: (v: number | null) => (v == null ? '-' : v.toFixed(2)) },
    { title: t('cockpit.breachEta'), dataIndex: 'breach_eta', key: 'breach_eta', render: formatDate },
    { title: t('cockpit.confidence'), dataIndex: 'confidence', key: 'confidence', width: 110,
      render: (c: string) => <Tag color={c === 'high' ? 'red' : 'orange'}>{c}</Tag> },
    { title: t('cockpit.status'), dataIndex: 'status', key: 'status', width: 120,
      render: (s: string) => <Tag color={s === 'resolved' ? 'default' : s === 'acknowledged' ? 'blue' : 'warning'}>{s}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 130,
      render: (_: unknown, r: PredictiveAlertRead) => r.status === 'open' ? (
        <Space>
          <Button size="small" icon={<CheckOutlined />} onClick={(e) => { e.stopPropagation(); ack(r.id, 'acknowledge'); }} />
          <Button size="small" onClick={(e) => { e.stopPropagation(); ack(r.id, 'resolve'); }}>{t('cockpit.resolve')}</Button>
        </Space>
      ) : null,
    },
  ];

  return (
    <>
      <Card
        title={t('cockpit.predictiveAlerts')}
        loading={loading}
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={fetchAll} />}
      >
        {alerts.length === 0
          ? <Empty description={t('cockpit.noPredictive')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          : <Table size="small" rowKey="id" dataSource={alerts} columns={columns} pagination={false}
              onRow={(r) => ({ onClick: () => showForecast(r.indicator_id), style: { cursor: 'pointer' } })} />}
      </Card>

      <Card style={{ marginTop: 16 }}
        title={t('cockpit.forecastChart') + (selected ? ` — ${indicators.get(selected)?.name ?? ''}` : '')}>
        {chartOption
          ? <EChart option={chartOption} style={{ height: 340 }} />
          : <Text type="secondary">{t('cockpit.selectForForecast')}</Text>}
      </Card>
    </>
  );
}
