import { Layout, Badge, Button, Dropdown, Space, Typography } from 'antd';
import { BellOutlined, LogoutOutlined, UserOutlined, MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { useAlertStore } from '@/stores/alertStore';
import { useUIStore } from '@/stores/uiStore';
import { useNavigate } from 'react-router-dom';

export default function HeaderBar() {
  const { user, logout } = useAuthStore();
  const { liveAlerts } = useAlertStore();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const navigate = useNavigate();
  const firingCount = liveAlerts.filter((a) => a.status === 'firing').length;

  const userMenuItems = [
    {
      key: 'user',
      label: `${user?.sub} (${user?.tenant_id})`,
      icon: <UserOutlined />,
      disabled: true,
    },
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: () => { logout(); navigate('/login'); },
    },
  ];

  return (
    <Layout.Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <Button
        type="text"
        icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={toggleSidebar}
      />
      <Space size="large">
        <Badge count={firingCount} offset={[-2, 2]}>
          <Button type="text" icon={<BellOutlined />} onClick={() => navigate('/alerts')} />
        </Badge>
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Typography.Text style={{ cursor: 'pointer' }}>
            <UserOutlined /> {user?.sub}
          </Typography.Text>
        </Dropdown>
      </Space>
    </Layout.Header>
  );
}
