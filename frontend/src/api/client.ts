import axios from 'axios';
import { message } from 'antd';
import { useAuthStore } from '@/stores/authStore';

function getCookie(name: string): string | null {
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}

const client = axios.create({
  baseURL: '',
  timeout: 30000,
  // Send the httpOnly auth cookie with every request.
  withCredentials: true,
});

const UNSAFE_METHODS = ['post', 'put', 'patch', 'delete'];

client.interceptors.request.use((config) => {
  // Double-submit CSRF: echo the readable csrf_token cookie back as a header on
  // mutating requests. The httpOnly auth cookie itself is sent automatically.
  if (config.method && UNSAFE_METHODS.includes(config.method.toLowerCase())) {
    const csrf = getCookie('csrf_token');
    if (csrf) {
      config.headers['X-CSRF-Token'] = csrf;
    }
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const url: string = error.config?.url || '';
    const status = error.response?.status;
    // 401 on the auth probe (/auth/me) or a login attempt (/token) is expected and
    // is handled by the caller. Hard-redirecting on those would loop on load
    // (getMe 401 -> redirect -> reload -> getMe ...), so skip them.
    const authProbe = url.includes('/auth/me') || url.includes('/token');
    if (status === 401 && !authProbe) {
      void useAuthStore.getState().logout();
      window.location.href = '/login';
    } else if (status === 403) {
      message.error('Access denied');
    } else if (!authProbe && error.response?.data?.detail) {
      message.error(error.response.data.detail);
    }
    return Promise.reject(error);
  },
);

export default client;
