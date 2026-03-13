import { Tabs } from 'antd';
import RulesTab from './Rules/RulesTab';
import MLConfigsTab from './MLConfigs/MLConfigsTab';
import SlaTab from './Sla/SlaTab';

export default function SettingsPage() {
  return (
    <Tabs
      items={[
        { key: 'rules', label: 'Alert Rules', children: <RulesTab /> },
        { key: 'ml', label: 'ML Configs', children: <MLConfigsTab /> },
        { key: 'sla', label: 'SLA Policies', children: <SlaTab /> },
      ]}
    />
  );
}
