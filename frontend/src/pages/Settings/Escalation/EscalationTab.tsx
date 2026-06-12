import { useEffect, useState } from 'react';
import PageHelp from '@/components/Common/PageHelp';
import {
  Table, Button, Modal, Form, Input, InputNumber, Space, Popconfirm, Tag, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { listChains, createChain, updateChain, deleteChain } from '@/api/escalation';
import type { EscalationChain, EscalationChainCreate } from '@/types/escalation';

const csvToList = (s?: string): string[] =>
  (s ?? '').split(',').map((x) => x.trim()).filter(Boolean);

export default function EscalationTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [chains, setChains] = useState<EscalationChain[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setChains(await listChains()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ levels: [{ level: 1, escalate_after_minutes: 30 }] });
    setModalOpen(true);
  };

  const openEdit = (c: EscalationChain) => {
    setEditingId(c.id);
    form.setFieldsValue({
      name: c.name,
      levels: c.levels.map((l) => ({
        level: l.level,
        notify_role: l.notify_role,
        notify_users: (l.notify_users ?? []).join(', '),
        escalate_after_minutes: l.escalate_after_minutes,
      })),
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const payload: EscalationChainCreate = {
      name: values.name,
      levels: (values.levels ?? [])
        .filter((l: { notify_role?: string }) => l && l.notify_role)
        .map((l: { level?: number; notify_role: string; notify_users?: string; escalate_after_minutes?: number }, i: number) => ({
          level: l.level ?? i + 1,
          notify_role: l.notify_role,
          notify_users: csvToList(l.notify_users),
          escalate_after_minutes: l.escalate_after_minutes ?? 30,
        })),
    };
    try {
      if (editingId) await updateChain(editingId, payload);
      else await createChain(payload);
      message.success(t('settingsEsc.saved', 'Сохранено'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('settingsEsc.saveFailed', 'Не удалось сохранить (дубль уровня?)'));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteChain(id);
    message.success(t('settingsEsc.deleted', 'Цепочка удалена'));
    fetchData();
  };

  const columns = [
    { title: t('settingsEsc.name', 'Название'), dataIndex: 'name', key: 'name' },
    {
      title: t('settingsEsc.levels', 'Уровни'), key: 'levels',
      render: (_: unknown, c: EscalationChain) => (
        <Space wrap>
          {c.levels.map((l) => (
            <Tag key={l.level} color="blue">
              L{l.level} → {l.notify_role}{l.notify_users?.length ? ` (${l.notify_users.join(', ')})` : ''} · {l.escalate_after_minutes}{t('settingsEsc.min', 'м')}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: t('common.actions'), key: 'actions', width: 110,
      render: (_: unknown, c: EscalationChain) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(c)} />
          <Popconfirm title={t('settingsEsc.deleteConfirm', 'Удалить цепочку?')} onConfirm={() => handleDelete(c.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <PageHelp section="escalation" />
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        {t('settingsEsc.newChain', 'Новая цепочка')}
      </Button>
      <Table dataSource={chains} columns={columns} rowKey="id" loading={loading} />

      <Modal title={editingId ? t('settingsEsc.editChain', 'Редактировать цепочку') : t('settingsEsc.newChain', 'Новая цепочка')}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={620} forceRender>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('settingsEsc.name', 'Название')} rules={[{ required: true }]}><Input /></Form.Item>
          <div style={{ fontWeight: 500, margin: '4px 0 8px' }}>{t('settingsEsc.levels', 'Уровни')}</div>
          <Form.List name="levels">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 4 }}>
                    <Form.Item name={[field.name, 'level']} rules={[{ required: true, message: '' }]}>
                      <InputNumber min={1} max={99} placeholder="L#" style={{ width: 64 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'notify_role']} rules={[{ required: true, message: '' }]}>
                      <Input placeholder={t('settingsEsc.role', 'роль')} style={{ width: 130 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'notify_users']}>
                      <Input placeholder={t('settingsEsc.usersCsv', 'пользователи через запятую')} style={{ width: 200 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'escalate_after_minutes']} rules={[{ required: true, message: '' }]}>
                      <InputNumber min={1} placeholder={t('settingsEsc.min', 'м')} style={{ width: 80 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ level: fields.length + 1, escalate_after_minutes: 30 })} block>
                  {t('settingsEsc.addLevel', 'Добавить уровень')}
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>
    </>
  );
}
