import { useEffect, useState, useMemo } from 'react';
import { App, Card, Col, Row, Statistic, Table, Tree, Tag, Button, Space, Tooltip, Typography } from 'antd';
import {
  WarningOutlined, ThunderboltOutlined, ClusterOutlined, AppstoreOutlined, ReloadOutlined, SyncOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/utils/formatters';
import {
  getIndicatorTree, listDeviations, listSituations, listPredictiveAlerts, correlateNow,
  indicatorStatus, LIGHT_COLOR,
} from '@/api/dss';
import type {
  IndicatorTreeResponse, DeviationRead, SituationListItem, PredictiveAlertRead, IndicatorTreeNode,
} from '@/types/dss';
import SituationDetailDrawer from './SituationDetailDrawer';

const { Text } = Typography;

function Dot({ color }: { color: string }) {
  return <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: color, marginRight: 8 }} />;
}

export default function CockpitPage() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [tree, setTree] = useState<IndicatorTreeResponse>({ goals: [], unassigned: [] });
  const [deviations, setDeviations] = useState<DeviationRead[]>([]);
  const [situations, setSituations] = useState<SituationListItem[]>([]);
  const [predictive, setPredictive] = useState<PredictiveAlertRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [correlating, setCorrelating] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [tr, dev, sit, pred] = await Promise.all([
        getIndicatorTree(),
        listDeviations({ active_only: true }),
        listSituations({ active_only: true }),
        listPredictiveAlerts({ active_only: true }),
      ]);
      setTree(tr);
      setDeviations(dev);
      setSituations(sit);
      setPredictive(pred);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const breachingIds = useMemo(() => new Set(deviations.map((d) => d.indicator_id)), [deviations]);
  const predictedIds = useMemo(() => new Set(predictive.map((p) => p.indicator_id)), [predictive]);

  const indicatorCount = useMemo(
    () => tree.goals.reduce((n, g) => n + g.indicators.length, 0) + tree.unassigned.length,
    [tree],
  );

  const corridorText = (i: IndicatorTreeNode) =>
    `[${i.target_low ?? '−∞'}, ${i.target_high ?? '+∞'}]${i.unit ? ' ' + i.unit : ''}`;

  const indicatorNode = (i: IndicatorTreeNode) => {
    const light = indicatorStatus(i, breachingIds, predictedIds);
    return {
      key: `ind:${i.id}`,
      title: (
        <Space size={4}>
          <Dot color={LIGHT_COLOR[light]} />
          <span>{i.name}</span>
          <Text type="secondary" style={{ fontSize: 12 }}>{corridorText(i)}</Text>
          {light === 'breach' && <Tag color="red">{t('cockpit.breach')}</Tag>}
          {light === 'predict' && <Tag color="orange">{t('cockpit.predicted')}</Tag>}
        </Space>
      ),
      children: i.factors.map((f) => ({
        key: `fac:${f.id}`,
        title: <Text type="secondary">{f.name} · {f.metrics.join(', ') || '—'}</Text>,
      })),
    };
  };

  const treeData = useMemo(() => {
    const goalNodes = tree.goals.map((g) => ({
      key: `goal:${g.id}`,
      title: <Space><AppstoreOutlined /><b>{g.name}</b>{g.owner_role && <Text type="secondary">({g.owner_role})</Text>}</Space>,
      children: g.indicators.map(indicatorNode),
    }));
    const unassigned = tree.unassigned.length
      ? [{ key: 'goal:_', title: <Text type="secondary">{t('cockpit.unassigned')}</Text>, children: tree.unassigned.map(indicatorNode) }]
      : [];
    return [...goalNodes, ...unassigned];
  }, [tree, breachingIds, predictedIds]); // eslint-disable-line react-hooks/exhaustive-deps

  const onCorrelate = async () => {
    setCorrelating(true);
    try {
      const res = await correlateNow();
      message.success(t('cockpit.correlated', { created: res.created ?? 0, resolved: res.resolved ?? 0 }));
      await fetchAll();
    } finally {
      setCorrelating(false);
    }
  };

  const sitColumns = [
    { title: t('cockpit.impact'), dataIndex: 'impact_score', key: 'impact_score', width: 90,
      sorter: (a: SituationListItem, b: SituationListItem) => a.impact_score - b.impact_score,
      defaultSortOrder: 'descend' as const,
      render: (v: number) => <Text strong>{v.toFixed(2)}</Text> },
    { title: t('cockpit.situation'), dataIndex: 'title', key: 'title', ellipsis: true },
    { title: t('cockpit.status'), dataIndex: 'status', key: 'status', width: 130,
      render: (s: string) => <Tag color={s === 'investigating' ? 'processing' : 'warning'}>{s}</Tag> },
    { title: t('cockpit.deviations'), dataIndex: 'deviation_count', key: 'deviation_count', width: 110 },
    { title: t('cockpit.opened'), dataIndex: 'opened_at', key: 'opened_at', render: formatDate },
  ];

  return (
    <>
      <Row gutter={16}>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('cockpit.activeSituations')} value={situations.length}
            prefix={<ClusterOutlined />} styles={{ content: { color: situations.length ? '#cf1322' : undefined } }} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('cockpit.openDeviations')} value={deviations.length}
            prefix={<WarningOutlined />} styles={{ content: { color: deviations.length ? '#d4380d' : undefined } }} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('cockpit.predictiveAlerts')} value={predictive.length}
            prefix={<ThunderboltOutlined />} styles={{ content: { color: predictive.length ? '#d48806' : undefined } }} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card><Statistic title={t('cockpit.indicators')} value={indicatorCount} prefix={<AppstoreOutlined />} /></Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col xs={24} lg={10}>
          <Card
            title={t('cockpit.indicatorTree')}
            loading={loading}
            extra={<Button size="small" icon={<ReloadOutlined />} onClick={fetchAll} />}
          >
            {treeData.length === 0
              ? <Text type="secondary">{t('cockpit.noIndicators')}</Text>
              : <Tree showLine defaultExpandAll treeData={treeData} selectable={false} />}
            <Space style={{ marginTop: 12 }} size="large" wrap>
              <span><Dot color={LIGHT_COLOR.ok} />{t('cockpit.lightOk')}</span>
              <span><Dot color={LIGHT_COLOR.predict} />{t('cockpit.lightPredict')}</span>
              <span><Dot color={LIGHT_COLOR.breach} />{t('cockpit.lightBreach')}</span>
              <span><Dot color={LIGHT_COLOR.idle} />{t('cockpit.lightIdle')}</span>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card
            title={t('cockpit.activeSituations')}
            loading={loading}
            extra={
              <Space>
                <Tooltip title={t('cockpit.correlateHint')}>
                  <Button size="small" icon={<SyncOutlined />} loading={correlating} onClick={onCorrelate}>
                    {t('cockpit.correlate')}
                  </Button>
                </Tooltip>
                <Button size="small" icon={<ReloadOutlined />} onClick={fetchAll} />
              </Space>
            }
          >
            <Table
              size="small"
              rowKey="id"
              dataSource={situations}
              columns={sitColumns}
              pagination={false}
              onRow={(r) => ({ onClick: () => setSelected(r.id), style: { cursor: 'pointer' } })}
            />
          </Card>
        </Col>
      </Row>

      <SituationDetailDrawer
        situationId={selected}
        open={selected !== null}
        onClose={() => setSelected(null)}
        onChanged={fetchAll}
      />
    </>
  );
}
