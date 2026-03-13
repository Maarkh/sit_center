import { create } from 'zustand';
import i18n from '@/i18n';

interface UIState {
  sidebarCollapsed: boolean;
  darkMode: boolean;
  language: string;
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
  setLanguage: (lang: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  darkMode: localStorage.getItem('darkMode') === 'true',
  language: localStorage.getItem('language') || 'ru',
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  toggleDarkMode: () =>
    set((s) => {
      const next = !s.darkMode;
      localStorage.setItem('darkMode', String(next));
      return { darkMode: next };
    }),
  setLanguage: (lang: string) => {
    localStorage.setItem('language', lang);
    i18n.changeLanguage(lang);
    set({ language: lang });
  },
}));
