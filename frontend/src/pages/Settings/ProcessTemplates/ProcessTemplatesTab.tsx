import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Select, AutoComplete, Space, Popconfirm, Tag, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, MinusCircleOutlined, EyeOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import PageHelp from '@/components/Common/PageHelp';
import {
  listProcessTemplates, getProcessTemplate, createProcessTemplate, deleteProcessTemplate,
  getAssignmentRoles,
} from '@/api/dss';
import type { ProcessTemplateListItem, ProcessTemplateCreate, ProcessTemplateRead } from '@/types/dss';

const csvToList = (s?: string): string[] => (s ?? '').split(',').map((x) => x.trim()).filter(Boolean);

export default function ProcessTemplatesTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [templates, setTemplates] = useState<ProcessTemplateListItem[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [viewing, setViewing] = useState<ProcessTemplateRead | null>(null);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tmpls, rls] = await Promise.all([listProcessTemplates(), getAssignmentRoles().catch(() => [])]);
      setTemplates(tmpls);
      setRoles(rls);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreate = () => {
    form.resetFields();
    form.setFieldsValue({ is_active: true, steps: [{ step_type: 'sequential' }] });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const payload: ProcessTemplateCreate = {
      name: values.name,
      description: values.description,
      is_active: values.is_active ?? true,
      steps: (values.steps ?? [])
        .filter((s: { name?: string }) => s && s.name)
        .map((s: { name: string; step_type?: string; assignee_role?: string; checklist?: string; due_after_minutes?: number }, i: number) => ({
          name: s.name,
          step_order: i,
          step_type: (s.step_type as 'sequential' | 'parallel') ?? 'sequential',
          assignee_role: s.assignee_role || null,
          checklist: csvToList(s.checklist),
          due_after_minutes: s.due_after_minutes ?? null,
        })),
    };
    if (payload.steps.length === 0) { message.error(t('settingsProc.needStep')); return; }
    try {
      await createProcessTemplate(payload);
      message.success(t('settingsDss.saved'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('settingsDss.saveFailed'));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteProcessTemplate(id);
    message.success(t('settingsDss.deleted'));
    fetchData();
  };

  const roleOptions = roles.map((r) => ({ value: r }));

  const columns = [
    { title: t('settingsDss.name'), dataIndex: 'name', key: 'name' },
    { title: t('settingsDss.description'), dataIndex: 'description', key: 'description', ellipsis: true,
      render: (v: string | null) => v || '—' },
    { title: t('settingsProc.steps'), dataIndex: 'step_count', key: 'step_count', width: 90 },
    { title: t('settingsDss.active'), dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '✓' : '—'}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 110,
      render: (_: unknown, r: ProcessTemplateListItem) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={async () => setViewing(await getProcessTemplate(r.id))} />
          <Popconfirm title={t('settingsDss.deleteConfirm')} onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <PageHelp section="processTemplates" />
      <Button type="primary" icon={<PlusOutlined />} onClick={openCreate} style={{ marginBottom: 16 }}>
        {t('settingsProc.newTemplate')}
      </Button>
      <Table dataSource={templates} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal title={t('settingsProc.newTemplate')} open={modalOpen} onOk={handleSubmit}
        onCancel={() => setModalOpen(false)} width={760} forceRender>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('settingsDss.name')} rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label={t('settingsDss.description')}><Input.TextArea rows={2} /></Form.Item>

          <div style={{ fontWeight: 500, margin: '4px 0 2px' }}>{t('settingsProc.steps')}</div>
          <div style={{ color: '#888', fontSize: 12, margin: '0 0 8px' }}>{t('settingsProc.stepsHint')}</div>
          <Form.List name="steps">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 4 }} wrap>
                    <Form.Item name={[field.name, 'name']} rules={[{ required: true, message: '' }]}>
                      <Input placeholder={t('settingsProc.stepName')} style={{ width: 200 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'assignee_role']} tooltip={t('settingsProc.roleHint')}>
                      <AutoComplete options={roleOptions} style={{ width: 150 }}
                        placeholder={t('settingsDss.role')} filterOption
                        allowClear />
                    </Form.Item>
                    <Form.Item name={[field.name, 'step_type']}>
                      <Select style={{ width: 120 }}
                        options={[{ value: 'sequential', label: t('settingsProc.sequential') },
                          { value: 'parallel', label: t('settingsProc.parallel') }]} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'checklist']}>
                      <Input placeholder={t('settingsDss.checklistCsv')} style={{ width: 200 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'due_after_minutes']}>
                      <InputNumber placeholder={t('settingsProc.dueMin')} min={1} style={{ width: 110 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ step_type: 'sequential' })} block>
                  {t('settingsProc.addStep')}
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal title={viewing?.name} open={viewing !== null} footer={null} onCancel={() => setViewing(null)} width={620}>
        {viewing && (
          <Space orientation="vertical" style={{ width: '100%' }}>
            {viewing.description && <div style={{ color: '#666' }}>{viewing.description}</div>}
            {viewing.steps.map((s) => (
              <div key={s.id} style={{ borderLeft: '3px solid #1677ff', paddingLeft: 8 }}>
                <b>{s.step_order + 1}. {s.name}</b>
                {s.assignee_role && <Tag style={{ marginLeft: 8 }}>{s.assignee_role}</Tag>}
                {s.due_after_minutes && <Tag color="orange">SLA {s.due_after_minutes}м</Tag>}
                {s.checklist.length > 0 && (
                  <ul style={{ margin: '4px 0 0', color: '#666' }}>{s.checklist.map((c, i) => <li key={i}>{c}</li>)}</ul>
                )}
              </div>
            ))}
          </Space>
        )}
      </Modal>
    </>
  );
}
