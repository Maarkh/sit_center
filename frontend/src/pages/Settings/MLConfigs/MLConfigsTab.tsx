import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, Switch, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { listMLConfigs, createMLConfig, deleteMLConfig } from '@/api/mlConfigs';
import { ML_METHODS } from '@/utils/constants';
import type { MLConfigRead } from '@/types/mlConfigs';

export default function MLConfigsTab() {
  const [configs, setConfigs] = useState<MLConfigRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setConfigs(await listMLConfigs()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createMLConfig(values);
      message.success('ML config created');
      form.resetFields();
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
      title: 'Actions', key: 'actions', width: 100,
      render: (_: unknown, r: MLConfigRead) => (
        <Popconfirm title="Delete?" onConfirm={() => handleDelete(r.id)}>
          <Button danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ marginBottom: 16 }}>
        Create ML Config
      </Button>
      <Table dataSource={configs} columns={columns} rowKey="id" loading={loading} />
      <Modal title="Create ML Config" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} destroyOnClose>
        <Form form={form} layout="vertical" initialValues={{ methods: ['prophet'], auto_alert: true, alert_severity: 'warning', is_active: true }}>
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
