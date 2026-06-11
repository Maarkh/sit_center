import { useEffect, useState, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { Select, Spin, Card, Result, App, Segmented, Typography, Tag, theme } from 'antd';
import { useNavigate } from 'react-router-dom';
import { getMetricNames } from '@/api/metrics';
import { getLatestMetricByRegion } from '@/api/data';
import type { RegionMetricValue } from '@/api/data';
import { listIncidents } from '@/api/incidents';
import { resolveRegionName, codeForName } from '@/utils/ruRegions';
import { useTranslation } from 'react-i18next';
import PageHelp from '@/components/Common/PageHelp';
import 'leaflet/dist/leaflet.css';

const { Text } = Typography;

// --- metric heat ramp (0..100) ---
const METRIC_COLORS = ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027'];
const METRIC_THRESHOLDS = [20, 40, 60, 80, 95];

function metricColor(value: number | undefined): string {
  if (value === undefined) return '#cccccc';
  for (let i = 0; i < METRIC_THRESHOLDS.length; i++) {
    if (value <= METRIC_THRESHOLDS[i]) return METRIC_COLORS[i];
  }
  return METRIC_COLORS[METRIC_COLORS.length - 1];
}

interface RegionIncidents { total: number; active: number; }

// "all"/"*"/"global" mean every region — these incidents tint the whole map rather
// than sitting in the off-map side list.
const GLOBAL_REGIONS = new Set(['all', '*', 'global', 'все', 'всё']);

// active incidents drive the colour; a region with only resolved ones stays pale-green.
function incidentColor(r: RegionIncidents | undefined): string {
  if (!r) return '#cccccc';
  if (r.active >= 6) return '#d73027';
  if (r.active >= 3) return '#fc8d59';
  if (r.active >= 1) return '#fee08b';
  if (r.total > 0) return '#91cf60';
  return '#cccccc';
}

function Legend({ items, bg, color }: { items: { color: string; label: string }[]; bg: string; color: string }) {
  return (
    <div style={{
      position: 'absolute', bottom: 30, right: 10, zIndex: 1000,
      background: bg, color, padding: '8px 12px', borderRadius: 6,
      fontSize: 12, lineHeight: '20px', boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
    }}>
      {items.map((it) => (
        <div key={it.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 18, height: 14, background: it.color, display: 'inline-block', borderRadius: 2 }} />
          {it.label}
        </div>
      ))}
    </div>
  );
}

const ACTIVE_STATUSES = (s: string) => !['resolved', 'closed'].includes(s);

