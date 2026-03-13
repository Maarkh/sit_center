import { Menu } from 'antd';
import {
  DashboardOutlined, GlobalOutlined, LineChartOutlined,
  AlertOutlined, FileTextOutlined, SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAdmin } = useAuthStore();

  const items = [
    { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
    { key: '/map', icon: <GlobalOutlined />, label: 'Map' },
    { key: '/metrics', icon: <LineChartOutlined />, label: 'Metrics' },
    { key: '/alerts', icon: <AlertOutlined />, label: 'Alerts' },
    { key: '/incidents', icon: <FileTextOutlined />, label: 'Incidents' },
    { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
    ...(isAdmin() ? [{ key: '/admin', icon: <TeamOutlined />, label: 'Admin' }] : []),
  ];

  return (
    <Menu
      theme="dark"
      mode="inline"
      selectedKeys={[location.pathname]}
      items={items}
      onClick={({ key }) => navigate(key)}
    />
  );
}
