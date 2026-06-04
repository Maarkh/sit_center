import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, message, Popconfirm, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { listRules, createRule, updateRule, deleteRule } from '@/api/rules';
import StatusTag from '@/components/Common/StatusTag';
import type { RuleRead } from '@/types/rules';

export default function RulesTab() {
  const [rules, setRules] = useState<RuleRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setRules(await listRules()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setModalOpen(true);
  };

  const openEdit = (r: RuleRead) => {
    setEditingId(r.id);
    form.setFieldsValue({
      name: r.name,
      description: r.description,
      expr: r.condition?.expr,
      for_duration: r.condition?.for_duration,
      is_active: r.is_active,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        name: values.name,
        description: values.description,
        condition: { expr: values.expr, for_duration: values.for_duration },
        is_active: values.is_active ?? true,
      };
      if (editingId) await updateRule(editingId, payload);
      else await createRule(payload);
      message.success(editingId ? 'Rule updated' : 'Rule created');
      setModalOpen(false);
      fetchData();
    } catch { /* validation */ }
  };

  const handleDelete = async (id: string) => {
    await deleteRule(id);
    message.success('Rule deleted');
    fetchData();
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Expression', dataIndex: ['condition', 'expr'], key: 'expr', ellipsis: true },
    { title: 'Active', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <StatusTag status={v ? 'resolved' : 'closed'} /> },
    {
      title: 'Actions', key: 'actions', width: 110,
      render: (_: unknown, r: RuleRead) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          <Popconfirm title="Delete this rule?" onConfirm={() => handleDelete(r.id)}>
            <Button danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        Create Rule
      </Button>
      <Table dataSource={rules} columns={columns} rowKey="id" loading={loading} />
      <Modal title={editingId ? 'Edit Rule' : 'Create Rule'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} forceRender>
        <Form form={form} layout="vertical" initialValues={{ is_active: true }}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="expr" label="Expression (PromQL)" rules={[{ required: true }]}><Input placeholder="cpu{region='msk'} > 80" /></Form.Item>
          <Form.Item name="for_duration" label="For Duration"><Input placeholder="5m" /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
          <Form.Item name="is_active" label="Active" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
