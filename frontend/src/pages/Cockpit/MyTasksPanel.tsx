import { useEffect, useState, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Checkbox, Input, Empty, Typography, App, Tooltip } from 'antd';
import { ReloadOutlined, PlayCircleOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import ReassignControl from '@/components/Common/ReassignControl';
import { formatDate } from '@/utils/formatters';
import { getMyTasks, startStep, updateStepChecklist, completeStep } from '@/api/dss';
import type { MyTask } from '@/types/dss';

const { Text } = Typography;

const STATUS_COLOR: Record<string, string> = {
  pending: 'default', active: 'blue', in_progress: 'processing', done: 'success', skipped: 'default',
};

export default function MyTasksPanel() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [tasks, setTasks] = useState<MyTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reports, setReports] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    try { setTasks(await getMyTasks(true)); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onStart = async (a: MyTask) => {
    setBusy(true);
    try { await startStep(a.id); await load(); } finally { setBusy(false); }
  };

  const onToggle = async (a: MyTask, idx: number, checked: boolean) => {
    const next = a.checklist_state.map((c, i) => (i === idx ? { ...c, done: checked } : c));
    setBusy(true);
    try { await updateStepChecklist(a.id, next); await load(); } finally { setBusy(false); }
  };

  const onComplete = async (a: MyTask) => {
    const allDone = a.checklist_state.every((c) => c.done);
    setBusy(true);
    try {
      await completeStep(a.id, reports[a.id] || undefined, !allDone);
      message.success(t('cockpit.stepCompleted'));
      await load();
    } catch {
      message.error(t('cockpit.checklistIncomplete'));
    } finally {
      setBusy(false);
    }
  };

  const columns = [
    { title: t('cockpit.process'), dataIndex: 'instance_title', key: 'instance_title', ellipsis: true,
      render: (v: string | null) => v || '—' },
    { title: t('myTasks.step'), dataIndex: 'name', key: 'name', ellipsis: true },
    { title: t('settingsDss.role'), dataIndex: 'assignee_role', key: 'assignee_role', width: 130,
      render: (v: string | null) => (v ? <Tag>{v}</Tag> : '—') },
    { title: t('myTasks.assignee'), dataIndex: 'assignee', key: 'assignee', width: 120,
      render: (v: string | null) => v || <Text type="secondary">{t('myTasks.unclaimed')}</Text> },
    { title: t('cockpit.status'), dataIndex: 'status', key: 'status', width: 120,
      render: (s: string, r: MyTask) => (
        <Space size={4}>
          <Tag color={STATUS_COLOR[s] ?? 'default'}>{s}</Tag>
          {r.escalated && <Tooltip title={t('cockpit.overdue')}><WarningOutlined style={{ color: '#cf1322' }} /></Tooltip>}
        </Space>
      ) },
    { title: t('myTasks.due'), dataIndex: 'due_at', key: 'due_at', width: 150,
      render: (v: string | null) => (v ? formatDate(v) : '—') },
    { title: t('common.actions'), key: 'actions', width: 280,
      render: (_: unknown, a: MyTask) => {
        const actionable = a.status === 'active' || a.status === 'in_progress';
        const allDone = a.checklist_state.every((c) => c.done);
        return (
          <Space wrap>
            {a.status === 'active' && (
              <Button size="small" icon={<PlayCircleOutlined />} disabled={busy} onClick={() => onStart(a)}>
                {t('cockpit.start')}
              </Button>
            )}
            {actionable && (
              <Button size="small" type="primary" icon={<CheckCircleOutlined />} disabled={busy}
                onClick={() => onComplete(a)}>
                {allDone ? t('cockpit.complete') : t('cockpit.completeForce')}
              </Button>
            )}
            <ReassignControl assignmentId={a.id} roleHint={a.assignee_role} value={a.assignee} onDone={load} />
          </Space>
        );
      } },
  ];

  return (
    <>
      <Card title={t('myTasks.title')} loading={loading}
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={load} />}>
        {tasks.length === 0
          ? <Empty description={t('myTasks.empty')} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          : (
            <Table size="small" rowKey="id" dataSource={tasks} columns={columns} pagination={false}
              expandable={{
                rowExpandable: (a) => a.checklist_state.length > 0,
                expandedRowRender: (a) => (
                  <Space orientation="vertical" style={{ width: '100%' }}>
                    {a.checklist_state.map((c, idx) => (
                      <Checkbox key={idx} checked={c.done}
                        disabled={busy || !(a.status === 'active' || a.status === 'in_progress')}
                        onChange={(e) => onToggle(a, idx, e.target.checked)}>
                        {c.item}
                      </Checkbox>
                    ))}
                    {(a.status === 'active' || a.status === 'in_progress') && (
                      <Input size="small" style={{ maxWidth: 360 }} placeholder={t('cockpit.report')}
                        value={reports[a.id] ?? ''}
                        onChange={(e) => setReports((p) => ({ ...p, [a.id]: e.target.value }))} />
                    )}
                  </Space>
                ),
              }}
            />
          )}
      </Card>
    </>
  );
}
