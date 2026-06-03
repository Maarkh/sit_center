import { useEffect, useState } from 'react';
import { Card, Table, Tag, Button, Space, Empty, Progress, Typography, App } from 'antd';
import { ReloadOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/utils/formatters';
import { listDecisions, listPlaybooks, getPlaybookStats, recordOutcome } from '@/api/dss';
import type { DecisionLogItem, PlaybookStats, PlaybookListItem } from '@/types/dss';

const { Text } = Typography;

type PlaybookRow = PlaybookListItem & PlaybookStats;

export default function DecisionLogPanel() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [decisions, setDecisions] = useState<DecisionLogItem[]>([]);
  const [playbooks, setPlaybooks] = useState<PlaybookRow[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [dec, pbs] = await Promise.all([listDecisions(), listPlaybooks()]);
      setDecisions(dec);
      const stats = await Promise.all(pbs.map((p) => getPlaybookStats(p.id).catch(() => null)));
      setPlaybooks(pbs.map((p, i) => ({ ...p, ...(stats[i] ?? { playbook_id: p.id, accepted: 0, decided: 0, resolved: 0, win_rate: null }) })));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const setOutcome = async (recId: string, resolved: boolean) => {
    await recordOutcome(recId, resolved);
    message.success(t('cockpit.outcomeRecorded'));
    fetchAll();
  };

  const decisionColumns = [
    { title: t('cockpit.playbook'), dataIndex: 'playbook_name', key: 'playbook_name', ellipsis: true,
      render: (v: string | null) => v || '—' },
    { title: t('cockpit.score'), dataIndex: 'score', key: 'score', width: 80, render: (v: number) => v.toFixed(2) },
    { title: t('cockpit.decidedBy'), dataIndex: 'decided_by', key: 'decided_by', width: 120 },
    { title: t('cockpit.decidedAt'), dataIndex: 'decided_at', key: 'decided_at', render: formatDate },
    {
      title: t('cockpit.outcome'), key: 'outcome', width: 200,
      render: (_: unknown, r: DecisionLogItem) => {
        if (r.resolved === null) {
          return (
            <Space>
              <Button size="small" icon={<CheckOutlined />} onClick={() => setOutcome(r.recommendation_id, true)}>
                {t('cockpit.resolvedYes')}
              </Button>
              <Button size="small" danger icon={<CloseOutlined />} onClick={() => setOutcome(r.recommendation_id, false)} />
            </Space>
          );
        }
        return (
          <Space>
            <Tag color={r.resolved ? 'green' : 'red'}>{r.resolved ? t('cockpit.resolvedYes') : t('cockpit.resolvedNo')}</Tag>
            {r.outcome_auto && <Tag>{t('cockpit.auto')}</Tag>}
          </Space>
        );
      },
    },
  ];

  const playbookColumns = [
    { title: t('cockpit.playbook'), dataIndex: 'name', key: 'name', ellipsis: true },
    { title: t('cockpit.accepted'), dataIndex: 'accepted', key: 'accepted', width: 100 },
    { title: t('cockpit.decided'), dataIndex: 'decided', key: 'decided', width: 100 },
    {
      title: t('cockpit.winRate'), key: 'win_rate', width: 200,
      render: (_: unknown, r: PlaybookRow) => r.win_rate == null
        ? <Text type="secondary">{t('cockpit.noData')}</Text>
        : <Progress percent={Math.round(r.win_rate * 100)}
            strokeColor={r.win_rate >= 0.6 ? '#389e0d' : r.win_rate >= 0.4 ? '#d48806' : '#cf1322'} size="small" />,
    },
  ];

  return (
    <>
      <Card title={t('cockpit.decisionLog')} loading={loading}
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={fetchAll} />}>
        {decisions.length === 0
          ? <Empty description={t('cockpit.noDecisions')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          : <Table size="small" rowKey="recommendation_id" dataSource={decisions} columns={decisionColumns} pagination={false} />}
      </Card>

      <Card title={t('cockpit.playbookWinRates')} style={{ marginTop: 16 }} loading={loading}>
        {playbooks.length === 0
          ? <Empty description={t('cockpit.noPlaybooks')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          : <Table size="small" rowKey="id" dataSource={playbooks} columns={playbookColumns} pagination={false} />}
      </Card>
    </>
  );
}
