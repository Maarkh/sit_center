import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Select, Space, Popconfirm, Tag, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import {
  listPlaybooks, getPlaybook, createPlaybook, updatePlaybook, deletePlaybook,
  listProcessTemplates, listIndicators,
} from '@/api/dss';
import type {
  PlaybookListItem, PlaybookCreate, ProcessTemplateListItem, IndicatorRead,
} from '@/types/dss';

const csvToList = (s?: string): string[] =>
  (s ?? '').split(',').map((x) => x.trim()).filter(Boolean);

const ANY = 'any';

export default function PlaybooksTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [playbooks, setPlaybooks] = useState<PlaybookListItem[]>([]);
  const [templates, setTemplates] = useState<ProcessTemplateListItem[]>([]);
  const [indicators, setIndicators] = useState<IndicatorRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [pbs, tmpls, inds] = await Promise.all([listPlaybooks(), listProcessTemplates(), listIndicators()]);
      setPlaybooks(pbs);
      setTemplates(tmpls);
      setIndicators(inds);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ trigger_severity: ANY, trigger_direction: ANY, effect_score: 1, actions: [] });
    setModalOpen(true);
  };

  const openEdit = async (id: string) => {
    const pb = await getPlaybook(id);
    setEditingId(id);
    form.setFieldsValue({
      name: pb.name, description: pb.description,
      trigger_severity: pb.trigger_severity ?? ANY,
      trigger_direction: pb.trigger_direction ?? ANY,
      effect_score: pb.effect_score, process_template_id: pb.process_template_id ?? undefined,
      indicator_ids: pb.indicator_ids,
      actions: pb.actions.map((a) => ({ action: a.action, checklist: a.checklist.join(', ') })),
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const payload: PlaybookCreate = {
      name: values.name,
      description: values.description,
      trigger_severity: values.trigger_severity === ANY ? null : values.trigger_severity,
      trigger_direction: values.trigger_direction === ANY ? null : values.trigger_direction,
      effect_score: values.effect_score ?? 1,
      process_template_id: values.process_template_id ?? null,
      indicator_ids: values.indicator_ids ?? [],
      actions: (values.actions ?? [])
        .filter((a: { action?: string }) => a && a.action)
        .map((a: { action: string; checklist?: string }) => ({ action: a.action, checklist: csvToList(a.checklist) })),
    };
    try {
      if (editingId) await updatePlaybook(editingId, payload);
      else await createPlaybook(payload);
      message.success(t('settingsDss.saved'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('settingsDss.saveFailed'));
    }
  };

  const handleDelete = async (id: string) => {
    await deletePlaybook(id);
    message.success(t('settingsDss.deleted'));
    fetchData();
  };

  const templateName = (id: string | null) => templates.find((x) => x.id === id)?.name ?? null;

  const columns = [
    { title: t('settingsDss.name'), dataIndex: 'name', key: 'name' },
    { title: t('settingsDss.trigger'), key: 'trigger',
      render: (_: unknown, r: PlaybookListItem) => (
        <Space size={4}>
          <Tag>{r.trigger_severity ?? t('settingsDss.any')}</Tag>
          <Tag>{r.trigger_direction ?? t('settingsDss.any')}</Tag>
        </Space>
      ) },
    { title: t('settingsDss.effect'), dataIndex: 'effect_score', key: 'effect_score', width: 90 },
    { title: t('settingsDss.process'), key: 'process',
      render: (_: unknown, r: PlaybookListItem) => templateName(r.process_template_id) ?? '—' },
    {
      title: t('common.actions'), key: 'actions', width: 110,
      render: (_: unknown, r: PlaybookListItem) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r.id)} />
          <Popconfirm title={t('settingsDss.deleteConfirm')} onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        {t('settingsDss.newPlaybook')}
      </Button>
      <Table dataSource={playbooks} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal title={editingId ? t('settingsDss.editPlaybook') : t('settingsDss.newPlaybook')}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={680} forceRender>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('settingsDss.name')} rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label={t('settingsDss.description')}><Input.TextArea rows={2} /></Form.Item>
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="trigger_severity" label={t('settingsDss.triggerSeverity')}>
              <Select style={{ width: 140 }} options={[ANY, 'warning', 'critical'].map((v) => ({ label: v, value: v }))} />
            </Form.Item>
            <Form.Item name="trigger_direction" label={t('settingsDss.triggerDirection')}>
              <Select style={{ width: 130 }} options={[ANY, 'below', 'above'].map((v) => ({ label: v, value: v }))} />
            </Form.Item>
            <Form.Item name="effect_score" label={t('settingsDss.effect')}>
              <InputNumber min={0} step={0.5} style={{ width: 110 }} />
            </Form.Item>
          </Space>
          <Form.Item name="process_template_id" label={t('settingsDss.processTemplate')}>
            <Select allowClear options={templates.map((x) => ({ label: x.name, value: x.id }))} />
          </Form.Item>
          <Form.Item name="indicator_ids" label={t('settingsDss.indicatorScope')}
            extra={t('settingsDss.scopeHint')}>
            <Select mode="multiple" allowClear optionFilterProp="label"
              options={indicators.map((i) => ({ label: i.name, value: i.id }))} />
          </Form.Item>

          <div style={{ fontWeight: 500, margin: '4px 0 8px' }}>{t('settingsDss.recommendedActions')}</div>
          <Form.List name="actions">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 4 }}>
                    <Form.Item name={[field.name, 'action']} rules={[{ required: true, message: '' }]}>
                      <Input placeholder={t('settingsDss.action')} style={{ width: 240 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'checklist']}>
                      <Input placeholder={t('settingsDss.checklistCsv')} style={{ width: 240 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" icon={<PlusOutlined />} onClick={() => add()} block>
                  {t('settingsDss.addAction')}
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>
    </>
  );
}
