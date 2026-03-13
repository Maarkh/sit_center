import axios from 'axios';
import { message } from 'antd';
import { useAuthStore } from '@/stores/authStore';

const client = axios.create({
  baseURL: '',
  timeout: 30000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      message.error('Access denied');
    } else if (error.response?.data?.detail) {
      message.error(error.response.data.detail);
    }
    return Promise.reject(error);
  },
);

export default client;
