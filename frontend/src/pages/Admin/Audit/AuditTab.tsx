import { useEffect, useState } from 'react';
import { Table, Select, Input, Space, Card } from 'antd';
import { listAuditLogs } from '@/api/audit';
import { formatDate } from '@/utils/formatters';
import type { AuditLogEntry } from '@/types/audit';

export default function AuditTab() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<string | undefined>();
  const [resourceType, setResourceType] = useState<string | undefined>();
  const [username, setUsername] = useState<string | undefined>();

  const fetchData = async () => {
    setLoading(true);
    try { setLogs(await listAuditLogs({ action, resource_type: resourceType, username, limit: 100 })); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, [action, resourceType, username]);

  const columns = [
    { title: 'Time', dataIndex: 'timestamp', key: 'timestamp', render: formatDate, width: 180 },
    { title: 'User', dataIndex: 'username', key: 'username' },
    { title: 'Action', dataIndex: 'action', key: 'action' },
    { title: 'Resource', dataIndex: 'resource_type', key: 'resource_type' },
    { title: 'Resource ID', dataIndex: 'resource_id', key: 'resource_id', ellipsis: true },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip_address' },
  ];

  return (
    <>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select placeholder="Action" options={['create', 'update', 'delete', 'login'].map((a) => ({ label: a, value: a }))} value={action} onChange={setAction} allowClear style={{ width: 150 }} />
          <Select placeholder="Resource" options={['metric', 'rule', 'incident', 'ml_config', 'tenant', 'user', 'role', 'sla_policy', 'session'].map((r) => ({ label: r, value: r }))} value={resourceType} onChange={setResourceType} allowClear style={{ width: 150 }} />
          <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value || undefined)} allowClear style={{ width: 150 }} />
        </Space>
      </Card>
      <Table dataSource={logs} columns={columns} rowKey="id" loading={loading} pagination={{ pageSize: 20 }} />
    </>
  );
}
