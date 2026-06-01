import { useEffect, useState, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { Select, Spin, Card, Result, App } from 'antd';
import { getMetricNames } from '@/api/metrics';
import { getLatestMetricByRegion } from '@/api/data';
import type { RegionMetricValue } from '@/api/data';
import { useTranslation } from 'react-i18next';
import 'leaflet/dist/leaflet.css';

const COLORS = ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027'];
const THRESHOLDS = [20, 40, 60, 80, 95];

function getColor(value: number | undefined): string {
  if (value === undefined) return '#cccccc';
  for (let i = 0; i < THRESHOLDS.length; i++) {
    if (value <= THRESHOLDS[i]) return COLORS[i];
  }
  return COLORS[COLORS.length - 1];
}

function Legend() {
  const labels = ['0-20', '20-40', '40-60', '60-80', '80-95', '95+'];
  return (
    <div style={{
      position: 'absolute', bottom: 30, right: 10, zIndex: 1000,
      background: 'rgba(255,255,255,0.9)', padding: '8px 12px', borderRadius: 6,
      fontSize: 12, lineHeight: '20px', boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
    }}>
      {COLORS.map((c, i) => (
        <div key={c} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 18, height: 14, background: c, display: 'inline-block', borderRadius: 2 }} />
          {labels[i]}
        </div>
      ))}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 18, height: 14, background: '#cccccc', display: 'inline-block', borderRadius: 2 }} />
        N/A
      </div>
    </div>
  );
}

export default function MapPage() {
  const [geoData, setGeoData] = useState<GeoJSON.FeatureCollection | null>(null);
  const [metricNames, setMetricNames] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>();
  const [regionValues, setRegionValues] = useState<Map<string, number>>(new Map());
  const [loadError, setLoadError] = useState<string | null>(null);
  const { t } = useTranslation();
  const { message } = App.useApp();

  useEffect(() => {
    fetch('/russia.geojson')
      .then((r) => {
        if (!r.ok) throw new Error(`geojson HTTP ${r.status}`);
        return r.json();
      })
      .then(setGeoData)
      .catch((e) => {
        console.error('Failed to load map geometry', e);
        setLoadError(t('map.load_error', 'Failed to load map data'));
      });

    getMetricNames().then(setMetricNames).catch((e) => {
      console.error('Failed to load metric names', e);
      message.error(t('map.metrics_error', 'Failed to load metric list'));
    });
  }, [t, message]);

  useEffect(() => {
    if (!selectedMetric) {
      setRegionValues(new Map());
      return;
    }
    getLatestMetricByRegion(selectedMetric)
      .then((data: RegionMetricValue[]) => {
        const map = new Map<string, number>();
        data.forEach((r) => map.set(r.region.toLowerCase(), r.value));
        setRegionValues(map);
      })
      .catch((e) => {
        console.error('Failed to load region values', e);
        message.error(t('map.values_error', 'Failed to load metric values'));
        setRegionValues(new Map());
      });
  }, [selectedMetric, t, message]);

  const onEachFeature = useCallback((feature: GeoJSON.Feature, layer: L.Layer) => {
    const name = feature.properties?.name || feature.properties?.NAME || 'Unknown';
    const val = regionValues.get(name.toLowerCase());
    const tooltip = val !== undefined ? `${name}: ${val.toFixed(1)}` : name;
    layer.bindTooltip(tooltip, { sticky: true });
  }, [regionValues]);

  const style = useCallback((feature?: GeoJSON.Feature) => {
    const name = feature?.properties?.name || feature?.properties?.NAME || '';
    const val = regionValues.get(name.toLowerCase());
    return {
      fillColor: getColor(val),
      weight: 1,
      opacity: 0.8,
      color: '#fff',
      fillOpacity: 0.7,
    };
  }, [regionValues]);

  // Force re-render GeoJSON when data changes
  const geoKey = useMemo(() => `geo-${selectedMetric}-${regionValues.size}`, [selectedMetric, regionValues]);

  if (loadError && !geoData) {
    return <Result status="error" title={loadError} />;
  }
  if (!geoData) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div style={{ height: 'calc(100vh - 140px)', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 10, left: 60, zIndex: 1000 }}>
        <Card size="small" style={{ minWidth: 250 }}>
          <Select
            placeholder={t('map.select_metric')}
            options={metricNames.map((m) => ({ label: m, value: m }))}
            value={selectedMetric}
            onChange={setSelectedMetric}
            allowClear
            showSearch
            style={{ width: '100%' }}
          />
        </Card>
      </div>
      {selectedMetric && <Legend />}
      <MapContainer center={[62, 95]} zoom={3} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        <GeoJSON key={geoKey} data={geoData} style={style} onEachFeature={onEachFeature} />
      </MapContainer>
    </div>
  );
}
