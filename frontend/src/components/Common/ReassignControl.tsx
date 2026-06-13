import { useState } from 'react';
import { Select, App } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { getAssignableUsers } from '@/api/dss';

/**
 * D: pick a person and assign something to them. Generic over the target — the caller
 * supplies onAssign (assignStep for a process step, assignIncident for an incident).
 * roleHint (if given) restricts the user list to holders of that role; omit it to list
 * all active users (incidents have no role).
 */
export default function ReassignControl({ onAssign, roleHint, value, onDone }: {
  onAssign: (user: string) => Promise<unknown>;
  roleHint?: string | null;
  value?: string | null;
  onDone?: () => void;
}) {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [users, setUsers] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setUsers(await getAssignableUsers(roleHint ?? undefined)); } finally { setLoading(false); }
  };

  const onPick = async (user: string) => {
    setBusy(true);
    try {
      await onAssign(user);
      message.success(t('myTasks.assigned', { user }));
      onDone?.();
    } catch {
      message.error(t('myTasks.assignFailed'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Select
      size="small"
      style={{ minWidth: 150 }}
      placeholder={t('myTasks.assignTo')}
      value={value ?? undefined}
      loading={loading || busy}
      showSearch
      suffixIcon={<UserOutlined />}
      onDropdownVisibleChange={(open) => { if (open && users.length === 0) load(); }}
      onChange={onPick}
      options={users.map((u) => ({ label: u, value: u }))}
      notFoundContent={loading ? '…' : t('myTasks.noUsers')}
    />
  );
}
