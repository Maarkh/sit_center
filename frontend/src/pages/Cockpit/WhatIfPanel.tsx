import { useEffect, useState } from 'react';
import {
  Card, Table, Tag, Button, Space, Empty, Modal, Input, Select, InputNumber, Statistic, Row, Col,
  Typography, App, Popconfirm,
} from 'antd';
import { ReloadOutlined, PlusOutlined, PlayCircleOutlined, DeleteOutlined, MinusCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/utils/formatters';
import {
  listScenarios, runScenario, createScenario, deleteScenario, getIndicatorTree,
} from '@/api/dss';
import type {
  ScenarioListItem, ScenarioResultRead, IndicatorTreeResponse, IndicatorTreeNode, AssumptionMode,
} from '@/types/dss';

const { Text } = Typography;

interface DraftAssumption { indicator_id?: string; mode: AssumptionMode; value: number; }

function flatten(tree: IndicatorTreeResponse): IndicatorTreeNode[] {
  return [...tree.goals.flatMap((g) => g.indicators), ...tree.unassigned];
}

export default function WhatIfPanel() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [scenarios, setScenarios] = useState<ScenarioListItem[]>([]);
  const [indicators, setIndicators] = useState<IndicatorTreeNode[]>([]);
  const [result, setResult] = useState<ScenarioResultRead | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [rows, setRows] = useState<DraftAssumption[]>([{ mode: 'target', value: 0 }]);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [sc, tr] = await Promise.all([listScenarios(), getIndicatorTree()]);
      setScenarios(sc);
      setIndicators(flatten(tr));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const onRun = async (id: string) => {
    setRunning(true);
    try {
      setResult(await runScenario(id));
      fetchAll();
    } finally {
      setRunning(false);
    }
  };

  const onCreate = async () => {
    const assumptions = rows.filter((r) => r.indicator_id).map((r) => ({
      indicator_id: r.indicator_id as string, mode: r.mode, value: r.value,
    }));
    if (!name || assumptions.length === 0) {
      message.warning(t('cockpit.scenarioNeedsAssumption'));
      return;
    }
    const sc = await createScenario({ name, assumptions });
    setModalOpen(false);
    setName('');
    setRows([{ mode: 'target', value: 0 }]);
    message.success(t('cockpit.scenarioCreated'));
    await fetchAll();
    onRun(sc.id);
  };

  const onDelete = async (id: string) => {
    await deleteScenario(id);
    fetchAll();
  };

  const scenarioColumns = [
    { title: t('cockpit.scenario'), dataIndex: 'name', key: 'name', ellipsis: true },
    { title: t('cockpit.potential'), dataIndex: 'potential_value', key: 'potential_value', width: 110,
      render: (v: number | null) => v == null ? <Text type="secondary">—</Text> : <Text strong>{v.toFixed(2)}</Text> },
    { title: t('cockpit.created'), dataIndex: 'created_at', key: 'created_at', render: formatDate },
    {
      title: t('common.actions'), key: 'actions', width: 130,
      render: (_: unknown, r: ScenarioListItem) => (
        <Space>
          <Button size="small" type="primary" icon={<PlayCircleOutlined />} loading={running}
            onClick={() => onRun(r.id)}>{t('cockpit.run')}</Button>
          <Popconfirm title={t('common.delete') + '?'} onConfirm={() => onDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const resultColumns = [
    { title: t('cockpit.indicator'), dataIndex: 'indicator_name', key: 'indicator_name', ellipsis: true,
      render: (v: string | null, r: { indicator_id: string }) => v || r.indicator_id.slice(0, 8) },
    { title: t('cockpit.baseline'), dataIndex: 'baseline', key: 'baseline', width: 100,
      render: (v: number | null) => v == null ? '-' : v.toFixed(2) },
    { title: t('cockpit.projectedVal'), dataIndex: 'projected', key: 'projected', width: 100,
      render: (v: number | null) => v == null ? '-' : v.toFixed(2) },
    {
      title: t('cockpit.effect'), key: 'effect', width: 160,
      render: (_: unknown, r: ScenarioResultRead['results'][number]) =>
        r.improved ? <Tag color="green">{t('cockpit.improved')}</Tag>
        : r.worsened ? <Tag color="red">{t('cockpit.worsened')}</Tag>
        : <Tag>{t('cockpit.unchanged')}</Tag>,
    },
  ];

  return (
    <>
      <Card title={t('cockpit.scenarios')} loading={loading}
        extra={
          <Space>
            <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
              {t('cockpit.newScenario')}
            </Button>
            <Button size="small" icon={<ReloadOutlined />} onClick={fetchAll} />
          </Space>
        }>
        {scenarios.length === 0
          ? <Empty description={t('cockpit.noScenarios')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          : <Table size="small" rowKey="id" dataSource={scenarios} columns={scenarioColumns} pagination={false} />}
      </Card>

      {result && (
        <Card title={t('cockpit.scenarioResult')} style={{ marginTop: 16 }}>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Statistic title={t('cockpit.potential')} value={result.potential_value} precision={2}
                styles={{ content: { color: result.potential_value > 0 ? '#389e0d' : undefined } }} />
            </Col>
            <Col span={12}>
              <Statistic title={t('cockpit.breachesAvoided')} value={result.breaches_avoided} />
            </Col>
          </Row>
          <Table size="small" rowKey="indicator_id" dataSource={result.results} columns={resultColumns} pagination={false} />
        </Card>
      )}

      <Modal title={t('cockpit.newScenario')} open={modalOpen} onCancel={() => setModalOpen(false)}
        onOk={onCreate} okText={t('cockpit.createAndRun')} width={640}>
        <Input placeholder={t('cockpit.scenarioName')} value={name} onChange={(e) => setName(e.target.value)}
          style={{ marginBottom: 12 }} />
        <Text type="secondary">{t('cockpit.assumptions')}</Text>
        <Space orientation="vertical" style={{ width: '100%', marginTop: 8 }}>
          {rows.map((r, idx) => (
            <Space key={idx} wrap>
              <Select placeholder={t('cockpit.indicator')} style={{ width: 220 }} value={r.indicator_id}
                showSearch optionFilterProp="label"
                options={indicators.map((i) => ({ label: i.name, value: i.id }))}
                onChange={(v) => setRows(rows.map((x, i) => i === idx ? { ...x, indicator_id: v } : x))} />
              <Select style={{ width: 120 }} value={r.mode}
                options={[
                  { label: t('cockpit.modeTarget'), value: 'target' },
                  { label: t('cockpit.modeDelta'), value: 'delta' },
                  { label: t('cockpit.modeDeltaPct'), value: 'delta_pct' },
                ]}
                onChange={(v) => setRows(rows.map((x, i) => i === idx ? { ...x, mode: v } : x))} />
              <InputNumber value={r.value} onChange={(v) => setRows(rows.map((x, i) => i === idx ? { ...x, value: v ?? 0 } : x))} />
              {rows.length > 1 && (
                <Button type="text" icon={<MinusCircleOutlined />} onClick={() => setRows(rows.filter((_, i) => i !== idx))} />
              )}
            </Space>
          ))}
          <Button type="dashed" icon={<PlusOutlined />} onClick={() => setRows([...rows, { mode: 'target', value: 0 }])}>
            {t('cockpit.addAssumption')}
          </Button>
        </Space>
      </Modal>
    </>
  );
}
