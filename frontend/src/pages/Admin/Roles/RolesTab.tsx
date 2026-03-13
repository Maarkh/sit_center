import { useEffect, useState } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { listRoles, createRole } from '@/api/admin';
import { PERMISSIONS } from '@/utils/constants';
import type { RoleRead } from '@/types/admin';

export default function RolesTab() {
  const [roles, setRoles] = useState<RoleRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setRoles(await listRoles()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createRole(values);
      message.success('Role created');
      form.resetFields();
      setModalOpen(false);
      fetchData();
    } catch { /* validation */ }
  };

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Tenant', dataIndex: 'tenant_id', key: 'tenant_id' },
    { title: 'Permissions', dataIndex: 'permissions', key: 'permissions', render: (p: string[]) => p?.map((v) => <Tag key={v}>{v}</Tag>) },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
  ];

  return (
    <>
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ marginBottom: 16 }}>Create Role</Button>
      <Table dataSource={roles} columns={columns} rowKey="id" loading={loading} />
      <Modal title="Create Role" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} destroyOnClose>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="permissions" label="Permissions" rules={[{ required: true }]}>
            <Select mode="multiple" options={PERMISSIONS.map((p) => ({ label: p, value: p }))} />
          </Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
