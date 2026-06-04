import { useEffect, useState, useMemo } from 'react';
import { Table, Select, Space, Card, Button, Tag, App, Typography } from 'antd';
import { ReloadOutlined, CheckOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  listDeviations, getIndicatorTree, acknowledgeDeviation, resolveDeviation,
} from '@/api/dss';
import DeviationDetailDrawer from '@/components/Common/DeviationDetailDrawer';
import { formatDate } from '@/utils/formatters';
import { useTranslation } from 'react-i18next';
import type { DeviationRead, IndicatorTreeResponse } from '@/types/dss';

const { Text } = Typography;

const SEVERITY_COLOR: Record<string, string> = { critical: 'red', warning: 'orange' };
const STATUS_COLOR: Record<string, string> = { open: 'warning', acknowledged: 'processing', resolved: 'default' };

// Alerts are now DSS deviations (single detection pipeline). Each row is an indicator
// that left its corridor; chronic ones auto-open an incident (linked here).
export default function AlertsPage() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [deviations, setDeviations] = useState<DeviationRead[]>([]);
  const [names, setNames] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(false);
  // Honour a ?status= deep-link from the Dashboard KPI cards.
  const [statusFilter, setStatusFilter] = useState<string | undefined>(searchParams.get('status') || undefined);
  const [selected, setSelected] = useState<DeviationRead | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [devs, tree] = await Promise.all([
        listDeviations({ status: statusFilter, limit: 200 }),
        getIndicatorTree() as Promise<IndicatorTreeResponse>,
      ]);
      setDeviations(devs);
      const m = new Map<string, string>();
      tree.goals.forEach((g) => g.indicators.forEach((i) => m.set(i.id, i.name)));
      tree.unassigned.forEach((i) => m.set(i.id, i.name));
      setNames(m);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (id: string, action: 'ack' | 'resolve') => {
    if (action === 'ack') await acknowledgeDeviation(id);
    else await resolveDeviation(id);
    message.success(t('cockpit.statusUpdated'));
    fetchData();
  };

  const columns = useMemo(() => [
    { title: t('cockpit.severity'), dataIndex: 'severity', key: 'severity', width: 110,
      render: (s: string) => <Tag color={SEVERITY_COLOR[s] ?? 'default'}>{s}</Tag> },
    { title: t('cockpit.indicator'), key: 'indicator', ellipsis: true,
      render: (_: unknown, r: DeviationRead) => names.get(r.indicator_id) ?? r.indicator_id.slice(0, 8) },
    { title: t('cockpit.direction'), dataIndex: 'direction', key: 'direction', width: 90 },
    { title: t('cockpit.value'), dataIndex: 'value', key: 'value', width: 90,
      render: (v: number | null) => (v == null ? '-' : v.toFixed(2)) },
    { title: t('cockpit.periods'), dataIndex: 'periods', key: 'periods', width: 80 },
    { title: t('alerts.status'), dataIndex: 'status', key: 'status', width: 120,
      render: (s: string) => <Tag color={STATUS_COLOR[s] ?? 'default'}>{s}</Tag> },
    { title: t('cockpit.detected'), dataIndex: 'detected_at', key: 'detected_at', render: formatDate },
    { title: t('cockpit.incident'), dataIndex: 'incident_id', key: 'incident_id', width: 110,
      render: (id: number | null) => id
        ? <a onClick={(e) => { e.stopPropagation(); navigate(`/incidents/${id}`); }}>#{id}</a>
        : <Text type="secondary">—</Text> },
    {
      title: t('common.actions'), key: 'actions', width: 130,
      render: (_: unknown, r: DeviationRead) => r.status !== 'resolved' ? (
        // stop row-click (which opens the detail drawer) from firing on the buttons
        <Space onClick={(e) => e.stopPropagation()}>
          {r.status === 'open' && (
            <Button size="small" icon={<CheckOutlined />} onClick={() => act(r.id, 'ack')} />
          )}
          <Button size="small" onClick={() => act(r.id, 'resolve')}>{t('cockpit.resolve')}</Button>
        </Space>
      ) : null,
    },
  ], [names, t]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Card>
        <Space>
          <Select
            placeholder={t('alerts.filter_status')}
            options={[
              { label: t('cockpit.lightBreach'), value: 'open' },
              { label: t('alerts.acknowledged'), value: 'acknowledged' },
              { label: t('alerts.resolved'), value: 'resolved' },
            ]}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v || undefined)}
            allowClear
            style={{ width: 200 }}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchData}>{t('alerts.refresh')}</Button>
        </Space>
      </Card>
      <Table
        dataSource={deviations}
        columns={columns}
        rowKey="id"
        loading={loading}
        style={{ marginTop: 16 }}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        onRow={(r) => ({
          onClick: () => { setSelected(r); setDrawerOpen(true); },
          style: { cursor: 'pointer' },
        })}
      />
      <DeviationDetailDrawer
        deviation={selected}
        indicatorName={selected ? names.get(selected.indicator_id) : undefined}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}
