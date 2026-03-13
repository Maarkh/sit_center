import { useEffect, useState } from 'react';
import { Table, Select, Space, Card, Button } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import { listIncidents } from '@/api/incidents';
import StatusTag from '@/components/Common/StatusTag';
import PriorityTag from '@/components/Common/PriorityTag';
import SlaIndicator from '@/components/Common/SlaIndicator';
import { formatDate } from '@/utils/formatters';
import { useNavigate } from 'react-router-dom';
import CreateIncidentModal from './CreateIncidentModal';
import type { IncidentRead } from '@/types/incidents';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentRead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [priorityFilter, setPriorityFilter] = useState<string | undefined>();
  const [createOpen, setCreateOpen] = useState(false);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await listIncidents({
        status: statusFilter,
        priority: priorityFilter,
        limit: 20,
        offset: (page - 1) * 20,
      });
      setIncidents(data.items || []);
      setTotal(data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [statusFilter, priorityFilter, page]);

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 100, render: (p: string) => <PriorityTag priority={p} /> },
    { title: 'Status', dataIndex: 'status', key: 'status', width: 120, render: (s: string) => <StatusTag status={s} /> },
    { title: 'Message', dataIndex: 'alert_message', key: 'alert_message', ellipsis: true },
    { title: 'Metric', dataIndex: 'metric', key: 'metric' },
    { title: 'Region', dataIndex: 'region', key: 'region' },
    { title: 'Assigned', dataIndex: 'assigned_to', key: 'assigned_to' },
    { title: 'Detected', dataIndex: 'detected_at', key: 'detected_at', render: formatDate },
    {
      title: 'SLA', key: 'sla', width: 180,
      render: (_: unknown, r: IncidentRead) => (
        <SlaIndicator deadline={r.response_deadline} breached={r.response_breached} label="Resp" />
      ),
    },
  ];

  return (
    <>
      <Card>
        <Space wrap>
          <Select placeholder="Status" options={[
            { label: 'New', value: 'new' }, { label: 'In Progress', value: 'in_progress' },
            { label: 'Escalated', value: 'escalated' }, { label: 'Resolved', value: 'resolved' },
            { label: 'Closed', value: 'closed' },
          ]} value={statusFilter} onChange={(v) => { setStatusFilter(v || undefined); setPage(1); }} allowClear style={{ width: 150 }} />
          <Select placeholder="Priority" options={[
            { label: 'Critical', value: 'critical' }, { label: 'High', value: 'high' },
            { label: 'Medium', value: 'medium' }, { label: 'Low', value: 'low' },
          ]} value={priorityFilter} onChange={(v) => { setPriorityFilter(v || undefined); setPage(1); }} allowClear style={{ width: 150 }} />
          <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>Create</Button>
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
