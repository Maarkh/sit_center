import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import { useEffect } from 'react';
import { theme } from '@/styles/theme';
import { useAuthStore } from '@/stores/authStore';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import AppLayout from '@/components/Layout/AppLayout';
import LoginPage from '@/pages/Login/LoginPage';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import MapPage from '@/pages/Map/MapPage';
import MetricsExplorerPage from '@/pages/Metrics/MetricsExplorerPage';
import AlertsPage from '@/pages/Alerts/AlertsPage';
import IncidentsPage from '@/pages/Incidents/IncidentsPage';
import IncidentDetailPage from '@/pages/Incidents/IncidentDetailPage';
import SettingsPage from '@/pages/Settings/SettingsPage';
import AdminPage from '@/pages/Admin/AdminPage';
import '@/styles/global.css';

export default function App() {
  const { initFromStorage } = useAuthStore();

  useEffect(() => {
    initFromStorage();
  }, [initFromStorage]);

  return (
    <ConfigProvider theme={theme}>
      <AntApp>
        <BrowserRouter>
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
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}