export default function MapPage() {
  const [geoData, setGeoData] = useState<GeoJSON.FeatureCollection | null>(null);
  const [mode, setMode] = useState<'incidents' | 'metric'>('incidents');
  // metric mode
  const [metricNames, setMetricNames] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>();
  const [regionValues, setRegionValues] = useState<Map<string, number>>(new Map());
  // incident mode
  const [incidentByRegion, setIncidentByRegion] = useState<Map<string, RegionIncidents>>(new Map());
  const [globalInc, setGlobalInc] = useState<RegionIncidents>({ total: 0, active: 0 });
  const [offMap, setOffMap] = useState<{ region: string; total: number; active: number }[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const { t } = useTranslation();
  const { message } = App.useApp();
  const { token } = theme.useToken();
  const navigate = useNavigate();

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
    });
  }, [t]);

  // Incident overlay: group all incidents by region, mapping codes/names to geojson names.
  useEffect(() => {
    listIncidents({ limit: 500 })
      .then((resp) => {
        const onMap = new Map<string, RegionIncidents>();
        const off = new Map<string, RegionIncidents>();
        const glob = { total: 0, active: 0 };
        (resp.items || []).forEach((inc) => {
          const active = ACTIVE_STATUSES(inc.status) ? 1 : 0;
          if (inc.region && GLOBAL_REGIONS.has(inc.region.toLowerCase())) {
            glob.total += 1; glob.active += active; return; // applies to every region
          }
          const name = resolveRegionName(inc.region);
          const bucket = name ? onMap : off;
          const key = name ?? (inc.region || '—');
          const cur = bucket.get(key) ?? { total: 0, active: 0 };
          bucket.set(key, { total: cur.total + 1, active: cur.active + active });
        });
        setIncidentByRegion(onMap);
        setGlobalInc(glob);
        setOffMap([...off.entries()].map(([region, v]) => ({ region, ...v })).sort((a, b) => b.active - a.active));
      })
      .catch((e) => {
        console.error('Failed to load incidents for map', e);
        message.error(t('map.incidents_error', 'Failed to load incidents'));
      });
  }, [t, message]);

  useEffect(() => {
    if (!selectedMetric) return; // cleared via the Select onChange below
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

  // a region's own incidents plus the global ("all") ones that apply everywhere
  const effectiveIncidents = useCallback((name: string): RegionIncidents | undefined => {
    const base = incidentByRegion.get(name);
    if (!base && globalInc.total === 0) return undefined;
    return {
      total: (base?.total ?? 0) + globalInc.total,
      active: (base?.active ?? 0) + globalInc.active,
    };
  }, [incidentByRegion, globalInc]);

  const onEachFeature = useCallback((feature: GeoJSON.Feature, layer: L.Layer) => {
    const name = feature.properties?.name || feature.properties?.NAME || 'Unknown';
    let tooltip = name;
    if (mode === 'metric') {
      const val = regionValues.get(name.toLowerCase());
      if (val !== undefined) tooltip = `${name}: ${val.toFixed(1)}`;
    } else {
      const r = effectiveIncidents(name);
      if (r) {
        tooltip = `${name}: ${r.active} ${t('map.active', 'активных')} / ${r.total} ${t('map.total', 'всего')}`;
        if (globalInc.total > 0) tooltip += ` (${t('map.incl_global', 'вкл. общерегиональные')}: ${globalInc.active})`;
      }
      // clicking a region filters the incident list to that region (by ISO code)
      (layer as L.Path).on('click', () => {
        const code = codeForName(name);
        navigate(code ? `/incidents?region=${encodeURIComponent(code)}` : '/incidents');
      });
    }
    layer.bindTooltip(tooltip, { sticky: true });
  }, [mode, regionValues, effectiveIncidents, globalInc, t, navigate]);

  const style = useCallback((feature?: GeoJSON.Feature) => {
    const name = feature?.properties?.name || feature?.properties?.NAME || '';
    const fillColor = mode === 'metric'
      ? metricColor(regionValues.get(name.toLowerCase()))
      : incidentColor(effectiveIncidents(name));
    return { fillColor, weight: 1, opacity: 0.8, color: '#fff', fillOpacity: 0.7 };
  }, [mode, regionValues, effectiveIncidents]);

  const geoKey = useMemo(
    () => `geo-${mode}-${selectedMetric}-${regionValues.size}-${incidentByRegion.size}-${globalInc.total}-${globalInc.active}`,
    [mode, selectedMetric, regionValues, incidentByRegion, globalInc],
  );

  const legendItems = mode === 'metric'
    ? METRIC_COLORS.map((c, i) => ({ color: c, label: ['0-20', '20-40', '40-60', '60-80', '80-95', '95+'][i] }))
        .concat([{ color: '#cccccc', label: 'N/A' }])
    : [
        { color: '#d73027', label: `6+ ${t('map.active', 'активных')}` },
        { color: '#fc8d59', label: '3–5' },
        { color: '#fee08b', label: '1–2' },
        { color: '#91cf60', label: t('map.only_resolved', 'только закрытые') },
        { color: '#cccccc', label: t('map.none', 'нет') },
      ];

  if (loadError && !geoData) return <Result status="error" title={loadError} />;
  if (!geoData) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <>
      <PageHelp section="map" />
      <div style={{ height: 'calc(100vh - 200px)', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 10, left: 60, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Card size="small" styles={{ body: { padding: 8 } }}>
          <Segmented
            value={mode}
            onChange={(v) => setMode(v as 'incidents' | 'metric')}
            options={[
              { label: t('map.incidents', 'Инциденты'), value: 'incidents' },
              { label: t('map.metric', 'Метрика'), value: 'metric' },
            ]}
          />
        </Card>
        {mode === 'incidents' && globalInc.total > 0 && (
          <Card size="small" styles={{ body: { padding: 8 } }}>
            <Text strong>{t('map.all_regions', 'На все регионы')}: </Text>
            <Tag color="red">{globalInc.active}</Tag>
            <Text type="secondary">{globalInc.total}</Text>
          </Card>
        )}
        {mode === 'metric' && (
          <Card size="small" style={{ minWidth: 250 }}>
            <Select
              placeholder={t('map.select_metric')}
              options={metricNames.map((m) => ({ label: m, value: m }))}
              value={selectedMetric}
              onChange={(v) => { setSelectedMetric(v); if (!v) setRegionValues(new Map()); }}
              allowClear showSearch
              style={{ width: '100%' }}
            />
          </Card>
        )}
        {mode === 'incidents' && offMap.length > 0 && (
          <Card size="small" title={t('map.off_map', 'Регионы вне карты')} style={{ minWidth: 250, maxWidth: 280 }}
            styles={{ body: { padding: '4px 8px', maxHeight: 220, overflow: 'auto' } }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {offMap.map((it) => (
                <div key={it.region} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 0' }}>
                  <Text>{it.region}</Text>
                  <span>
                    {it.active > 0 && <Tag color="red">{it.active}</Tag>}
                    <Text type="secondary">{it.total}</Text>
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
      <Legend items={legendItems} bg={token.colorBgElevated} color={token.colorText} />
      <MapContainer center={[62, 95]} zoom={3} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        <GeoJSON key={geoKey} data={geoData} style={style} onEachFeature={onEachFeature} />
      </MapContainer>
      </div>
    </>
  );
}
