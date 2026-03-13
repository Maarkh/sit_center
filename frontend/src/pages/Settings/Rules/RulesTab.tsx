import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Switch, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { listRules, createRule, deleteRule } from '@/api/rules';
import StatusTag from '@/components/Common/StatusTag';
import type { RuleRead } from '@/types/rules';

export default function RulesTab() {
  const [rules, setRules] = useState<RuleRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setRules(await listRules()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createRule({
        name: values.name,
        description: values.description,
        condition: { expr: values.expr, for_duration: values.for_duration },
        is_active: values.is_active ?? true,
      });
      message.success('Rule created');
      form.resetFields();
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
      title: 'Actions', key: 'actions', width: 100,
      render: (_: unknown, r: RuleRead) => (
        <Popconfirm title="Delete this rule?" onConfirm={() => handleDelete(r.id)}>
          <Button danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ marginBottom: 16 }}>
        Create Rule
      </Button>
      <Table dataSource={rules} columns={columns} rowKey="id" loading={loading} />
      <Modal title="Create Rule" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} destroyOnClose>
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
