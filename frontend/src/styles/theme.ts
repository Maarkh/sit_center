import { theme as antTheme } from 'antd';
import type { ThemeConfig } from 'antd';

const baseToken = {
  colorPrimary: '#1677ff',
  colorError: '#ff4d4f',
  colorWarning: '#faad14',
  colorSuccess: '#52c41a',
  borderRadius: 6,
  fontSize: 14,
};

export const lightTheme: ThemeConfig = {
  token: baseToken,
};

export const darkTheme: ThemeConfig = {
  token: baseToken,
  algorithm: antTheme.darkAlgorithm,
};
