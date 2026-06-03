import { useEffect, useState, useCallback } from 'react';
import {
  App, Drawer, Descriptions, Tag, Button, Space, Table, Typography, Divider,
  Empty, Spin, Popconfirm,
} from 'antd';
import { ThunderboltOutlined, PlayCircleOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/utils/formatters';
import {
  getSituation, updateSituationStatus, generateRecommendations, listRecommendations,
  acceptRecommendation, dismissRecommendation,
} from '@/api/dss';
import type { SituationRead, DeviationRead, RecommendationRead } from '@/types/dss';

const { Paragraph, Text } = Typography;

const SEVERITY_COLOR: Record<string, string> = { critical: 'red', warning: 'orange' };

interface Props {
  situationId: string | null;
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
}

export default function SituationDetailDrawer({ situationId, open, onClose, onChanged }: Props) {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [situation, setSituation] = useState<SituationRead | null>(null);
  const [recs, setRecs] = useState<RecommendationRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  // The deviation recommendations are generated for: prefer the root-cause indicator's.
  const primaryDeviation = (s: SituationRead | null): DeviationRead | undefined => {
    if (!s || s.deviations.length === 0) return undefined;
    return s.deviations.find((d) => d.indicator_id === s.root_cause_indicator_id) ?? s.deviations[0];
  };

  const load = useCallback(async () => {
    if (!situationId) return;
    setLoading(true);
    try {
      const s = await getSituation(situationId);
      setSituation(s);
      const dev = primaryDeviation(s);
      setRecs(dev ? await listRecommendations({ deviation_id: dev.id }) : []);
    } finally {
      setLoading(false);
    }
  }, [situationId]);

  useEffect(() => { if (open && situationId) load(); }, [open, situationId, load]);

  const changeStatus = async (status: 'investigating' | 'resolved') => {
    if (!situationId) return;
    setBusy(true);
    try {
      await updateSituationStatus(situationId, status);
      message.success(t('cockpit.statusUpdated'));
      await load();
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const onGenerate = async () => {
    const dev = primaryDeviation(situation);
    if (!dev) return;
    setBusy(true);
    try {
      const r = await generateRecommendations(dev.id);
      setRecs(r);
      message.success(t('cockpit.recsGenerated', { count: r.length }));
    } finally {
      setBusy(false);
    }
  };

  const onAccept = async (id: string) => {
    setBusy(true);
    try {
      await acceptRecommendation(id);
      message.success(t('cockpit.recAccepted'));
      await load();
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const onDismiss = async (id: string) => {
    setBusy(true);
    try {
      await dismissRecommendation(id);
      await load();
    } finally {
      setBusy(false);
    }
  };

  const devColumns = [
    { title: t('cockpit.severity'), dataIndex: 'severity', key: 'severity', width: 100,
      render: (s: string) => <Tag color={SEVERITY_COLOR[s] ?? 'default'}>{s}</Tag> },
    { title: t('cockpit.direction'), dataIndex: 'direction', key: 'direction', width: 90 },
    { title: t('cockpit.value'), dataIndex: 'value', key: 'value', width: 90,
      render: (v: number | null) => (v == null ? '-' : v.toFixed(2)) },
    { title: t('cockpit.periods'), dataIndex: 'periods', key: 'periods', width: 80 },
    { title: t('cockpit.detected'), dataIndex: 'detected_at', key: 'detected_at', render: formatDate },
  ];

  const recColumns = [
    { title: '#', dataIndex: 'rank', key: 'rank', width: 50 },
    { title: t('cockpit.playbook'), dataIndex: 'playbook_name', key: 'playbook_name' },
    { title: t('cockpit.score'), dataIndex: 'score', key: 'score', width: 80,
      render: (v: number) => v.toFixed(2) },
    { title: t('cockpit.confidence'), dataIndex: 'confidence', key: 'confidence', width: 110,
      render: (v: number) => `${Math.round(v * 100)}%` },
    { title: t('cockpit.rationale'), dataIndex: 'rationale', key: 'rationale', ellipsis: true },
    { title: t('cockpit.status'), dataIndex: 'status', key: 'status', width: 110,
      render: (s: string) => <Tag color={s === 'accepted' ? 'green' : s === 'dismissed' ? 'default' : 'blue'}>{s}</Tag> },
    {
      title: t('common.actions'), key: 'actions', width: 160,
      render: (_: unknown, r: RecommendationRead) => r.status === 'proposed' ? (
        <Space>
          <Button size="small" type="primary" icon={<PlayCircleOutlined />} disabled={busy}
            onClick={() => onAccept(r.id)}>{t('cockpit.accept')}</Button>
          <Button size="small" icon={<CloseOutlined />} disabled={busy}
            onClick={() => onDismiss(r.id)} />
        </Space>
      ) : null,
    },
  ];

  const dev = primaryDeviation(situation);
  const active = situation && ['open', 'investigating'].includes(situation.status);

  return (
    <Drawer
      title={situation?.title ?? t('cockpit.situation')}
      size="large"
      open={open}
      onClose={onClose}
    >
      {loading || !situation ? <Spin /> : (
        <>
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label={t('cockpit.impact')}>
              <Text strong>{situation.impact_score.toFixed(2)}</Text>
            </Descriptions.Item>
            <Descriptions.Item label={t('cockpit.status')}>
              <Tag color={active ? 'processing' : 'default'}>{situation.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('cockpit.deviations')}>{situation.deviation_count}</Descriptions.Item>
            <Descriptions.Item label={t('cockpit.opened')}>{formatDate(situation.opened_at)}</Descriptions.Item>
          </Descriptions>

          {situation.root_cause_hypothesis && (
            <Paragraph type="secondary" style={{ marginTop: 12 }}>
              💡 {situation.root_cause_hypothesis}
            </Paragraph>
          )}

          {active && (
            <Space style={{ marginTop: 8 }}>
              {situation.status === 'open' && (
                <Button size="small" loading={busy} onClick={() => changeStatus('investigating')}>
                  {t('cockpit.investigate')}
                </Button>
              )}
              <Popconfirm title={t('cockpit.confirmResolve')} onConfirm={() => changeStatus('resolved')}>
                <Button size="small" loading={busy}>{t('cockpit.resolve')}</Button>
              </Popconfirm>
            </Space>
          )}

          <Divider titlePlacement="start">{t('cockpit.linkedDeviations')}</Divider>
          <Table size="small" rowKey="id" dataSource={situation.deviations} columns={devColumns} pagination={false} />

          <Divider titlePlacement="start">{t('cockpit.recommendations')}</Divider>
          <Space style={{ marginBottom: 12 }}>
            <Button type="primary" icon={<ThunderboltOutlined />} loading={busy} disabled={!dev}
              onClick={onGenerate}>
              {t('cockpit.generateRecs')}
            </Button>
            {dev && <Text type="secondary">{t('cockpit.forDeviation')}: {dev.direction} / {dev.severity}</Text>}
          </Space>
          {recs.length === 0
            ? <Empty description={t('cockpit.noRecs')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
            : <Table size="small" rowKey="id" dataSource={recs} columns={recColumns} pagination={false} />}
        </>
      )}
    </Drawer>
  );
}
