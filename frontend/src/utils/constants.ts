export const STATUS_COLORS: Record<string, string> = {
  firing: 'red',
  acknowledged: 'orange',
  resolved: 'green',
  new: 'blue',
  in_progress: 'orange',
  escalated: 'red',
  closed: 'default',
};

export const PRIORITY_COLORS: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'gold',
  low: 'blue',
  info: 'default',
};

export const PERMISSIONS = [
  'read:metrics', 'write:metrics',
  'read:alerts', 'write:alerts',
  'read:rules', 'write:rules',
  'read:ml', 'write:ml',
  'read:incidents', 'write:incidents',
  'read:audit',
  'read:dimensions', 'write:dimensions',
] as const;

export const ML_METHODS = ['prophet', 'lstm', 'isolation_forest', 'clustering', 'arima'] as const;

export const DATE_PRESETS = [
  { label: '1 hour', value: 1 },
  { label: '6 hours', value: 6 },
  { label: '24 hours', value: 24 },
  { label: '7 days', value: 168 },
  { label: '30 days', value: 720 },
];
