import { Drawer, Descriptions, Tag, Button, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { formatDate } from '@/utils/formatters';
import type { DeviationRead } from '@/types/dss';

const { Text } = Typography;
const SEVERITY_COLOR: Record<string, string> = { critical: 'red', warning: 'orange' };
const STATUS_COLOR: Record<string, string> = { open: 'warning', acknowledged: 'processing', resolved: 'default' };

interface Props {
  deviation: DeviationRead | null;
  indicatorName?: string;
  open: boolean;
  onClose: () => void;
}

// Shows everything that went into a single alert (DSS deviation): which indicator left
// which corridor, by how much and in which direction, for how many periods, plus the
// chronic-escalation link to a classic incident. Reused by Alerts and Dashboard.
export default function DeviationDetailDrawer({ deviation, indicatorName, open, onClose }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  if (!deviation) return null;
  const d = deviation;
  const low = d.target_low == null ? '−∞' : d.target_low;
  const high = d.target_high == null ? '+∞' : d.target_high;
  const dimKeys = Object.keys(d.dimensions || {});

  return (
    <Drawer
      title={t('deviation.title', 'Детали отклонения')}
      open={open}
      onClose={onClose}
      size="large"
    >
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label={t('cockpit.indicator')}>
          {indicatorName ?? d.indicator_id}
        </Descriptions.Item>
        <Descriptions.Item label={t('cockpit.severity')}>
          <Tag color={SEVERITY_COLOR[d.severity] ?? 'default'}>{d.severity}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label={t('alerts.status')}>
          <Tag color={STATUS_COLOR[d.status] ?? 'default'}>{d.status}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label={t('cockpit.direction')}>{d.direction}</Descriptions.Item>
        <Descriptions.Item label={t('cockpit.value')}>
          {d.value == null ? '—' : d.value.toFixed(2)}
        </Descriptions.Item>
        <Descriptions.Item label={t('deviation.corridor', 'Целевой коридор')}>
          [{low} … {high}]
        </Descriptions.Item>
        <Descriptions.Item label={t('cockpit.periods')}>{d.periods}</Descriptions.Item>
        <Descriptions.Item label={t('cockpit.detected')}>{formatDate(d.detected_at)}</Descriptions.Item>
        <Descriptions.Item label={t('deviation.lastSeen', 'Последний раз')}>{formatDate(d.last_seen)}</Descriptions.Item>
        {d.resolved_at && (
          <Descriptions.Item label={t('deviation.resolvedAt', 'Закрыто')}>{formatDate(d.resolved_at)}</Descriptions.Item>
        )}
        {d.acknowledged_by && (
          <Descriptions.Item label={t('deviation.acknowledgedBy', 'Подтвердил')}>
            {d.acknowledged_by}{d.acknowledged_at ? ` · ${formatDate(d.acknowledged_at)}` : ''}
          </Descriptions.Item>
        )}
        <Descriptions.Item label={t('deviation.dimensions', 'Измерения')}>
          {dimKeys.length ? dimKeys.map((k) => `${k}=${String(d.dimensions[k])}`).join(', ') : '—'}
        </Descriptions.Item>
        <Descriptions.Item label={t('deviation.fingerprint', 'Отпечаток')}>
          <Text code style={{ fontSize: 11 }}>{d.fingerprint}</Text>
        </Descriptions.Item>
        <Descriptions.Item label={t('cockpit.incident')}>
          {d.incident_id ? (
            <Button type="link" style={{ padding: 0 }}
              onClick={() => { onClose(); navigate(`/incidents/${d.incident_id}`); }}>
              #{d.incident_id} — {t('deviation.goToIncident', 'Перейти к инциденту')}
            </Button>
          ) : (
            <Text type="secondary">{t('deviation.noIncident', 'Инцидент не заведён')}</Text>
          )}
        </Descriptions.Item>
      </Descriptions>
    </Drawer>
  );
}
