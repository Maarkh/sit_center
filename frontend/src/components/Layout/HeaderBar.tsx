import { Layout, Badge, Button, Dropdown, Space, Typography, Switch, Select } from 'antd';
import { BellOutlined, LogoutOutlined, UserOutlined, MenuFoldOutlined, MenuUnfoldOutlined, MoonOutlined, SunOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { useAlertStore } from '@/stores/alertStore';
import { useUIStore } from '@/stores/uiStore';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function HeaderBar() {
  const { user, logout } = useAuthStore();
  const { liveAlerts } = useAlertStore();
  const { sidebarCollapsed, toggleSidebar, darkMode, toggleDarkMode, language, setLanguage } = useUIStore();
  const navigate = useNavigate();
  const { t } = useTranslation();
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
      label: t('common.logout'),
      icon: <LogoutOutlined />,
      onClick: () => { logout(); navigate('/login'); },
    },
  ];

  return (
    <Layout.Header style={{ background: darkMode ? undefined : '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <Button
        type="text"
        icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={toggleSidebar}
      />
      <Space size="middle">
        <Select
          value={language}
          onChange={setLanguage}
          size="small"
          style={{ width: 70 }}
          options={[
            { label: 'RU', value: 'ru' },
            { label: 'EN', value: 'en' },
          ]}
        />
        <Switch
          checked={darkMode}
          onChange={toggleDarkMode}
          checkedChildren={<MoonOutlined />}
          unCheckedChildren={<SunOutlined />}
        />
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
