import { useState } from 'react';
import { Alert, Button } from 'antd';
import { QuestionCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

/**
 * Короткая подсказка вверху страницы: «что это и что тут делать».
 * Закрывается (запоминается в localStorage по section), возвращается кнопкой «?».
 * Текст берётся из i18n: help.<section>.title / help.<section>.body.
 */
export default function PageHelp({ section }: { section: string }) {
  const { t } = useTranslation();
  const storageKey = `pagehelp:${section}`;
  const [closed, setClosed] = useState<boolean>(() => {
    try { return localStorage.getItem(storageKey) === '1'; } catch { return false; }
  });

  const reopen = () => {
    try { localStorage.removeItem(storageKey); } catch { /* ignore */ }
    setClosed(false);
  };
  const dismiss = () => {
    try { localStorage.setItem(storageKey, '1'); } catch { /* ignore */ }
    setClosed(true);
  };

  if (closed) {
    return (
      <Button type="link" size="small" icon={<QuestionCircleOutlined />} onClick={reopen}
        style={{ paddingLeft: 0, marginBottom: 8 }}>
        {t('help.show')}
      </Button>
    );
  }

  return (
    <Alert
      type="info"
      showIcon
      closable
      onClose={dismiss}
      message={t(`help.${section}.title`)}
      description={<span style={{ whiteSpace: 'pre-line' }}>{t(`help.${section}.body`)}</span>}
      style={{ marginBottom: 12 }}
    />
  );
}
