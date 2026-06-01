import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp, Spin } from 'antd';
import { useEffect, lazy, Suspense } from 'react';
import { lightTheme, darkTheme } from '@/styles/theme';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import AppLayout from '@/components/Layout/AppLayout';
import ErrorBoundary from '@/components/Common/ErrorBoundary';
import '@/i18n';
import '@/styles/global.css';

const LoginPage = lazy(() => import('@/pages/Login/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/Dashboard/DashboardPage'));
const MapPage = lazy(() => import('@/pages/Map/MapPage'));
const MetricsExplorerPage = lazy(() => import('@/pages/Metrics/MetricsExplorerPage'));
const AlertsPage = lazy(() => import('@/pages/Alerts/AlertsPage'));
const IncidentsPage = lazy(() => import('@/pages/Incidents/IncidentsPage'));
const IncidentDetailPage = lazy(() => import('@/pages/Incidents/IncidentDetailPage'));
const SettingsPage = lazy(() => import('@/pages/Settings/SettingsPage'));
const AdminPage = lazy(() => import('@/pages/Admin/AdminPage'));

const PageLoader = <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

export default function App() {
  const { initFromStorage } = useAuthStore();
  const { darkMode } = useUIStore();

  useEffect(() => {
    initFromStorage();
  }, [initFromStorage]);

  return (
    <ConfigProvider theme={darkMode ? darkTheme : lightTheme}>
      <AntApp>
        <ErrorBoundary>
        <BrowserRouter>
          <Suspense fallback={PageLoader}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                <Route index element={<DashboardPage />} />
                <Route path="map" element={<MapPage />} />
                <Route path="metrics" element={<MetricsExplorerPage />} />
                <Route path="alerts" element={<AlertsPage />} />
                <Route path="incidents" element={<IncidentsPage />} />
                <Route path="incidents/:id" element={<IncidentDetailPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="admin" element={<ProtectedRoute requireAdmin><AdminPage /></ProtectedRoute>} />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
        </ErrorBoundary>
      </AntApp>
    </ConfigProvider>
  );
}
