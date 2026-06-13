import { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Tag, Button, Space, Drawer, Steps, Checkbox, Input, Empty, Typography, App, Tooltip,
} from 'antd';
import { ReloadOutlined, PlayCircleOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/utils/formatters';
import ReassignControl from '@/components/Common/ReassignControl';
import {
  listProcessInstances, getProcessInstance, startStep, updateStepChecklist, completeStep, assignStep,
} from '@/api/dss';
import type { ProcessInstanceListItem, ProcessInstanceRead, StepAssignmentRead } from '@/types/dss';

const { Text, Paragraph } = Typography;

const STATUS_COLOR: Record<string, string> = {
  running: 'processing', completed: 'success', cancelled: 'default',
  pending: 'default', active: 'blue', in_progress: 'processing', done: 'success', skipped: 'default',
};

function stepIndex(status: string): number {
  // Ant Steps "current" position from an assignment status.
  return status === 'done' || status === 'skipped' ? 3 : status === 'in_progress' ? 2 : status === 'active' ? 1 : 0;
}

export default function ProcessPanel() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [instances, setInstances] = useState<ProcessInstanceListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<ProcessInstanceRead | null>(null);
  const [busy, setBusy] = useState(false);

  const fetchAll = async () => {
    setLoading(true);
    try {
      setInstances(await listProcessInstances());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const loadDetail = useCallback(async (id: string) => {
    setDetail(await getProcessInstance(id));
  }, []);

  useEffect(() => { if (selected) loadDetail(selected); }, [selected, loadDetail]);

  const onStart = async (a: StepAssignmentRead) => {
    setBusy(true);
    try { await startStep(a.id); await loadDetail(selected!); } finally { setBusy(false); }
  };

  const onToggle = async (a: StepAssignmentRead, idx: number, checked: boolean) => {
    const next = a.checklist_state.map((c, i) => (i === idx ? { ...c, done: checked } : c));
    setBusy(true);
    try { await updateStepChecklist(a.id, next); await loadDetail(selected!); } finally { setBusy(false); }
  };

  const onComplete = async (a: StepAssignmentRead, report: string, force: boolean) => {
    setBusy(true);
    try {
      await completeStep(a.id, report || undefined, force);
      message.success(t('cockpit.stepCompleted'));
      await loadDetail(selected!);
      fetchAll();
    } catch {
      message.error(t('cockpit.checklistIncomplete'));
    } finally {
      setBusy(false);
    }
  };

  const columns = [
    { title: t('cockpit.process'), dataIndex: 'title', key: 'title', ellipsis: true,
      render: (v: string | null) => v || '—' },
    { title: t('cockpit.status'), dataIndex: 'status', key: 'status', width: 130,
      render: (s: string) => <Tag color={STATUS_COLOR[s] ?? 'default'}>{s}</Tag> },
    { title: t('cockpit.started'), dataIndex: 'started_at', key: 'started_at', render: formatDate },
    { title: t('cockpit.completed'), dataIndex: 'completed_at', key: 'completed_at', render: formatDate },
  ];

  return (
    <>
      <Card title={t('cockpit.processes')} loading={loading}
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={fetchAll} />}>
        {instances.length === 0
          ? <Empty description={t('cockpit.noProcesses')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          : <Table size="small" rowKey="id" dataSource={instances} columns={columns} pagination={false}
              onRow={(r) => ({ onClick: () => setSelected(r.id), style: { cursor: 'pointer' } })} />}
      </Card>

      <Drawer title={detail?.title ?? t('cockpit.process')} size="large"
        open={selected !== null} onClose={() => { setSelected(null); setDetail(null); }}>
        {detail && (
          <>
            <Space style={{ marginBottom: 16 }}>
              <Tag color={STATUS_COLOR[detail.status]}>{detail.status}</Tag>
              <Text type="secondary">{formatDate(detail.started_at)}</Text>
            </Space>
            <Steps orientation="vertical" size="small"
              items={detail.assignments.map((a) => ({
                title: (
                  <Space>
                    <span>{a.name}</span>
                    <Tag color={STATUS_COLOR[a.status] ?? 'default'}>{a.status}</Tag>
                    {a.escalated && <Tooltip title={t('cockpit.overdue')}><WarningOutlined style={{ color: '#cf1322' }} /></Tooltip>}
                    {a.assignee_role && <Text type="secondary">{a.assignee_role}</Text>}
                  </Space>
                ),
                status: (a.status === 'done' ? 'finish' : a.status === 'in_progress' || a.status === 'active' ? 'process' : 'wait') as 'finish' | 'process' | 'wait',
                content: <StepBody a={a} busy={busy} onStart={onStart} onToggle={onToggle} onComplete={onComplete} reload={() => loadDetail(selected!)} t={t} />,
              }))}
              current={Math.max(0, detail.assignments.findIndex((a) => stepIndex(a.status) < 3))}
            />
          </>
        )}
      </Drawer>
    </>
  );
}

interface StepBodyProps {
  a: StepAssignmentRead;
  busy: boolean;
  onStart: (a: StepAssignmentRead) => void;
  onToggle: (a: StepAssignmentRead, idx: number, checked: boolean) => void;
  onComplete: (a: StepAssignmentRead, report: string, force: boolean) => void;
  reload: () => void;
  t: (k: string) => string;
}

function StepBody({ a, busy, onStart, onToggle, onComplete, reload, t }: StepBodyProps) {
  const [report, setReport] = useState('');
  const active = a.status === 'active' || a.status === 'in_progress';
  const allDone = a.checklist_state.every((c) => c.done);

  if (a.status === 'done') {
    return a.report ? <Paragraph type="secondary" style={{ marginTop: 4 }}>✓ {a.report}</Paragraph> : null;
  }
  if (!active) return null;

  return (
    <div style={{ marginTop: 8 }}>
      {a.checklist_state.length > 0 && (
        <Space orientation="vertical" style={{ marginBottom: 8 }}>
          {a.checklist_state.map((c, idx) => (
            <Checkbox key={idx} checked={c.done} disabled={busy} onChange={(e) => onToggle(a, idx, e.target.checked)}>
              {c.item}
            </Checkbox>
          ))}
        </Space>
      )}
      <Space.Compact style={{ width: '100%', marginBottom: 8 }}>
        <Input placeholder={t('cockpit.report')} value={report} onChange={(e) => setReport(e.target.value)} />
      </Space.Compact>
      <Space>
        {a.status === 'active' && (
          <Button size="small" icon={<PlayCircleOutlined />} disabled={busy} onClick={() => onStart(a)}>
            {t('cockpit.start')}
          </Button>
        )}
        <Button size="small" type="primary" icon={<CheckCircleOutlined />} disabled={busy}
          onClick={() => onComplete(a, report, !allDone)}>
          {allDone ? t('cockpit.complete') : t('cockpit.completeForce')}
        </Button>
        <ReassignControl onAssign={(u) => assignStep(a.id, u)} roleHint={a.assignee_role} value={a.assignee} onDone={reload} />
      </Space>
    </div>
  );
}
