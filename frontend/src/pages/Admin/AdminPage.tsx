import { Tabs } from 'antd';
import TenantsTab from './Tenants/TenantsTab';
import UsersTab from './Users/UsersTab';
import RolesTab from './Roles/RolesTab';
import AuditTab from './Audit/AuditTab';

export default function AdminPage() {
  return (
    <Tabs
      items={[
        { key: 'tenants', label: 'Tenants', children: <TenantsTab /> },
        { key: 'users', label: 'Users', children: <UsersTab /> },
        { key: 'roles', label: 'Roles', children: <RolesTab /> },
        { key: 'audit', label: 'Audit Log', children: <AuditTab /> },
      ]}
    />
  );
}
