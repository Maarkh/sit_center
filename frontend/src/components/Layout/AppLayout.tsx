import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import HeaderBar from './HeaderBar';
import { useUIStore } from '@/stores/uiStore';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useAlertStore } from '@/stores/alertStore';
import { AlertWebSocket } from '@/api/ws';
import { notification } from 'antd';
import type { AlertRead } from '@/types/alerts';

let wsInstance: AlertWebSocket | null = null;

export default function AppLayout() {
  const { sidebarCollapsed } = useUIStore();
  const { token } = useAuthStore();
  const { addLiveAlert } = useAlertStore();

  useEffect(() => {
    if (!token) return;

    wsInstance = new AlertWebSocket(token);
    wsInstance.onMessage((data) => {
      const alert = data as AlertRead;
      addLiveAlert(alert);
      notification.warning({
        message: `Alert: ${alert.metric_name}`,
        description: `Value: ${alert.value} | Status: ${alert.status}`,
        placement: 'topRight',
        duration: 5,
      });
    });
    wsInstance.connect();

    return () => {
      wsInstance?.disconnect();
      wsInstance = null;
    };
  }, [token, addLiveAlert]);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider trigger={null} collapsible collapsed={sidebarCollapsed} theme="dark">
        <div style={{ height: 32, margin: 16, color: '#fff', textAlign: 'center', fontWeight: 'bold', fontSize: sidebarCollapsed ? 14 : 18 }}>
          {sidebarCollapsed ? 'SC' : 'Sit Center'}
        </div>
        <Sidebar />
      </Layout.Sider>
      <Layout>
        <HeaderBar />
        <Layout.Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
