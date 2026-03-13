import { Tag, Tooltip } from 'antd';
import { ClockCircleOutlined, WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface Props {
  deadline: string | null;
  breached: boolean;
  label: string;
}

export default function SlaIndicator({ deadline, breached, label }: Props) {
  if (!deadline) return <Tag>{label}: N/A</Tag>;

  if (breached) {
    return (
      <Tooltip title={`${label} breached at ${dayjs(deadline).format('DD.MM HH:mm')}`}>
        <Tag color="red" icon={<WarningOutlined />}>{label}: BREACHED</Tag>
      </Tooltip>
    );
  }

  const remaining = dayjs(deadline).diff(dayjs(), 'minute');
  const color = remaining < 30 ? 'orange' : 'green';

  return (
    <Tooltip title={dayjs(deadline).format('DD.MM.YYYY HH:mm')}>
      <Tag color={color} icon={<ClockCircleOutlined />}>
        {label}: {remaining > 0 ? `${remaining}m left` : 'OVERDUE'}
      </Tag>
    </Tooltip>
  );
}
