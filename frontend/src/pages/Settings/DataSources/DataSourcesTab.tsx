import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Select, Switch, Space, Popconfirm, Tag, Typography, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, SendOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { listSources, createSource, updateSource, deleteSource, testSource } from '@/api/sources';
import type { DataSource, SourceCreate, SourceType } from '@/types/sources';

const SOURCE_TYPES: SourceType[] = ['host_agent', 'http_pull', 'kafka', 'http_push'];
const HOST_METRICS = ['cpu_usage', 'mem_usage', 'disk_usage', 'swap_usage', 'load1'];
const TYPE_COLOR: Record<string, string> = { host_agent: 'blue', http_pull: 'purple', kafka: 'gold', http_push: 'magenta' };
const INGEST_PATH = '/api/v1/ingest/metrics';

export default function DataSourcesTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const type = Form.useWatch('type', form) as SourceType | undefined;

  const fetchData = async () => {
    setLoading(true);
    try { setSources(await listSources()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      type: 'host_agent', enabled: true,
      config: { metrics: ['cpu_usage', 'mem_usage'], sample_seconds: 5 },
    });
    setModalOpen(true);
  };

  const openEdit = (s: DataSource) => {
    setEditingId(s.id);
    const cfg: Record<string, unknown> = { ...s.config };
    if (s.type === 'http_pull' && cfg.headers && typeof cfg.headers === 'object') {
      cfg.headers = JSON.stringify(cfg.headers);
    }
    form.setFieldsValue({ name: s.name, type: s.type, enabled: s.enabled, config: cfg });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const config: Record<string, unknown> = { ...(values.config || {}) };

    if (values.type === 'http_pull') {
      if (typeof config.headers === 'string') {
        const raw = (config.headers as string).trim();
        try { config.headers = raw ? JSON.parse(raw) : {}; }
        catch { message.error(t('dataSrc.headersInvalid', 'Headers — не валидный JSON')); return; }
      }
      config.metric_map = ((config.metric_map as { json_path?: string; metric_name?: string }[]) || [])
        .filter((m) => m && m.json_path && m.metric_name);
    }

    const payload: SourceCreate = {
      name: values.name, type: values.type, config, enabled: values.enabled ?? true,
    };
    try {
      if (editingId) {
        await updateSource(editingId, payload);
      } else {
        const created = await createSource(payload);
        const key = (created.config as Record<string, unknown>)?.api_key as string | undefined;
        if (created.type === 'http_push' && key && key !== '***') {
          Modal.success({
            title: t('dataSrc.keyOnce', 'API-ключ создан — скопируйте сейчас (больше не показывается)'),
            width: 540,
            content: (
              <div>
                <Typography.Paragraph copyable={{ text: key }} code style={{ wordBreak: 'break-all' }}>{key}</Typography.Paragraph>
                <div style={{ color: '#888' }}>
                  {t('dataSrc.pushHint', 'Агенты шлют POST на {{path}} с заголовком X-API-KEY.', { path: INGEST_PATH })}
                </div>
              </div>
            ),
          });
        }
      }
      message.success(t('dataSrc.saved', 'Источник сохранён'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('dataSrc.saveFailed', 'Не удалось сохранить (дубль имени?)'));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteSource(id);
    message.success(t('dataSrc.deleted', 'Источник удалён'));
    fetchData();
  };

  const handleTest = async (id: string) => {
    const res = await testSource(id);
    if (res.ok) {
      const sample = res.sample ? ` — ${JSON.stringify(res.sample)}` : '';
      message.success(`${t('dataSrc.testOk', 'Проба успешна')}${sample}`);
    } else {
      message.error(`${t('dataSrc.testFail', 'Ошибка пробы')}: ${res.error ?? ''}`);
    }
  };

  const columns = [
    { title: t('dataSrc.name', 'Название'), dataIndex: 'name', key: 'name' },
    { title: t('dataSrc.type', 'Тип'), dataIndex: 'type', key: 'type',
      render: (v: string) => <Tag color={TYPE_COLOR[v] ?? 'default'}>{v}</Tag> },
    { title: t('dataSrc.summary', 'Конфиг'), key: 'summary',
      render: (_: unknown, s: DataSource) => {
        if (s.type === 'host_agent') return ((s.config.metrics as string[]) || []).join(', ');
        if (s.type === 'http_pull') return String(s.config.url ?? '');
        if (s.type === 'kafka') return String(s.config.topic ?? '');
        if (s.type === 'http_push') return INGEST_PATH;
        return '';
      } },
    { title: t('dataSrc.enabled', 'Вкл'), dataIndex: 'enabled', key: 'enabled', width: 70,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '✓' : '—'}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 140,
      render: (_: unknown, s: DataSource) => (
        <Space>
          <Button size="small" icon={<SendOutlined />} onClick={() => handleTest(s.id)} title={t('dataSrc.test', 'Тест')} />
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(s)} />
          <Popconfirm title={t('dataSrc.deleteConfirm', 'Удалить источник?')} onConfirm={() => handleDelete(s.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <div style={{ marginBottom: 12, color: 'var(--ant-color-text-secondary, #888)' }}>
        {t('dataSrc.hint', 'Откуда система берёт метрики. Коллектор и kafka-consumer читают включённые источники из этого реестра.')}
      </div>
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        {t('dataSrc.newSource', 'Новый источник')}
      </Button>
      <Table dataSource={sources} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal title={editingId ? t('dataSrc.editSource', 'Редактировать источник') : t('dataSrc.newSource', 'Новый источник')}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={620} forceRender>
        <Form form={form} layout="vertical">
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="name" label={t('dataSrc.name', 'Название')} rules={[{ required: true }]} style={{ minWidth: 260 }}>
              <Input />
            </Form.Item>
            <Form.Item name="type" label={t('dataSrc.type', 'Тип')} rules={[{ required: true }]} style={{ minWidth: 160 }}>
              <Select options={SOURCE_TYPES.map((v) => ({ label: v, value: v }))} />
            </Form.Item>
            <Form.Item name="enabled" label={t('dataSrc.enabled', 'Вкл')} valuePropName="checked"><Switch /></Form.Item>
          </Space>

          {type === 'host_agent' && (
            <Space style={{ display: 'flex' }} align="start">
              <Form.Item name={['config', 'metrics']} label={t('dataSrc.metrics', 'Метрики')} style={{ minWidth: 360 }}>
                <Select mode="multiple" options={HOST_METRICS.map((m) => ({ label: m, value: m }))} />
              </Form.Item>
              <Form.Item name={['config', 'sample_seconds']} label={t('dataSrc.sampleSeconds', 'Интервал, с')}>
                <InputNumber min={1} style={{ width: 120 }} />
              </Form.Item>
            </Space>
          )}

          {type === 'http_pull' && (
            <>
              <Form.Item name={['config', 'url']} label="URL" rules={[{ required: true }]}>
                <Input placeholder="https://host/metrics.json" />
              </Form.Item>
              <Space style={{ display: 'flex' }} align="start">
                <Form.Item name={['config', 'method']} label={t('dataSrc.method', 'Метод')} initialValue="GET">
                  <Select style={{ width: 100 }} options={['GET', 'POST'].map((m) => ({ label: m, value: m }))} />
                </Form.Item>
                <Form.Item name={['config', 'interval_seconds']} label={t('dataSrc.intervalSeconds', 'Интервал, с')} initialValue={30}>
                  <InputNumber min={1} style={{ width: 120 }} />
                </Form.Item>
                <Form.Item name={['config', 'token']} label={t('dataSrc.token', 'Токен (Bearer)')}
                  tooltip={editingId ? t('dataSrc.secretHint', 'Оставьте «***», чтобы не менять') : undefined} style={{ minWidth: 220 }}>
                  <Input placeholder="optional" />
                </Form.Item>
              </Space>
              <Form.Item name={['config', 'headers']} label={t('dataSrc.headers', 'Доп. заголовки (JSON)')}>
                <Input.TextArea rows={2} placeholder='{"X-Api-Key": "..."}' />
              </Form.Item>
              <div style={{ fontWeight: 500, margin: '4px 0 8px' }}>{t('dataSrc.metricMap', 'Соответствие метрик')}</div>
              <Form.List name={['config', 'metric_map']}>
                {(fields, { add, remove }) => (
                  <>
                    {fields.map((field) => (
                      <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 4 }}>
                        <Form.Item name={[field.name, 'json_path']} rules={[{ required: true, message: '' }]}>
                          <Input placeholder={t('dataSrc.jsonPath', 'json-путь, напр. data.cpu')} style={{ width: 240 }} />
                        </Form.Item>
                        <Form.Item name={[field.name, 'metric_name']} rules={[{ required: true, message: '' }]}>
                          <Input placeholder={t('dataSrc.metricName', 'имя метрики')} style={{ width: 200 }} />
                        </Form.Item>
                        <MinusCircleOutlined onClick={() => remove(field.name)} />
                      </Space>
                    ))}
                    <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({})} block>
                      {t('dataSrc.addMapping', 'Добавить соответствие')}
                    </Button>
                  </>
                )}
              </Form.List>
            </>
          )}

          {type === 'kafka' && (
            <>
              <Form.Item name={['config', 'topic']} label={t('dataSrc.topic', 'Topic')} rules={[{ required: true }]}>
                <Input placeholder="sit_center.metrics" />
              </Form.Item>
              <Form.Item name={['config', 'bootstrap_servers']} label={t('dataSrc.bootstrap', 'Bootstrap servers')}>
                <Input placeholder="kafka:9092" />
              </Form.Item>
              <Form.Item name={['config', 'sasl_password']} label={t('dataSrc.saslPassword', 'SASL пароль')}
                tooltip={editingId ? t('dataSrc.secretHint', 'Оставьте «***», чтобы не менять') : undefined}>
                <Input placeholder="optional" />
              </Form.Item>
            </>
          )}

          {type === 'http_push' && (
            <>
              <Form.Item name={['config', 'api_key']} label={t('dataSrc.apiKey', 'API-ключ')}
                tooltip={editingId
                  ? t('dataSrc.secretHint', 'Оставьте «***», чтобы не менять')
                  : t('dataSrc.keyAutogen', 'Оставьте пустым — ключ сгенерируется и покажется один раз')}>
                <Input placeholder={editingId ? '***' : t('dataSrc.keyAutogen', 'авто')} />
              </Form.Item>
              <div style={{ color: 'var(--ant-color-text-secondary, #888)' }}>
                {t('dataSrc.pushHint', 'Агенты шлют POST на {{path}} с заголовком X-API-KEY.', { path: INGEST_PATH })}
              </div>
            </>
          )}
        </Form>
      </Modal>
    </>
  );
}
