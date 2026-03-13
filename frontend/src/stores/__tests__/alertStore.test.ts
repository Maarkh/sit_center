import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { AlertRead } from '@/types/alerts';

vi.mock('@/api/alerts', () => ({
  listAlerts: vi.fn(),
}));

import { useAlertStore } from '../alertStore';
import { listAlerts } from '@/api/alerts';

function makeAlert(id: string): AlertRead {
  return {
    id,
    rule_id: null,
    ml_config_id: null,
    metric_name: 'cpu_usage',
    dimensions: {},
    value: 95,
    event_time: '2026-01-01T00:00:00Z',
    detected_at: '2026-01-01T00:00:00Z',
    status: 'firing',
    sent: false,
    fingerprint: `fp-${id}`,
    acknowledged_by: null,
    acknowledged_at: null,
    resolved_by: null,
  };
}

describe('alertStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAlertStore.setState({
      alerts: [],
      liveAlerts: [],
      loading: false,
      filters: {},
    });
  });

  it('has correct initial state', () => {
    const state = useAlertStore.getState();
    expect(state.alerts).toEqual([]);
    expect(state.liveAlerts).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.filters).toEqual({});
  });

  it('fetchAlerts sets alerts from API', async () => {
    const mockAlerts = [makeAlert('1'), makeAlert('2')];
    vi.mocked(listAlerts).mockResolvedValue(mockAlerts);

    await useAlertStore.getState().fetchAlerts();

    const state = useAlertStore.getState();
    expect(state.alerts).toEqual(mockAlerts);
    expect(state.loading).toBe(false);
    expect(listAlerts).toHaveBeenCalledWith({});
  });

  it('fetchAlerts uses provided params over stored filters', async () => {
    const mockAlerts = [makeAlert('1')];
    vi.mocked(listAlerts).mockResolvedValue(mockAlerts);
    const params = { status: 'firing' as const };

    await useAlertStore.getState().fetchAlerts(params);

    expect(listAlerts).toHaveBeenCalledWith(params);
  });

  it('fetchAlerts handles API errors gracefully', async () => {
    vi.mocked(listAlerts).mockRejectedValue(new Error('Network error'));

    await useAlertStore.getState().fetchAlerts();

    const state = useAlertStore.getState();
    expect(state.alerts).toEqual([]);
    expect(state.loading).toBe(false);
  });

  it('addLiveAlert prepends alert to liveAlerts', () => {
    const alert1 = makeAlert('1');
    const alert2 = makeAlert('2');

    useAlertStore.getState().addLiveAlert(alert1);
    expect(useAlertStore.getState().liveAlerts).toEqual([alert1]);

    useAlertStore.getState().addLiveAlert(alert2);
    expect(useAlertStore.getState().liveAlerts).toEqual([alert2, alert1]);
  });

  it('addLiveAlert limits to 100 alerts', () => {
    // Fill with 100 alerts
    for (let i = 0; i < 100; i++) {
      useAlertStore.getState().addLiveAlert(makeAlert(`old-${i}`));
    }
    expect(useAlertStore.getState().liveAlerts).toHaveLength(100);

    // Adding one more should still be 100 (oldest dropped)
    const newAlert = makeAlert('new');
    useAlertStore.getState().addLiveAlert(newAlert);

    const liveAlerts = useAlertStore.getState().liveAlerts;
    expect(liveAlerts).toHaveLength(100);
    expect(liveAlerts[0]).toEqual(newAlert);
  });

  it('clearLiveAlerts empties the list', () => {
    useAlertStore.getState().addLiveAlert(makeAlert('1'));
    useAlertStore.getState().addLiveAlert(makeAlert('2'));
    expect(useAlertStore.getState().liveAlerts).toHaveLength(2);

    useAlertStore.getState().clearLiveAlerts();
    expect(useAlertStore.getState().liveAlerts).toEqual([]);
  });

  it('setFilters updates filters', () => {
    const filters = { status: 'resolved' as const };
    useAlertStore.getState().setFilters(filters);
    expect(useAlertStore.getState().filters).toEqual(filters);
  });
});
