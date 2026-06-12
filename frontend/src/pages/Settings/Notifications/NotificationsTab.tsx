import { useEffect, useState } from 'react';
import PageHelp from '@/components/Common/PageHelp';
import {
  Table, Button, Modal, Form, Input, Select, Switch, Space, Popconfirm, Tag, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, SendOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import {
  listChannels, createChannel, updateChannel, deleteChannel, testChannel,
} from '@/api/notifications';
import type { NotificationChannel, ChannelCreate, ChannelType } from '@/types/notifications';

const CHANNEL_TYPES: ChannelType[] = ['telegram', 'email', 'webhook', 'whatsapp_twilio'];
const EVENT_TYPES = ['all', 'alert', 'incident', 'escalation', 'predictive', 'situation', 'system'];
const PRIORITIES = ['info', 'warning', 'critical'];

// transport-specific config fields rendered when that type is selected
const TYPE_FIELDS: Record<ChannelType, { key: string; label: string; secret?: boolean; placeholder?: string }[]> = {
  telegram: [
    { key: 'bot_token', label: 'Bot token', secret: true },
    { key: 'chat_id', label: 'Chat ID' },
  ],
  email: [
    { key: 'host', label: 'SMTP host' },
    { key: 'port', label: 'Port', placeholder: '587' },
    { key: 'username', label: 'Username' },
    { key: 'password', label: 'Password', secret: true },
    { key: 'from', label: 'From' },
    { key: 'to', label: 'To (comma-separated)' },
  ],
  webhook: [
    { key: 'url', label: 'URL' },
    { key: 'headers', label: 'Headers (JSON)', placeholder: '{"Authorization": "Bearer ..."}' },
  ],
  whatsapp_twilio: [
    { key: 'account_sid', label: 'Account SID' },
    { key: 'auth_token', label: 'Auth token', secret: true },
    { key: 'from', label: 'From (number)' },
    { key: 'to', label: 'To (number)' },
  ],
};

const TYPE_COLOR: Record<string, string> = { telegram: 'blue', email: 'green', webhook: 'purple', whatsapp_twilio: 'cyan' };
const PRIO_COLOR: Record<string, string> = { info: 'default', warning: 'orange', critical: 'red' };

export default function NotificationsTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [channels, setChannels] = useState<NotificationChannel[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const type = Form.useWatch('type', form) as ChannelType | undefined;

  const fetchData = async () => {
    setLoading(true);
    try { setChannels(await listChannels()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ type: 'telegram', min_priority: 'info', enabled: true, event_types: ['alert', 'escalation'] });
    setModalOpen(true);
  };

  const openEdit = (c: NotificationChannel) => {
    setEditingId(c.id);
    const cfg: Record<string, unknown> = { ...c.config };
    if (c.type === 'webhook' && cfg.headers && typeof cfg.headers === 'object') {
      cfg.headers = JSON.stringify(cfg.headers);
    }
    form.setFieldsValue({
      name: c.name, type: c.type, config: cfg,
      event_types: c.event_types, min_priority: c.min_priority, enabled: c.enabled,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const config: Record<string, unknown> = { ...(values.config || {}) };
    if (values.type === 'webhook' && typeof config.headers === 'string') {
      const raw = (config.headers as string).trim();
      try { config.headers = raw ? JSON.parse(raw) : {}; }
      catch { message.error(t('notif.headersInvalid', 'Headers — не валидный JSON')); return; }
    }
    const payload: ChannelCreate = {
      name: values.name, type: values.type, config,
      event_types: values.event_types ?? [], min_priority: values.min_priority, enabled: values.enabled ?? true,
    };
    try {
      if (editingId) await updateChannel(editingId, payload);
      else await createChannel(payload);
      message.success(t('notif.saved', 'Канал сохранён'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('notif.saveFailed', 'Не удалось сохранить'));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteChannel(id);
    message.success(t('notif.deleted', 'Канал удалён'));
    fetchData();
  };

  const handleTest = async (id: string) => {
    const res = await testChannel(id);
    if (res.ok) message.success(t('notif.testOk', 'Тестовое уведомление отправлено'));
    else message.error(`${t('notif.testFail', 'Ошибка отправки')}: ${res.error ?? ''}`);
  };

  const columns = [
    { title: t('notif.name', 'Название'), dataIndex: 'name', key: 'name' },
    { title: t('notif.type', 'Тип'), dataIndex: 'type', key: 'type',
      render: (v: string) => <Tag color={TYPE_COLOR[v] ?? 'default'}>{v}</Tag> },
    { title: t('notif.events', 'События'), dataIndex: 'event_types', key: 'event_types',
      render: (v: string[]) => <Space wrap size={[0, 4]}>{(v ?? []).map((e) => <Tag key={e}>{t(`notif.event.${e}`, e)}</Tag>)}</Space> },
    { title: t('notif.minPriority', 'Мин. приоритет'), dataIndex: 'min_priority', key: 'min_priority',
      render: (v: string) => <Tag color={PRIO_COLOR[v] ?? 'default'}>{v}</Tag> },
    { title: t('notif.enabled', 'Вкл'), dataIndex: 'enabled', key: 'enabled', width: 70,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '✓' : '—'}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 140,
      render: (_: unknown, c: NotificationChannel) => (
        <Space>
          <Button size="small" icon={<SendOutlined />} onClick={() => handleTest(c.id)} title={t('notif.test', 'Тест')} />
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(c)} />
          <Popconfirm title={t('notif.deleteConfirm', 'Удалить канал?')} onConfirm={() => handleDelete(c.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <PageHelp section="notifications" />
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        {t('notif.newChannel', 'Новый канал')}
      </Button>
      <Table dataSource={channels} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal title={editingId ? t('notif.editChannel', 'Редактировать канал') : t('notif.newChannel', 'Новый канал')}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={560} forceRender>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('notif.name', 'Название')} rules={[{ required: true }]}><Input /></Form.Item>
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="type" label={t('notif.type', 'Тип')} rules={[{ required: true }]} style={{ minWidth: 200 }}>
              <Select options={CHANNEL_TYPES.map((v) => ({ label: v, value: v }))} />
            </Form.Item>
            <Form.Item name="min_priority" label={t('notif.minPriority', 'Мин. приоритет')} style={{ minWidth: 140 }}>
              <Select options={PRIORITIES.map((v) => ({ label: v, value: v }))} />
            </Form.Item>
            <Form.Item name="enabled" label={t('notif.enabled', 'Вкл')} valuePropName="checked"><Switch /></Form.Item>
          </Space>

          <Form.Item name="event_types" label={t('notif.events', 'События')}
            tooltip={t('notif.eventsHint', 'На какие события слать. «all» = все.')}>
            <Select mode="multiple" options={EVENT_TYPES.map((e) => ({ label: t(`notif.event.${e}`, e), value: e }))} />
          </Form.Item>

          {type && TYPE_FIELDS[type].map((f) => (
            <Form.Item key={f.key} name={['config', f.key]} label={f.label}
              tooltip={f.secret && editingId ? t('notif.secretHint', 'Оставьте «***», чтобы не менять') : undefined}>
              {f.key === 'headers'
                ? <Input.TextArea rows={2} placeholder={f.placeholder} />
                : <Input placeholder={f.placeholder} />}
            </Form.Item>
          ))}
        </Form>
      </Modal>
    </>
  );
}
