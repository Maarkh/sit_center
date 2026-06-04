import { useEffect, useState } from 'react';
import { Table, Button, Select, InputNumber, Space, Popconfirm, App, Alert, Card } from 'antd';
import { PlusOutlined, DeleteOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { listIndicators, listDependencies, createDependency, deleteDependency } from '@/api/dss';
import type { IndicatorRead, DependencyRead } from '@/types/dss';

export default function DependenciesTab() {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [indicators, setIndicators] = useState<IndicatorRead[]>([]);
  const [deps, setDeps] = useState<DependencyRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [src, setSrc] = useState<string | undefined>();
  const [dst, setDst] = useState<string | undefined>();
  const [weight, setWeight] = useState<number>(1);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [inds, edges] = await Promise.all([listIndicators(), listDependencies()]);
      setIndicators(inds);
      setDeps(edges);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const name = (id: string) => indicators.find((i) => i.id === id)?.name ?? id.slice(0, 8);

  const add = async () => {
    if (!src || !dst) { message.warning(t('settingsDep.pickBoth', 'Выберите оба показателя')); return; }
    if (src === dst) { message.warning(t('settingsDep.noSelf', 'Показатель не может зависеть от себя')); return; }
    try {
      await createDependency({ src_indicator_id: src, dst_indicator_id: dst, weight });
      message.success(t('settingsDep.added', 'Зависимость добавлена'));
      setSrc(undefined); setDst(undefined); setWeight(1);
      fetchData();
    } catch {
      message.error(t('settingsDep.addFailed', 'Не удалось добавить (дубликат?)'));
    }
  };

  const remove = async (id: string) => {
    await deleteDependency(id);
    message.success(t('settingsDep.deleted', 'Зависимость удалена'));
    fetchData();
  };

  const options = indicators.map((i) => ({ label: i.name, value: i.id }));

  const columns = [
    { title: t('settingsDep.source', 'Источник'), key: 'src', render: (_: unknown, r: DependencyRead) => name(r.src_indicator_id) },
    { title: '', key: 'arrow', width: 30, render: () => <ArrowRightOutlined /> },
    { title: t('settingsDep.target', 'Влияет на'), key: 'dst', render: (_: unknown, r: DependencyRead) => name(r.dst_indicator_id) },
    { title: t('settingsDep.weight', 'Вес'), dataIndex: 'weight', key: 'weight', width: 90 },
    {
      title: t('common.actions'), key: 'actions', width: 90,
      render: (_: unknown, r: DependencyRead) => (
        <Popconfirm title={t('settingsDep.deleteConfirm', 'Удалить зависимость?')} onConfirm={() => remove(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <>
      <Alert type="info" showIcon style={{ marginBottom: 16 }}
        title={t('settingsDep.title', 'Зависимости показателей')}
        description={t('settingsDep.hint',
          'Связи между показателями питают корреляцию: когда связанные показатели отклоняются одновременно, движок объединяет их в одну «Ситуацию» (общая первопричина вместо россыпи алертов). Без зависимостей блок «Ситуации» в кокпите остаётся пустым.')}
      />
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select placeholder={t('settingsDep.source', 'Источник')} options={options} value={src} onChange={setSrc}
            showSearch optionFilterProp="label" style={{ width: 220 }} />
          <ArrowRightOutlined />
          <Select placeholder={t('settingsDep.target', 'Влияет на')} options={options} value={dst} onChange={setDst}
            showSearch optionFilterProp="label" style={{ width: 220 }} />
          <InputNumber min={0.1} step={0.1} value={weight} onChange={(v) => setWeight(v ?? 1)} style={{ width: 90 }} />
          <Button type="primary" icon={<PlusOutlined />} onClick={add}>{t('settingsDep.add', 'Добавить')}</Button>
        </Space>
      </Card>
      <Table dataSource={deps} columns={columns} rowKey="id" loading={loading} size="small" />
    </>
  );
}
