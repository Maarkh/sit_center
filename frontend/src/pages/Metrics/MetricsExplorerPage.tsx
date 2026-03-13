import { useState, useEffect } from 'react';
import { Select, DatePicker, Button, Space, Card, Empty } from 'antd';
import { getMetricNames } from '@/api/metrics';
import { predict } from '@/api/forecasts';
import TimeSeriesChart from '@/components/Charts/TimeSeriesChart';
import ForecastChart from '@/components/Charts/ForecastChart';
import { useTranslation } from 'react-i18next';
import type { ForecastResponse } from '@/types/forecasts';

const { RangePicker } = DatePicker;

export default function MetricsExplorerPage() {
  const [metricNames, setMetricNames] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>();
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    getMetricNames().then(setMetricNames).catch(() => {});
  }, []);

  const handleForecast = async () => {
    if (!selectedMetric) return;
    setLoading(true);
    try {
      const result = await predict(selectedMetric, 24);
      setForecast(result);
    } catch {
      setForecast(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Card>
        <Space wrap>
          <Select
            placeholder={t('metrics.select_metric')}
            options={metricNames.map((m) => ({ label: m, value: m }))}
            value={selectedMetric}
            onChange={setSelectedMetric}
            showSearch
            style={{ width: 300 }}
          />
          <RangePicker showTime />
          <Button type="primary" onClick={handleForecast} loading={loading} disabled={!selectedMetric}>
            {t('metrics.forecast')}
          </Button>
        </Space>
      </Card>

      <div style={{ marginTop: 16 }}>
        {forecast ? (
          <Card title={`${t('metrics.forecast_title')}: ${forecast.metric_name}`}>
            <ForecastChart historical={[]} forecast={forecast.points} height={500} />
          </Card>
        ) : (
          <Card>
            <Empty description={t('metrics.empty')} />
          </Card>
        )}
      </div>
    </>
  );
}
