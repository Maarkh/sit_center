import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Spin, Tag } from 'antd';
import { AlertOutlined, FileTextOutlined, WarningOutlined } from '@ant-design/icons';
import { listDeviations, getIndicatorTree } from '@/api/dss';
import { listIncidents } from '@/api/incidents';
import StatusTag from '@/components/Common/StatusTag';
import PriorityTag from '@/components/Common/PriorityTag';
import { formatDateShort } from '@/utils/formatters';
import { useTranslation } from 'react-i18next';
import type { DeviationRead } from '@/types/dss';
import type { IncidentRead } from '@/types/incidents';

const SEVERITY_COLOR: Record<string, string> = { critical: 'red', warning: 'orange' };

export default function DashboardPage() {
  const [deviations, setDeviations] = useState<DeviationRead[]>([]);
  const [incidents, setIncidents] = useState<IncidentRead[]>([]);
  const [names, setNames] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    async function load() {
      try {
        const [devs, i, tree] = await Promise.all([
          listDeviations({ limit: 50 }),
          listIncidents({ limit: 50 }),
          getIndicatorTree(),
        ]);
        setDeviations(devs);
        setIncidents(i.items || []);
        const m = new Map<string, string>();
        tree.goals.forEach((g) => g.indicators.forEach((ind) => m.set(ind.id, ind.name)));
        tree.unassigned.forEach((ind) => m.set(ind.id, ind.name));
        setNames(m);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const openCount = deviations.filter((d) => d.status === 'open').length;
  const ackCount = deviations.filter((d) => d.status === 'acknowledged').length;
  const openIncidents = incidents.filter((i) => !['resolved', 'closed'].includes(i.status)).length;
  const criticalIncidents = incidents.filter((i) => i.priority === 'critical' && !['resolved', 'closed'].includes(i.status)).length;

  const devColumns = [
    { title: t('cockpit.severity'), dataIndex: 'severity', key: 'severity',
      render: (s: string) => <Tag color={SEVERITY_COLOR[s] ?? 'default'}>{s}</Tag> },
    { title: t('cockpit.indicator'), key: 'indicator',
      render: (_: unknown, r: DeviationRead) => names.get(r.indicator_id) ?? r.indicator_id.slice(0, 8) },
    { title: t('alerts.value'), dataIndex: 'value', key: 'value', render: (v: number | null) => (v == null ? '-' : v.toFixed(2)) },
    { title: t('alerts.time'), dataIndex: 'detected_at', key: 'detected_at', render: formatDateShort },
  ];

  return (
    <>
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.firing_alerts')} value={openCount} prefix={<AlertOutlined />}
              styles={{ content: { color: openCount > 0 ? '#ff4d4f' : '#52c41a' } }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.acknowledged')} value={ackCount} prefix={<WarningOutlined />}
              styles={{ content: { color: '#faad14' } }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.open_incidents')} value={openIncidents} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.critical')} value={criticalIncidents} prefix={<WarningOutlined />}
              styles={{ content: { color: criticalIncidents > 0 ? '#ff4d4f' : '#52c41a' } }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title={t('dashboard.recent_alerts')} size="small">
            <Table dataSource={deviations.slice(0, 10)} columns={devColumns} rowKey="id" pagination={false} size="small" />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title={t('dashboard.open_incidents_table')} size="small">
            <Table
              dataSource={incidents.filter((i) => !['resolved', 'closed'].includes(i.status)).slice(0, 10)}
              columns={[
                { title: t('incidents.priority'), dataIndex: 'priority', key: 'priority', render: (p: string) => <PriorityTag priority={p} /> },
                { title: t('incidents.status'), dataIndex: 'status', key: 'status', render: (s: string) => <StatusTag status={s} /> },
                { title: t('incidents.metric'), dataIndex: 'metric', key: 'metric' },
                { title: t('incidents.region'), dataIndex: 'region', key: 'region' },
              ]}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </>
  );
}
