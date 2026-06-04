import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Switch, message, Popconfirm, Tag, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { listMLConfigs, createMLConfig, updateMLConfig, deleteMLConfig } from '@/api/mlConfigs';
import { ML_METHODS } from '@/utils/constants';
import type { MLConfigRead } from '@/types/mlConfigs';

export default function MLConfigsTab() {
  const [configs, setConfigs] = useState<MLConfigRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setConfigs(await listMLConfigs()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ methods: ['prophet'], auto_alert: true, alert_severity: 'warning' });
    setModalOpen(true);
  };

  const openEdit = (r: MLConfigRead) => {
    setEditingId(r.id);
    form.setFieldsValue({
      name: r.name,
      metric_name: r.metric_name,
      methods: r.methods,
      retrain_schedule: r.retrain_schedule,
      alert_severity: r.alert_severity,
      auto_alert: r.auto_alert,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingId) await updateMLConfig(editingId, values);
      else await createMLConfig(values);
      message.success(editingId ? 'ML config updated' : 'ML config created');
      setModalOpen(false);
      fetchData();
    } catch { /* validation */ }
  };

  const handleDelete = async (id: string) => {
    await deleteMLConfig(id);
    message.success('Config deleted');
    fetchData();
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Metric', dataIndex: 'metric_name', key: 'metric_name' },
    { title: 'Methods', dataIndex: 'methods', key: 'methods', render: (m: string[]) => m?.map((v) => <Tag key={v}>{v}</Tag>) },
    { title: 'Schedule', dataIndex: 'retrain_schedule', key: 'retrain_schedule' },
    { title: 'Auto Alert', dataIndex: 'auto_alert', key: 'auto_alert', render: (v: boolean) => v ? 'Yes' : 'No' },
    {
      title: 'Actions', key: 'actions', width: 110,
      render: (_: unknown, r: MLConfigRead) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          <Popconfirm title="Delete?" onConfirm={() => handleDelete(r.id)}>
            <Button danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        Create ML Config
      </Button>
      <Table dataSource={configs} columns={columns} rowKey="id" loading={loading} />
      <Modal title={editingId ? 'Edit ML Config' : 'Create ML Config'} open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} forceRender>
        <Form form={form} layout="vertical" initialValues={{ methods: ['prophet'], auto_alert: true, alert_severity: 'warning' }}>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="metric_name" label="Metric Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="methods" label="Methods" rules={[{ required: true }]}>
            <Select mode="multiple" options={ML_METHODS.map((m) => ({ label: m, value: m }))} />
          </Form.Item>
          <Form.Item name="retrain_schedule" label="Retrain Schedule"><Input placeholder="0 3 * * *" /></Form.Item>
          <Form.Item name="alert_severity" label="Alert Severity">
            <Select options={[{ label: 'Warning', value: 'warning' }, { label: 'Critical', value: 'critical' }]} />
          </Form.Item>
          <Form.Item name="auto_alert" label="Auto Alert" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
