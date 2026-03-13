import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Spin } from 'antd';
import { AlertOutlined, FileTextOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { listAlerts } from '@/api/alerts';
import { listIncidents } from '@/api/incidents';
import StatusTag from '@/components/Common/StatusTag';
import PriorityTag from '@/components/Common/PriorityTag';
import { formatDateShort } from '@/utils/formatters';
import { useTranslation } from 'react-i18next';
import type { AlertRead } from '@/types/alerts';
import type { IncidentRead } from '@/types/incidents';

export default function DashboardPage() {
  const [alerts, setAlerts] = useState<AlertRead[]>([]);
  const [incidents, setIncidents] = useState<IncidentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    async function load() {
      try {
        const [a, i] = await Promise.all([
          listAlerts({ limit: 50 }),
          listIncidents({ limit: 50 }),
        ]);
        setAlerts(a);
        setIncidents(i.items || []);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const firingCount = alerts.filter((a) => a.status === 'firing').length;
  const acknowledgedCount = alerts.filter((a) => a.status === 'acknowledged').length;
  const openIncidents = incidents.filter((i) => !['resolved', 'closed'].includes(i.status)).length;
  const criticalIncidents = incidents.filter((i) => i.priority === 'critical' && !['resolved', 'closed'].includes(i.status)).length;

  const alertColumns = [
    { title: t('alerts.status'), dataIndex: 'status', key: 'status', render: (s: string) => <StatusTag status={s} /> },
    { title: t('alerts.metric'), dataIndex: 'metric_name', key: 'metric_name' },
    { title: t('alerts.value'), dataIndex: 'value', key: 'value', render: (v: number) => v?.toFixed(2) },
    { title: t('alerts.time'), dataIndex: 'detected_at', key: 'detected_at', render: formatDateShort },
  ];

  return (
    <>
      <Row gutter={[16, 16]}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.firing_alerts')} value={firingCount} prefix={<AlertOutlined />} valueStyle={{ color: firingCount > 0 ? '#ff4d4f' : '#52c41a' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.acknowledged')} value={acknowledgedCount} prefix={<WarningOutlined />} valueStyle={{ color: '#faad14' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.open_incidents')} value={openIncidents} prefix={<FileTextOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title={t('dashboard.critical')} value={criticalIncidents} prefix={<WarningOutlined />} valueStyle={{ color: criticalIncidents > 0 ? '#ff4d4f' : '#52c41a' }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title={t('dashboard.recent_alerts')} size="small">
            <Table dataSource={alerts.slice(0, 10)} columns={alertColumns} rowKey="id" pagination={false} size="small" />
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
