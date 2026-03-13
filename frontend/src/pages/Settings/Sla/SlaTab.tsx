import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { listSlaPolicies, createSlaPolicy } from '@/api/incidents';
import { formatDuration } from '@/utils/formatters';
import type { SlaPolicyRead } from '@/types/sla';

export default function SlaTab() {
  const [policies, setPolicies] = useState<SlaPolicyRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setPolicies(await listSlaPolicies()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createSlaPolicy(values);
      message.success('SLA policy created');
      form.resetFields();
      setModalOpen(false);
      fetchData();
    } catch { /* validation */ }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Priority', dataIndex: 'priority', key: 'priority' },
    { title: 'Response Time', dataIndex: 'response_time_minutes', key: 'response', render: formatDuration },
    { title: 'Resolution Time', dataIndex: 'resolution_time_minutes', key: 'resolution', render: formatDuration },
    { title: 'Escalation After', dataIndex: 'escalation_after_minutes', key: 'escalation', render: formatDuration },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ marginBottom: 16 }}>
        Create SLA Policy
      </Button>
      <Table dataSource={policies} columns={columns} rowKey="id" loading={loading} />
      <Modal title="Create SLA Policy" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} destroyOnClose>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
            <Select options={[
              { label: 'Critical', value: 'critical' }, { label: 'High', value: 'high' },
              { label: 'Medium', value: 'medium' }, { label: 'Low', value: 'low' },
            ]} />
          </Form.Item>
          <Form.Item name="response_time_minutes" label="Response Time (min)" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="resolution_time_minutes" label="Resolution Time (min)" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="escalation_after_minutes" label="Escalation After (min)" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
