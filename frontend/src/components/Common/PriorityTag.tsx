import { Tag } from 'antd';
import { PRIORITY_COLORS } from '@/utils/constants';

interface Props {
  priority: string;
}

export default function PriorityTag({ priority }: Props) {
  return (
    <Tag color={PRIORITY_COLORS[priority] || 'default'}>
      {priority.toUpperCase()}
    </Tag>
  );
}
