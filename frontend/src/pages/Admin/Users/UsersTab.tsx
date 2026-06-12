import { useEffect, useState } from 'react';
import PageHelp from '@/components/Common/PageHelp';
import { Table, Button, Modal, Form, Input, message, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { listUsers, createUser } from '@/api/admin';
import type { UserRead } from '@/types/admin';

export default function UsersTab() {
  const [users, setUsers] = useState<UserRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchData = async () => {
    setLoading(true);
    try { setUsers(await listUsers()); } finally { setLoading(false); }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createUser(values);
      message.success('User created');
      form.resetFields();
      setModalOpen(false);
      fetchData();
    } catch { /* validation */ }
  };

  const columns = [
    { title: 'Username', dataIndex: 'username', key: 'username' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Tenant', dataIndex: 'tenant_id', key: 'tenant_id' },
    { title: 'Provider', dataIndex: 'auth_provider', key: 'auth_provider', render: (v: string) => <Tag>{v}</Tag> },
    { title: 'Active', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? 'Yes' : 'No'}</Tag> },
  ];

  return (
    <>
      <PageHelp section="users" />
      <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)} style={{ marginBottom: 16 }}>Create User</Button>
      <Table dataSource={users} columns={columns} rowKey="id" loading={loading} />
      <Modal title="Create User" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} destroyOnClose>
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="Username" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="email" label="Email"><Input type="email" /></Form.Item>
          <Form.Item name="password" label="Password"><Input.Password /></Form.Item>
          <Form.Item name="tenant_id" label="Tenant ID"><Input placeholder="default" /></Form.Item>
        </Form>
      </Modal>
    </>
  );
}
