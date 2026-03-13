import { Tabs } from 'antd';
import TenantsTab from './Tenants/TenantsTab';
import UsersTab from './Users/UsersTab';
import RolesTab from './Roles/RolesTab';
import AuditTab from './Audit/AuditTab';
import { useTranslation } from 'react-i18next';

export default function AdminPage() {
  const { t } = useTranslation();

  return (
    <Tabs
      items={[
        { key: 'tenants', label: t('admin.tenants'), children: <TenantsTab /> },
        { key: 'users', label: t('admin.users'), children: <UsersTab /> },
        { key: 'roles', label: t('admin.roles'), children: <RolesTab /> },
        { key: 'audit', label: t('admin.audit'), children: <AuditTab /> },
      ]}
    />
  );
}
