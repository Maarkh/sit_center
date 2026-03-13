import { create } from 'zustand';
import { listAlerts, type AlertFilters } from '@/api/alerts';
import type { AlertRead } from '@/types/alerts';

interface AlertState {
  alerts: AlertRead[];
  liveAlerts: AlertRead[];
  loading: boolean;
  filters: AlertFilters;
  fetchAlerts: (params?: AlertFilters) => Promise<void>;
  addLiveAlert: (alert: AlertRead) => void;
  setFilters: (filters: AlertFilters) => void;
  clearLiveAlerts: () => void;
}

export const useAlertStore = create<AlertState>((set, get) => ({
  alerts: [],
  liveAlerts: [],
  loading: false,
  filters: {},

  fetchAlerts: async (params) => {
    set({ loading: true });
    try {
      const filters = params || get().filters;
      const data = await listAlerts(filters);
      set({ alerts: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  addLiveAlert: (alert) => {
    set((state) => ({ liveAlerts: [alert, ...state.liveAlerts].slice(0, 100) }));
  },

  setFilters: (filters) => set({ filters }),
  clearLiveAlerts: () => set({ liveAlerts: [] }),
}));
