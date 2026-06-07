import { useCallback, useEffect, useState } from 'react';
import { Table, Select, Input, Space, Card } from 'antd';
import { listAuditLogs } from '@/api/audit';
import { formatDate } from '@/utils/formatters';
import { useTranslation } from 'react-i18next';
import type { AuditLogEntry } from '@/types/audit';

export default function AuditTab() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [action, setAction] = useState<string | undefined>();
  const [resourceType, setResourceType] = useState<string | undefined>();
  const [username, setUsername] = useState<string | undefined>();
  const { t } = useTranslation();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try { setLogs(await listAuditLogs({ action, resource_type: resourceType, username, limit: 100 })); } finally { setLoading(false); }
  }, [action, resourceType, username]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const columns = [
    { title: t('audit.time'), dataIndex: 'timestamp', key: 'timestamp', render: formatDate, width: 180 },
    { title: t('audit.user'), dataIndex: 'username', key: 'username' },
    { title: t('audit.action'), dataIndex: 'action', key: 'action' },
    { title: t('audit.resource'), dataIndex: 'resource_type', key: 'resource_type' },
    { title: t('audit.resource_id'), dataIndex: 'resource_id', key: 'resource_id', ellipsis: true },
    { title: t('audit.ip'), dataIndex: 'ip_address', key: 'ip_address' },
  ];

  return (
    <>
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select placeholder={t('audit.action_filter')} options={['create', 'update', 'delete', 'login'].map((a) => ({ label: a, value: a }))} value={action} onChange={setAction} allowClear style={{ width: 150 }} />
          <Select placeholder={t('audit.resource_filter')} options={['metric', 'rule', 'incident', 'ml_config', 'tenant', 'user', 'role', 'sla_policy', 'session'].map((r) => ({ label: r, value: r }))} value={resourceType} onChange={setResourceType} allowClear style={{ width: 150 }} />
          <Input placeholder={t('audit.username_filter')} value={username} onChange={(e) => setUsername(e.target.value || undefined)} allowClear style={{ width: 150 }} />
        </Space>
      </Card>
      <Table dataSource={logs} columns={columns} rowKey="id" loading={loading} pagination={{ pageSize: 20 }} />
    </>
  );
}
