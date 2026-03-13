# Sit Center Frontend

Situational center dashboard built with React 19, TypeScript, and Vite 8.

## Tech Stack

| Category           | Technology                                      |
| ------------------ | ----------------------------------------------- |
| Framework          | React 19 + TypeScript                           |
| Bundler            | Vite 8 (rolldown)                               |
| UI Components      | Ant Design 6                                    |
| Charts             | ECharts via echarts-for-react (tree-shaken, 735kB) |
| State Management   | Zustand                                         |
| Routing            | React Router 7                                  |
| Localization       | i18next (RU / EN)                               |
| PWA                | Manual Service Worker                            |

## Getting Started

```bash
npm install
npm run dev        # Dev server at http://localhost:5173
npm run build      # Production build
npm run preview    # Preview production build
```

## Environment Variables

Set these in a `.env` file or in `vite.config.ts`:

| Variable       | Description                | Default                  |
| -------------- | -------------------------- | ------------------------ |
| `VITE_API_URL` | Backend API base URL       | `http://localhost:8000`  |

## Project Structure

All pages are code-split with `React.lazy`.

```
src/
  main.tsx                              Entry point
  App.tsx                               Router setup, theme provider, lazy page imports
  i18n/                                 i18next config (RU/EN)
  styles/                               global.css, theme.ts (light/dark Ant Design tokens)

  api/                                  API client functions (auth, alerts, metrics, incidents, etc.)
  types/                                TypeScript interfaces (AlertRead, TokenData, etc.)
  utils/                                Helpers (jwt.ts — decode/expiry check)

  stores/
    authStore.ts                        Auth: login, logout, initFromStorage, hasPermission, isAdmin
                                        (JWT stored in localStorage)
    alertStore.ts                       Alerts: fetchAlerts, addLiveAlert (ring buffer, 100 max),
                                        setFilters
    uiStore.ts                          UI: sidebarCollapsed, darkMode, language
                                        (persisted to localStorage)

  hooks/
    useBreakpoint.ts                    Responsive breakpoint detection

  components/
    Auth/ProtectedRoute.tsx             Route guard (checks auth, optionally admin)
    Layout/AppLayout.tsx                Main layout: sidebar + header + content
    Layout/HeaderBar.tsx                Top bar: dark mode, language switcher, user menu
    Layout/Sidebar.tsx                  Navigation menu
    Common/ErrorBoundary.tsx            React error boundary with fallback UI
    Common/StatusTag.tsx                Colored status badges
    Common/PriorityTag.tsx              Priority badges
    Common/SlaIndicator.tsx             SLA compliance indicator
    Charts/TimeSeriesChart.tsx          ECharts time series
    Charts/GaugeChart.tsx               ECharts gauge
    Charts/ForecastChart.tsx            ECharts forecast with confidence bands

  lib/EChart.tsx                        Lazy ECharts wrapper

  pages/
    Login/LoginPage.tsx                 Login form (local + OIDC SSO button)
    Dashboard/DashboardPage.tsx         Overview: stat cards, charts, recent alerts
    Map/MapPage.tsx                     Interactive Russia map with region metrics
    Metrics/MetricsExplorerPage.tsx     Browse and chart metric data
    Alerts/AlertsPage.tsx               Alert list with filters + live WebSocket alerts
    Incidents/IncidentsPage.tsx         Incident list with SLA indicators
    Incidents/IncidentDetailPage.tsx    Incident detail: timeline, comments, actions
    Incidents/CreateIncidentModal.tsx   Create incident form
    Settings/SettingsPage.tsx           Tabs: Rules, ML Configs, SLA
    Admin/AdminPage.tsx                 Tabs: Tenants, Users, Roles, Audit
```

## WebSocket Integration

The frontend connects to `ws://<host>/ws/alerts?token=<jwt>` for live alert streaming. The JWT is passed as a query parameter and validated server-side. Incoming alerts are pushed into `alertStore.addLiveAlert`, which maintains a ring buffer capped at 100 entries.

## Error Handling

- **ErrorBoundary** wraps all pages and renders a fallback UI on uncaught errors.
- **API interceptors** catch 401 responses, trigger logout, and redirect to `/login`.
- **Network errors** surface as Ant Design notifications.

## Testing

### Unit Tests (Vitest 4 + @testing-library/react)

32 tests covering stores (authStore, alertStore, uiStore), hooks (useBreakpoint), and components.

```bash
npm run test          # or: npx vitest run
```

### E2E Tests (Playwright)

22 end-to-end tests exercising full user flows.

```bash
npx playwright test
```
