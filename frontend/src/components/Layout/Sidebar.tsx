import { Menu } from 'antd';
import {
  DashboardOutlined, GlobalOutlined, LineChartOutlined,
  AlertOutlined, FileTextOutlined, SettingOutlined,
  TeamOutlined, RadarChartOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { useTranslation } from 'react-i18next';
import { useIsMobile } from '@/hooks/useBreakpoint';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAdmin } = useAuthStore();
  const { toggleSidebar } = useUIStore();
  const { t } = useTranslation();
  const isMobile = useIsMobile();

  const items = [
    { key: '/', icon: <DashboardOutlined />, label: t('sidebar.dashboard') },
    { key: '/cockpit', icon: <RadarChartOutlined />, label: t('sidebar.cockpit') },
    { key: '/map', icon: <GlobalOutlined />, label: t('sidebar.map') },
    { key: '/metrics', icon: <LineChartOutlined />, label: t('sidebar.metrics') },
    { key: '/alerts', icon: <AlertOutlined />, label: t('sidebar.alerts') },
    { key: '/incidents', icon: <FileTextOutlined />, label: t('sidebar.incidents') },
    { key: '/settings', icon: <SettingOutlined />, label: t('sidebar.settings') },
    ...(isAdmin() ? [{ key: '/admin', icon: <TeamOutlined />, label: t('sidebar.admin') }] : []),
  ];

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={items}
      onClick={({ key }) => {
        navigate(key);
        if (isMobile) toggleSidebar();
      }}
    />
  );
}
