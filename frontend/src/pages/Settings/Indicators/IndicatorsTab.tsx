import { useEffect, useState } from 'react';
import {
  Table, Button, Modal, Form, Input, InputNumber, Select, AutoComplete, Switch, Space, Popconfirm, Tag, App,
} from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, MinusCircleOutlined, AppstoreAddOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import PageHelp from '@/components/Common/PageHelp';
import {
  listIndicators, createIndicator, updateIndicator, deleteIndicator,
  listGoals, createGoal, updateGoal, deleteGoal,
  getAssignmentRoles, getAssignableUsers,
} from '@/api/dss';
import { listChains } from '@/api/escalation';
import type { IndicatorRead, GoalRead, IndicatorCreate } from '@/types/dss';
import type { EscalationChain } from '@/types/escalation';

const csvToList = (s?: string): string[] =>
  (s ?? '').split(',').map((x) => x.trim()).filter(Boolean);

export default function IndicatorsTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [indicators, setIndicators] = useState<IndicatorRead[]>([]);
  const [goals, setGoals] = useState<GoalRead[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [users, setUsers] = useState<string[]>([]);
  const [chains, setChains] = useState<EscalationChain[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<IndicatorRead | null>(null);
  const [goalModalOpen, setGoalModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<GoalRead | null>(null);
  const [form] = Form.useForm();
  const [goalForm] = Form.useForm();
  // C: when the corridor self-learns (baseline), manual bounds are irrelevant.
  const corridorType = Form.useWatch('corridor_type', form);
  const isBaseline = corridorType === 'baseline';

  const fetchData = async () => {
    setLoading(true);
    try {
      const [inds, gls] = await Promise.all([listIndicators(), listGoals()]);
      setIndicators(inds);
      setGoals(gls);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // Responsibility-map pick lists (roles / users / escalation chains). Best-effort.
  useEffect(() => {
    getAssignmentRoles().then(setRoles).catch(() => {});
    getAssignableUsers().then(setUsers).catch(() => {});
    listChains().then(setChains).catch(() => {});
  }, []);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    // Default to the self-learning corridor so operators don't hand-type thresholds.
    form.setFieldsValue({ corridor_type: 'baseline', direction: 'both', chronicle_threshold: 3, is_active: true, factors: [{}] });
    setModalOpen(true);
  };

  const openEdit = (ind: IndicatorRead) => {
    setEditing(ind);
    form.setFieldsValue({
      ...ind,
      owner_role: ind.owner_role ?? undefined,
      owner_user: ind.owner_user ?? undefined,
      escalation_chain_id: ind.escalation_chain_id ?? undefined,
      factors: ind.factors.map((f) => ({ name: f.name, weight: f.weight, metrics: f.metrics.join(', ') })),
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    let values;
    try { values = await form.validateFields(); } catch { return; }
    const payload: IndicatorCreate = {
      name: values.name,
      description: values.description,
      unit: values.unit ?? '',
      goal_id: values.goal_id ?? null,
      target_low: values.target_low ?? null,
      target_high: values.target_high ?? null,
      corridor_type: values.corridor_type,
      direction: values.direction,
      chronicle_threshold: values.chronicle_threshold,
      is_active: values.is_active ?? true,
      owner_role: values.owner_role ?? null,
      owner_user: values.owner_user ?? null,
      escalation_chain_id: values.escalation_chain_id ?? null,
      factors: (values.factors ?? [])
        .filter((f: { name?: string }) => f && f.name)
        .map((f: { name: string; weight?: number; metrics?: string }) => ({
          name: f.name, weight: f.weight ?? 1.0, metrics: csvToList(f.metrics),
        })),
    };
    try {
      if (editing) await updateIndicator(editing.id, payload);
      else await createIndicator(payload);
      message.success(t('settingsDss.saved'));
      setModalOpen(false);
      fetchData();
    } catch {
      message.error(t('settingsDss.saveFailed'));
    }
  };

  const handleDelete = async (id: string) => {
    await deleteIndicator(id);
    message.success(t('settingsDss.deleted'));
    fetchData();
  };

  const openGoalCreate = () => {
    setEditingGoal(null);
    goalForm.resetFields();
    setGoalModalOpen(true);
  };

  const openGoalEdit = (g: GoalRead) => {
    setEditingGoal(g);
    goalForm.setFieldsValue({ name: g.name, owner_role: g.owner_role ?? undefined,
      escalation_chain_id: g.escalation_chain_id ?? undefined, description: g.description });
    setGoalModalOpen(true);
  };

  const handleSaveGoal = async () => {
    let values;
    try { values = await goalForm.validateFields(); } catch { return; }
    if (editingGoal) await updateGoal(editingGoal.id, values);
    else await createGoal(values);
    message.success(t('settingsDss.saved'));
    goalForm.resetFields();
    setEditingGoal(null);
    setGoalModalOpen(false);
    fetchData();
  };

  const removeGoal = async (g: GoalRead) => {
    await deleteGoal(g.id);
    if (editingGoal?.id === g.id) { setEditingGoal(null); goalForm.resetFields(); }
    fetchData();
  };

  const goalName = (id: string | null) => goals.find((g) => g.id === id)?.name ?? '—';

  const columns = [
    { title: t('settingsDss.name'), dataIndex: 'name', key: 'name' },
    { title: t('settingsDss.goal'), key: 'goal', render: (_: unknown, r: IndicatorRead) => goalName(r.goal_id) },
    { title: t('settingsDss.corridor'), key: 'corridor',
      render: (_: unknown, r: IndicatorRead) => `[${r.target_low ?? '−∞'}, ${r.target_high ?? '+∞'}]${r.unit ? ' ' + r.unit : ''}` },
    { title: t('settingsDss.direction'), dataIndex: 'direction', key: 'direction', width: 90 },
    { title: t('settingsDss.owner'), key: 'owner', width: 130,
      render: (_: unknown, r: IndicatorRead) => (r.owner_user || r.owner_role
        ? <Tag color="blue">{r.owner_user || r.owner_role}</Tag>
        : <span style={{ color: '#bbb' }}>{t('settingsDss.fromGoal')}</span>) },
    { title: t('settingsDss.factors'), key: 'factors', width: 90,
      render: (_: unknown, r: IndicatorRead) => r.factors.length },
    { title: t('settingsDss.active'), dataIndex: 'is_active', key: 'is_active', width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '✓' : '—'}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 110,
      render: (_: unknown, r: IndicatorRead) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          <Popconfirm title={t('settingsDss.deleteConfirm')} onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <PageHelp section="indicators" />
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>{t('settingsDss.newIndicator')}</Button>
        <Button icon={<AppstoreAddOutlined />} onClick={openGoalCreate}>{t('settingsDss.newGoal')}</Button>
      </Space>
      <Table dataSource={indicators} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal title={editing ? t('settingsDss.editIndicator') : t('settingsDss.newIndicator')}
        open={modalOpen} onOk={handleSubmit} onCancel={() => setModalOpen(false)} width={680} forceRender>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('settingsDss.name')} rules={[{ required: true }]}><Input /></Form.Item>
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="goal_id" label={t('settingsDss.goal')} style={{ minWidth: 220 }}>
              <Select allowClear options={goals.map((g) => ({ label: g.name, value: g.id }))} />
            </Form.Item>
            <Form.Item name="unit" label={t('settingsDss.unit')}><Input style={{ width: 100 }} placeholder="%" /></Form.Item>
            <Form.Item name="corridor_type" label={t('settingsDss.corridorType')}>
              <Select style={{ width: 130 }} options={[{ label: 'static', value: 'static' }, { label: 'baseline', value: 'baseline' }]} />
            </Form.Item>
          </Space>
          {isBaseline && (
            <div style={{ color: '#888', fontSize: 12, margin: '0 0 8px' }}>{t('settingsDss.baselineHint')}</div>
          )}
          <Space style={{ display: 'flex' }} align="start">
            <Form.Item name="target_low" label={t('settingsDss.targetLow')}>
              <InputNumber style={{ width: 130 }} disabled={isBaseline} placeholder={isBaseline ? t('settingsDss.auto') : undefined} />
            </Form.Item>
            <Form.Item name="target_high" label={t('settingsDss.targetHigh')}>
              <InputNumber style={{ width: 130 }} disabled={isBaseline} placeholder={isBaseline ? t('settingsDss.auto') : undefined} />
            </Form.Item>
            <Form.Item name="direction" label={t('settingsDss.direction')}>
              <Select style={{ width: 110 }} options={['both', 'below', 'above'].map((v) => ({ label: v, value: v }))} />
            </Form.Item>
            <Form.Item name="chronicle_threshold" label={t('settingsDss.chronicle')}>
              <InputNumber min={1} max={100} style={{ width: 90 }} />
            </Form.Item>
            <Form.Item name="is_active" label={t('settingsDss.active')} valuePropName="checked"><Switch /></Form.Item>
          </Space>

          <div style={{ fontWeight: 500, margin: '4px 0 2px' }}>{t('settingsDss.responsibility')}</div>
          <div style={{ color: '#888', fontSize: 12, margin: '0 0 8px' }}>{t('settingsDss.responsibilityHint')}</div>
          <Space style={{ display: 'flex' }} align="start" wrap>
            <Form.Item name="owner_role" label={t('settingsDss.ownerRole')} style={{ minWidth: 160 }}>
              <Select allowClear showSearch placeholder={t('settingsDss.fromGoal')}
                options={roles.map((r) => ({ label: r, value: r }))} />
            </Form.Item>
            <Form.Item name="owner_user" label={t('settingsDss.ownerUser')} style={{ minWidth: 160 }}>
              <AutoComplete allowClear options={users.map((u) => ({ value: u }))}
                placeholder={t('settingsDss.optional')} filterOption />
            </Form.Item>
            <Form.Item name="escalation_chain_id" label={t('settingsDss.escalationChain')} style={{ minWidth: 200 }}>
              <Select allowClear showSearch optionFilterProp="label" placeholder={t('settingsDss.fromGoalOrDefault')}
                options={chains.map((c) => ({ label: c.name, value: c.id }))} />
            </Form.Item>
          </Space>

          <div style={{ fontWeight: 500, margin: '4px 0 8px' }}>{t('settingsDss.factors')}</div>
          <Form.List name="factors">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 4 }}>
                    <Form.Item name={[field.name, 'name']} rules={[{ required: true, message: '' }]}>
                      <Input placeholder={t('settingsDss.factorName')} style={{ width: 160 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'weight']}>
                      <InputNumber placeholder={t('settingsDss.weight')} style={{ width: 90 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'metrics']}>
                      <Input placeholder={t('settingsDss.metricsCsv')} style={{ width: 240 }} />
                    </Form.Item>
                    <MinusCircleOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" icon={<PlusOutlined />} onClick={() => add({ weight: 1 })} block>
                  {t('settingsDss.addFactor')}
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      <Modal title={editingGoal ? t('settingsDss.editGoal', 'Редактировать цель') : t('settingsDss.newGoal')}
        open={goalModalOpen} onOk={handleSaveGoal} onCancel={() => setGoalModalOpen(false)} forceRender>
        <Form form={goalForm} layout="vertical">
          <Form.Item name="name" label={t('settingsDss.name')} rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="owner_role" label={t('settingsDss.ownerRole')} extra={t('settingsDss.goalOwnerHint')}>
            <Select allowClear showSearch options={roles.map((r) => ({ label: r, value: r }))} />
          </Form.Item>
          <Form.Item name="escalation_chain_id" label={t('settingsDss.escalationChain')}>
            <Select allowClear showSearch optionFilterProp="label"
              options={chains.map((c) => ({ label: c.name, value: c.id }))} />
          </Form.Item>
          <Form.Item name="description" label={t('settingsDss.description')}><Input.TextArea rows={2} /></Form.Item>
        </Form>
        {goals.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <div style={{ fontWeight: 500, marginBottom: 6 }}>{t('settingsDss.goals', 'Цели')}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {goals.map((g) => (
                <div key={g.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{g.name}{g.owner_role ? ` · ${g.owner_role}` : ''}</span>
                  <Space>
                    <Button size="small" icon={<EditOutlined />} onClick={() => openGoalEdit(g)} />
                    <Popconfirm title={t('settingsDss.deleteConfirm')} onConfirm={() => removeGoal(g)}>
                      <Button size="small" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                  </Space>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </>
  );
}
