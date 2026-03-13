import { Tag } from 'antd';
import { STATUS_COLORS } from '@/utils/constants';

interface Props {
  status: string;
}

export default function StatusTag({ status }: Props) {
  return (
    <Tag color={STATUS_COLORS[status] || 'default'}>
      {status.replace('_', ' ').toUpperCase()}
    </Tag>
  );
}
