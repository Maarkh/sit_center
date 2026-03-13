import { Modal, Form, Input, Select, message } from 'antd';
import { createIncident } from '@/api/incidents';

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateIncidentModal({ open, onClose, onCreated }: Props) {
  const [form] = Form.useForm();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await createIncident(values);
      message.success('Incident created');
      form.resetFields();
      onClose();
      onCreated();
    } catch { /* validation error */ }
  };

  return (
    <Modal title="Create Incident" open={open} onOk={handleOk} onCancel={onClose} destroyOnClose>
      <Form form={form} layout="vertical">
        <Form.Item name="alert_message" label="Alert Message" rules={[{ required: true }]}>
          <Input.TextArea rows={2} />
        </Form.Item>
        <Form.Item name="metric" label="Metric" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="region" label="Region" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="priority" label="Priority" rules={[{ required: true }]}>
          <Select options={[
            { label: 'Critical', value: 'critical' },
            { label: 'High', value: 'high' },
            { label: 'Medium', value: 'medium' },
            { label: 'Low', value: 'low' },
          ]} />
        </Form.Item>
        <Form.Item name="description" label="Description">
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item name="assigned_to" label="Assign To">
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
}
