import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '@/stores/authStore';

interface Props {
  children: React.ReactNode;
  permission?: string;
  requireAdmin?: boolean;
}

export default function ProtectedRoute({ children, permission, requireAdmin }: Props) {
  const { isAuthenticated, loading, hasPermission, isAdmin } = useAuthStore();
  const location = useLocation();

  // Auth state is resolved asynchronously from the cookie via checkAuth(). Show a
  // spinner until it settles, otherwise we'd bounce to /login on every reload.
  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !isAdmin()) {
    return <Navigate to="/" replace />;
  }

  if (permission && !hasPermission(permission)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
