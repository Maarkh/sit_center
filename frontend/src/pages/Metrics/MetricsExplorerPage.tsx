import { useState, useEffect, useCallback } from 'react';
import { Select, Button, Space, Card, Empty } from 'antd';
import { getMetricNames } from '@/api/metrics';
import { getMetricSeries } from '@/api/data';
import { predict } from '@/api/forecasts';
import ForecastChart from '@/components/Charts/ForecastChart';
import { useTranslation } from 'react-i18next';
import PageHelp from '@/components/Common/PageHelp';
import type { ForecastResponse } from '@/types/forecasts';
import type { DataPoint } from '@/types/metrics';

export default function MetricsExplorerPage() {
  const [metricNames, setMetricNames] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>();
  const [historical, setHistorical] = useState<DataPoint[]>([]);
  const [loadingHist, setLoadingHist] = useState(false);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loadingFc, setLoadingFc] = useState(false);
  const { t } = useTranslation();

  // Load metric names, then auto-select the first so the page opens with data, not empty.
  useEffect(() => {
    getMetricNames().then((names) => {
      setMetricNames(names);
      setSelectedMetric((cur) => cur ?? names[0]);
    }).catch((e) => console.error('Failed to load metric names', e));
  }, []);

  // Whenever the selected metric changes, auto-load its last-24h series.
  useEffect(() => {
    if (!selectedMetric) return;
    setForecast(null);
    setLoadingHist(true);
    getMetricSeries(selectedMetric, 24)
      .then(setHistorical)
      .catch(() => setHistorical([]))
      .finally(() => setLoadingHist(false));
  }, [selectedMetric]);

  const handleForecast = useCallback(async () => {
    if (!selectedMetric) return;
    setLoadingFc(true);
    try {
      setForecast(await predict(selectedMetric, 24));
    } catch {
      setForecast(null);
    } finally {
      setLoadingFc(false);
    }
  }, [selectedMetric]);

  const hasData = historical.length > 0 || !!forecast;

  return (
    <>
      <PageHelp section="metrics" />
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
          <Button onClick={handleForecast} loading={loadingFc} disabled={!selectedMetric}>
            {t('metrics.forecast')}
          </Button>
        </Space>
      </Card>

      <div style={{ marginTop: 16 }}>
        <Card
          loading={loadingHist}
          title={selectedMetric ? `${selectedMetric} — ${t('metrics.last24h', 'последние 24 ч')}` : t('metrics.select_metric')}
        >
          {hasData ? (
            <ForecastChart historical={historical} forecast={forecast?.points ?? []} height={500} />
          ) : (
            <Empty description={t('metrics.empty')} />
          )}
        </Card>
      </div>
    </>
  );
}
