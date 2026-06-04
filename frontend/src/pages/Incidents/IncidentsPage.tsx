import { useEffect, useState } from 'react';
import { Table, Select, Space, Card, Button, Tag } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { listIncidents } from '@/api/incidents';
import StatusTag from '@/components/Common/StatusTag';
import PriorityTag from '@/components/Common/PriorityTag';
import SlaIndicator from '@/components/Common/SlaIndicator';
import { formatDate } from '@/utils/formatters';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { RU_CODE_TO_NAME } from '@/utils/ruRegions';
import { usePolling } from '@/hooks/usePolling';
import CreateIncidentModal from './CreateIncidentModal';
import type { IncidentRead } from '@/types/incidents';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentRead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t } = useTranslation();

  // URL is the source of truth for filters, so deep-links from the map / dashboard
  // (e.g. /incidents?region=RU-MOW, ?active=true, ?priority=critical) apply on arrival.
  const statusFilter = searchParams.get('status') || undefined;
  const priorityFilter = searchParams.get('priority') || undefined;
  const regionFilter = searchParams.get('region') || undefined;
  const activeFilter = searchParams.get('active') === 'true';

  const setParam = (key: string, value?: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value); else next.delete(key);
    setSearchParams(next);
    setPage(1);
  };

  const fetchData = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await listIncidents({
        status: statusFilter,
        priority: priorityFilter,
        region: regionFilter,
        active: activeFilter || undefined,
        limit: 20,
        offset: (page - 1) * 20,
      });
      setIncidents(data.items || []);
      setTotal(data.total || 0);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [statusFilter, priorityFilter, regionFilter, activeFilter, page]); // eslint-disable-line react-hooks/exhaustive-deps
  usePolling(() => fetchData(true)); // auto-refresh new/updated incidents

  const columns = [
    { title: t('incidents.id'), dataIndex: 'id', key: 'id', width: 70 },
    { title: t('incidents.priority'), dataIndex: 'priority', key: 'priority', width: 100, render: (p: string) => <PriorityTag priority={p} /> },
    { title: t('incidents.status'), dataIndex: 'status', key: 'status', width: 120, render: (s: string) => <StatusTag status={s} /> },
    { title: t('incidents.message'), dataIndex: 'alert_message', key: 'alert_message', ellipsis: true },
    { title: t('incidents.metric'), dataIndex: 'metric', key: 'metric' },
    { title: t('incidents.region'), dataIndex: 'region', key: 'region' },
    { title: t('incidents.assigned'), dataIndex: 'assigned_to', key: 'assigned_to' },
    { title: t('incidents.detected'), dataIndex: 'detected_at', key: 'detected_at', render: formatDate },
    {
      title: t('incidents.sla'), key: 'sla', width: 180,
      render: (_: unknown, r: IncidentRead) => (
        <SlaIndicator deadline={r.response_deadline} breached={r.response_breached} label={t('incidents.response')} />
      ),
    },
  ];

  return (
    <>
      <Card>
        <Space wrap>
          <Select placeholder={t('incidents.status')} options={[
            { label: t('incidents.new'), value: 'new' }, { label: t('incidents.in_progress'), value: 'in_progress' },
            { label: t('incidents.escalated'), value: 'escalated' }, { label: t('alerts.resolved'), value: 'resolved' },
            { label: t('incidents.closed'), value: 'closed' },
          ]} value={statusFilter} onChange={(v) => setParam('status', v || undefined)} allowClear style={{ width: 150 }} />
          <Select placeholder={t('incidents.priority')} options={[
            { label: t('common.critical'), value: 'critical' }, { label: t('common.high'), value: 'high' },
            { label: t('common.medium'), value: 'medium' }, { label: t('common.low'), value: 'low' },
          ]} value={priorityFilter} onChange={(v) => setParam('priority', v || undefined)} allowClear style={{ width: 150 }} />
          {activeFilter && (
            <Tag color="processing" closable onClose={() => setParam('active', undefined)}>
              {t('incidents.active_only', 'Только активные')}
            </Tag>
          )}
          {regionFilter && (
            <Tag color="geekblue" closable onClose={() => setParam('region', undefined)}>
              {t('incidents.region')}: {RU_CODE_TO_NAME[regionFilter] ?? regionFilter}
            </Tag>
          )}
          <Button icon={<ReloadOutlined />} onClick={() => fetchData()}>{t('incidents.refresh')}</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>{t('incidents.create')}</Button>
        </Space>
      </Card>
      <Table
        dataSource={incidents}
        columns={columns}
        rowKey="id"
        loading={loading}
        style={{ marginTop: 16 }}
        pagination={{ current: page, pageSize: 20, total, onChange: setPage }}
        onRow={(record) => ({ onClick: () => navigate(`/incidents/${record.id}`), style: { cursor: 'pointer' } })}
      />
      <CreateIncidentModal open={createOpen} onClose={() => setCreateOpen(false)} onCreated={fetchData} />
    </>
  );
}
