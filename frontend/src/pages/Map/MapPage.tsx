import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import { Select, Spin, Card } from 'antd';
import { getMetricNames } from '@/api/metrics';
import 'leaflet/dist/leaflet.css';

export default function MapPage() {
  const [geoData, setGeoData] = useState<GeoJSON.FeatureCollection | null>(null);
  const [metricNames, setMetricNames] = useState<string[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>();

  useEffect(() => {
    fetch('/russia.geojson')
      .then((r) => r.json())
      .then(setGeoData)
      .catch(() => {});

    getMetricNames().then(setMetricNames).catch(() => {});
  }, []);

  const getColor = (value: number) => {
    if (value > 80) return '#ff4d4f';
    if (value > 60) return '#faad14';
    if (value > 40) return '#52c41a';
    return '#1677ff';
  };

  const onEachFeature = (feature: GeoJSON.Feature, layer: L.Layer) => {
    const name = feature.properties?.name || feature.properties?.NAME || 'Unknown';
    layer.bindTooltip(name, { sticky: true });
  };

  const style = () => ({
    fillColor: '#1677ff',
    weight: 1,
    opacity: 0.7,
    color: '#fff',
    fillOpacity: 0.5,
  });

  if (!geoData) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <div style={{ height: 'calc(100vh - 140px)', position: 'relative' }}>
      <div style={{ position: 'absolute', top: 10, left: 60, zIndex: 1000 }}>
        <Card size="small" style={{ minWidth: 250 }}>
          <Select
            placeholder="Select metric"
            options={metricNames.map((m) => ({ label: m, value: m }))}
            value={selectedMetric}
            onChange={setSelectedMetric}
            allowClear
            showSearch
            style={{ width: '100%' }}
          />
        </Card>
      </div>
      <MapContainer center={[62, 95]} zoom={3} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap'
        />
        <GeoJSON data={geoData} style={style} onEachFeature={onEachFeature} />
      </MapContainer>
    </div>
  );
}
