import { Tabs } from 'antd';
import RulesTab from './Rules/RulesTab';
import MLConfigsTab from './MLConfigs/MLConfigsTab';
import SlaTab from './Sla/SlaTab';
import { useTranslation } from 'react-i18next';

export default function SettingsPage() {
  const { t } = useTranslation();

  return (
    <Tabs
      items={[
        { key: 'rules', label: t('settings.alert_rules'), children: <RulesTab /> },
        { key: 'ml', label: t('settings.ml_configs'), children: <MLConfigsTab /> },
        { key: 'sla', label: t('settings.sla_policies'), children: <SlaTab /> },
      ]}
    />
  );
}
