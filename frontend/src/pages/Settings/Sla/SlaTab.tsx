import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, InputNumber, message, Popconfirm, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { listSlaPolicies, createSlaPolicy, updateSlaPolicy, deleteSlaPolicy } from '@/api/incidents';
import { formatDuration } from '@/utils/formatters';
import type { SlaPolicyRead } from '@/types/sla';

export default function SlaTab() {
  const [policies, setPolicies] = useState<SlaPolicyRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setPolicies(await listSlaPolicies()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (p: SlaPolicyRead) => {
    setEditingId(p.id);
    form.setFieldsValue({
      name: p.name,
      priority: p.priority,
      response_time_minutes: p.response_time_minutes,
      resolution_time_minutes: p.resolution_time_minutes,
      escalation_after_minutes: p.escalation_after_minutes,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingId) await updateSlaPolicy(editingId, values);
      else await createSlaPolicy(values);
      message.success(editingId ? 'SLA policy updated' : 'SLA policy created');
      setModalOpen(false);
      fetchData();
    } catch { /* validation */ }
  };

  const handleDelete = async (id: string) => {
    await deleteSlaPolicy(id);
    message.success('SLA policy deleted');
    fetchData();
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Priority', dataIndex: 'priority', key: 'priority' },
    { title: 'Response Time', dataIndex: 'response_time_minutes', key: 'response', render: formatDuration },
    { title: 'Resolution Time', dataIndex: 'resolution_time_minutes', key: 'resolution', render: formatDuration },
    { title: 'Escalation After', dataIndex: 'escalation_after_minutes', key: 'escalation', render: formatDuration },
    {
      title: 'Actions', key: 'actions', width: 110,
      render: (_: unknown, p: SlaPolicyRead) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(p)} />
          <Popconfirm title="Delete this SLA policy?" onConfirm={() => handleDelete(p.id)}>
            <Button danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        Create SLA Policy
      </Button>
      <Table dataSource={policies} columns={columns} rowKey="id" loading={loading} />
      <Modal title={editingId ? 'Edit SLA Policy' : 'Create SLA Policy'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} forceRender>
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
