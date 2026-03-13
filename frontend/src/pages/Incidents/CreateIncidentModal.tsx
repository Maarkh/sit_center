import { Modal, Form, Input, Select, message } from 'antd';
import { createIncident } from '@/api/incidents';
import { useTranslation } from 'react-i18next';

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateIncidentModal({ open, onClose, onCreated }: Props) {
  const [form] = Form.useForm();
  const { t } = useTranslation();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await createIncident(values);
      message.success(t('incidents.create'));
      form.resetFields();
      onClose();
      onCreated();
    } catch { /* validation error */ }
  };

  return (
    <Modal title={t('incidents.create_title')} open={open} onOk={handleOk} onCancel={onClose} destroyOnClose>
      <Form form={form} layout="vertical">
        <Form.Item name="alert_message" label={t('incidents.alert_message')} rules={[{ required: true }]}>
          <Input.TextArea rows={2} />
        </Form.Item>
        <Form.Item name="metric" label={t('incidents.metric')} rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="region" label={t('incidents.region')} rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="priority" label={t('incidents.priority')} rules={[{ required: true }]}>
          <Select options={[
            { label: t('common.critical'), value: 'critical' },
            { label: t('common.high'), value: 'high' },
            { label: t('common.medium'), value: 'medium' },
            { label: t('common.low'), value: 'low' },
          ]} />
        </Form.Item>
        <Form.Item name="description" label={t('incidents.message')}>
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item name="assigned_to" label={t('incidents.assigned_to')}>
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
}
