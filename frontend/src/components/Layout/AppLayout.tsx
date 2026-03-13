import { Layout, Drawer } from 'antd';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import HeaderBar from './HeaderBar';
import { useUIStore } from '@/stores/uiStore';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { useAlertStore } from '@/stores/alertStore';
import { AlertWebSocket } from '@/api/ws';
import { notification } from 'antd';
import { useTranslation } from 'react-i18next';
import { useIsMobile } from '@/hooks/useBreakpoint';
import type { AlertRead } from '@/types/alerts';

let wsInstance: AlertWebSocket | null = null;

export default function AppLayout() {
  const { sidebarCollapsed, darkMode, toggleSidebar } = useUIStore();
  const { token } = useAuthStore();
  const { addLiveAlert } = useAlertStore();
  const { t } = useTranslation();
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!token) return;

    wsInstance = new AlertWebSocket(token);
    wsInstance.onMessage((data) => {
      const alert = data as AlertRead;
      addLiveAlert(alert);
      notification.warning({
        message: `${t('sidebar.alerts')}: ${alert.metric_name}`,
        description: `${t('alerts.value')}: ${alert.value} | ${t('alerts.status')}: ${alert.status}`,
        placement: 'topRight',
        duration: 5,
      });
    });
    wsInstance.connect();

    return () => {
      wsInstance?.disconnect();
      wsInstance = null;
    };
  }, [token, addLiveAlert, t]);

  const sidebarContent = (
    <>
      <div style={{ height: 32, margin: 16, color: '#fff', textAlign: 'center', fontWeight: 'bold', fontSize: sidebarCollapsed && !isMobile ? 14 : 18 }}>
        {sidebarCollapsed && !isMobile ? t('app_short') : t('app_name')}
      </div>
      <Sidebar />
    </>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {isMobile ? (
        <Drawer
          placement="left"
          open={!sidebarCollapsed}
          onClose={toggleSidebar}
          width={220}
          styles={{ body: { padding: 0, background: '#001529' } }}
          closable={false}
        >
          {sidebarContent}
        </Drawer>
      ) : (
        <Layout.Sider trigger={null} collapsible collapsed={sidebarCollapsed} theme="dark">
          {sidebarContent}
        </Layout.Sider>
      )}
      <Layout>
        <HeaderBar />
        <Layout.Content style={{ margin: isMobile ? 8 : 16, padding: isMobile ? 12 : 24, background: darkMode ? undefined : '#fff', borderRadius: 8, minHeight: 280 }}>
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
