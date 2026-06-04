import { Tabs } from 'antd';
import RulesTab from './Rules/RulesTab';
import MLConfigsTab from './MLConfigs/MLConfigsTab';
import SlaTab from './Sla/SlaTab';
import EscalationTab from './Escalation/EscalationTab';
import NotificationsTab from './Notifications/NotificationsTab';
import DependenciesTab from './Dependencies/DependenciesTab';
import IndicatorsTab from './Indicators/IndicatorsTab';
import PlaybooksTab from './Playbooks/PlaybooksTab';
import { useTranslation } from 'react-i18next';

export default function SettingsPage() {
  const { t } = useTranslation();

  return (
    <Tabs
      items={[
        { key: 'indicators', label: t('settingsDss.indicators'), children: <IndicatorsTab /> },
        { key: 'playbooks', label: t('settingsDss.playbooks'), children: <PlaybooksTab /> },
        { key: 'rules', label: t('settings.alert_rules'), children: <RulesTab /> },
        { key: 'ml', label: t('settings.ml_configs'), children: <MLConfigsTab /> },
        { key: 'sla', label: t('settings.sla_policies'), children: <SlaTab /> },
        { key: 'escalation', label: t('settingsEsc.tab', 'Эскалация'), children: <EscalationTab /> },
        { key: 'notifications', label: t('notif.tab', 'Уведомления'), children: <NotificationsTab /> },
        { key: 'dependencies', label: t('settingsDep.tab', 'Зависимости'), children: <DependenciesTab /> },
      ]}
    />
  );
}
