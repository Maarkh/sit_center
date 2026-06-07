import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Switch, Space, Popconfirm, Tag, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { listMetrics, createMetric, updateMetric, deleteMetric } from '@/api/metrics';
import type { MetricRead, MetricCreate } from '@/types/metrics';

export default function MetricsTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [metrics, setMetrics] = useState<MetricRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<MetricRead | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setMetrics(await listMetrics(false)); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true, unit: '' });
    setModalOpen(true);
  };

  const openEdit = (m: MetricRead) => {
    setEditing(m);
    form.setFieldsValue({ ...m });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const payload: MetricCreate = {
      metric_name: values.metric_name,
      display_name: values.display_name,
      description: values.description ?? null,
      unit: values.unit ?? '',
      default_threshold: values.default_threshold ?? null,
      default_critical_threshold: values.default_critical_threshold ?? null,
      is_active: values.is_active ?? true,
    };
    try {
      if (editing) await updateMetric(editing.metric_name, payload);
      else await createMetric(payload);
      message.success(t('settingsDss.saved'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('settingsDss.saveFailed'));
    }
  };

  const handleDelete = async (name: string) => {
    await deleteMetric(name);
    message.success(t('settingsDss.deleted'));
    fetchData();
  };

  const columns = [
    { title: t('metricCat.metricName', 'Метрика'), dataIndex: 'metric_name', key: 'metric_name',
      render: (v: string) => <code>{v}</code> },
    { title: t('metricCat.displayName', 'Название'), dataIndex: 'display_name', key: 'display_name' },
    { title: t('metricCat.unit', 'Ед.'), dataIndex: 'unit', key: 'unit', width: 80 },
    { title: t('metricCat.threshold', 'Порог'), dataIndex: 'default_threshold', key: 'default_threshold', width: 90,
      render: (v: number | null) => (v ?? '—') },
    { title: t('metricCat.critical', 'Крит.'), dataIndex: 'default_critical_threshold', key: 'crit', width: 90,
      render: (v: number | null) => (v ?? '—') },
    { title: t('settingsDss.active'), dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '✓' : '—'}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 110,
      render: (_: unknown, m: MetricRead) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(m)} />
          <Popconfirm title={t('settingsDss.deleteConfirm')} onConfirm={() => handleDelete(m.metric_name)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        {t('metricCat.newMetric', 'Новая метрика')}
      </Button>
      <Table dataSource={metrics} columns={columns} rowKey="metric_name" loading={loading} size="small" />

      <Modal title={editing ? t('metricCat.editMetric', 'Редактировать метрику') : t('metricCat.newMetric', 'Новая метрика')}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={560} forceRender>
        <Form form={form} layout="vertical">
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="metric_name" label={t('metricCat.metricName', 'Метрика (ключ)')} style={{ minWidth: 240 }}
              rules={[{ required: true }, { pattern: /^[a-zA-Z0-9_\-.]+$/, message: 'a-z 0-9 _ - .' }]}>
              <Input placeholder="cpu_usage" disabled={!!editing} />
            </Form.Item>
            <Form.Item name="unit" label={t('metricCat.unit', 'Ед.')}><Input style={{ width: 90 }} placeholder="%" /></Form.Item>
            <Form.Item name="is_active" label={t('settingsDss.active')} valuePropName="checked"><Switch /></Form.Item>
          </Space>
          <Form.Item name="display_name" label={t('metricCat.displayName', 'Название')} rules={[{ required: true }]}>
            <Input placeholder={t('metricCat.displayName', 'Название')} />
          </Form.Item>
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="default_threshold" label={t('metricCat.threshold', 'Порог')}>
              <InputNumber style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="default_critical_threshold" label={t('metricCat.critical', 'Крит. порог')}>
              <InputNumber style={{ width: 160 }} />
            </Form.Item>
          </Space>
          <Form.Item name="description" label={t('metricCat.description', 'Описание')}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
