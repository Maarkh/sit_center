import { useState, lazy, Suspense } from 'react';
import { Tabs, Spin } from 'antd';
import {
  DashboardOutlined, ThunderboltOutlined, ProfileOutlined, AuditOutlined, ExperimentOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import CockpitOverview from './CockpitOverview';

const PredictivePanel = lazy(() => import('./PredictivePanel'));
const ProcessPanel = lazy(() => import('./ProcessPanel'));
const DecisionLogPanel = lazy(() => import('./DecisionLogPanel'));
const WhatIfPanel = lazy(() => import('./WhatIfPanel'));

const Loader = <Spin style={{ display: 'block', margin: '60px auto' }} />;

export default function CockpitPage() {
  const { t } = useTranslation();
  const [active, setActive] = useState('overview');

  const items = [
    { key: 'overview', label: <span><DashboardOutlined /> {t('cockpit.tabOverview')}</span>, children: <CockpitOverview /> },
    { key: 'predictive', label: <span><ThunderboltOutlined /> {t('cockpit.tabPredictive')}</span>,
      children: <Suspense fallback={Loader}><PredictivePanel /></Suspense> },
    { key: 'processes', label: <span><ProfileOutlined /> {t('cockpit.tabProcesses')}</span>,
      children: <Suspense fallback={Loader}><ProcessPanel /></Suspense> },
    { key: 'decisions', label: <span><AuditOutlined /> {t('cockpit.tabDecisions')}</span>,
      children: <Suspense fallback={Loader}><DecisionLogPanel /></Suspense> },
    { key: 'whatif', label: <span><ExperimentOutlined /> {t('cockpit.tabWhatIf')}</span>,
      children: <Suspense fallback={Loader}><WhatIfPanel /></Suspense> },
  ];

  // destroyInactiveTabPane so each panel re-fetches fresh data when revisited.
  return <Tabs activeKey={active} onChange={setActive} items={items} destroyOnHidden />;
}
