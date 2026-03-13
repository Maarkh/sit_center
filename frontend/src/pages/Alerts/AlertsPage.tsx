import { useEffect, useState } from 'react';
import { Table, Select, Space, Card, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { listAlerts } from '@/api/alerts';
import { useAlertStore } from '@/stores/alertStore';
import StatusTag from '@/components/Common/StatusTag';
import { formatDate } from '@/utils/formatters';
import type { AlertRead } from '@/types/alerts';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const { liveAlerts } = useAlertStore();

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await listAlerts({ status: statusFilter, limit: 100 });
      setAlerts(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [statusFilter]);

  const allAlerts = [...liveAlerts.filter((la) => !alerts.find((a) => a.id === la.id)), ...alerts];

  const columns = [
    { title: 'Status', dataIndex: 'status', key: 'status', width: 130, render: (s: string) => <StatusTag status={s} /> },
    { title: 'Metric', dataIndex: 'metric_name', key: 'metric_name' },
    {
      title: 'Dimensions', dataIndex: 'dimensions', key: 'dimensions',
      render: (d: Record<string, string>) => Object.entries(d || {}).map(([k, v]) => `${k}=${v}`).join(', '),
    },
    { title: 'Value', dataIndex: 'value', key: 'value', render: (v: number) => v?.toFixed(2) },
    { title: 'Detected', dataIndex: 'detected_at', key: 'detected_at', render: formatDate },
    { title: 'Fingerprint', dataIndex: 'fingerprint', key: 'fingerprint', ellipsis: true },
  ];

  return (
    <>
      <Card>
        <Space>
          <Select
            placeholder="Filter by status"
            options={[
              { label: 'All', value: '' },
              { label: 'Firing', value: 'firing' },
              { label: 'Acknowledged', value: 'acknowledged' },
              { label: 'Resolved', value: 'resolved' },
            ]}
            value={statusFilter}
            onChange={(v) => setStatusFilter(v || undefined)}
            allowClear
            style={{ width: 200 }}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
        </Space>
      </Card>
      <Table
        dataSource={allAlerts}
        columns={columns}
        rowKey="id"
        loading={loading}
        style={{ marginTop: 16 }}
        pagination={{ pageSize: 20, showSizeChanger: true }}
      />
    </>
  );
}
