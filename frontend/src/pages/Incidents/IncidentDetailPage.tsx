import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Select, Input, message, Timeline, Spin, Tag, Divider } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { getIncident, updateIncidentStatus, addComment, listComments } from '@/api/incidents';
import StatusTag from '@/components/Common/StatusTag';
import PriorityTag from '@/components/Common/PriorityTag';
import SlaIndicator from '@/components/Common/SlaIndicator';
import { formatDate } from '@/utils/formatters';
import { VALID_TRANSITIONS } from '@/types/incidents';
import type { IncidentRead, IncidentStatus, IncidentCommentRead } from '@/types/incidents';

export default function IncidentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<IncidentRead | null>(null);
  const [comments, setComments] = useState<IncidentCommentRead[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    if (!id) return;
    try {
      const [inc, cmts] = await Promise.all([
        getIncident(Number(id)),
        listComments(Number(id)),
      ]);
      setIncident(inc);
      setComments(cmts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [id]);

  const handleStatusChange = async (newStatus: IncidentStatus) => {
    if (!incident) return;
    try {
      await updateIncidentStatus(incident.id, { status: newStatus });
      message.success(`Status changed to ${newStatus}`);
      load();
    } catch { /* error handled by interceptor */ }
  };

  const handleAddComment = async () => {
    if (!incident || !newComment.trim()) return;
    try {
      await addComment(incident.id, newComment.trim());
      setNewComment('');
      const cmts = await listComments(incident.id);
      setComments(cmts);
    } catch { /* error handled by interceptor */ }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!incident) return <Card>Incident not found</Card>;

  const validNext = VALID_TRANSITIONS[incident.status as IncidentStatus] || [];

  return (
    <>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/incidents')} style={{ marginBottom: 16 }}>
        Back to Incidents
      </Button>

      <Card title={`Incident #${incident.id}`} extra={<Space><PriorityTag priority={incident.priority} /><StatusTag status={incident.status} /></Space>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
          <Descriptions.Item label="Message">{incident.alert_message}</Descriptions.Item>
          <Descriptions.Item label="Metric">{incident.metric}</Descriptions.Item>
          <Descriptions.Item label="Region">{incident.region}</Descriptions.Item>
          <Descriptions.Item label="Value">{incident.value || '-'}</Descriptions.Item>
          <Descriptions.Item label="Assigned">{incident.assigned_to || '-'}</Descriptions.Item>
          <Descriptions.Item label="Detected">{formatDate(incident.detected_at)}</Descriptions.Item>
          <Descriptions.Item label="Escalation Level">{incident.escalation_level}</Descriptions.Item>
          {incident.external_url && (
            <Descriptions.Item label="External">
              <a href={incident.external_url} target="_blank" rel="noopener noreferrer">
                {incident.external_system} #{incident.external_id}
              </a>
            </Descriptions.Item>
          )}
        </Descriptions>

        <Space style={{ marginTop: 16 }}>
          <SlaIndicator deadline={incident.response_deadline} breached={incident.response_breached} label="Response" />
          <SlaIndicator deadline={incident.resolution_deadline} breached={incident.resolution_breached} label="Resolution" />
        </Space>

        {validNext.length > 0 && (
          <>
            <Divider>Change Status</Divider>
            <Space>
              {validNext.map((s) => (
                <Button key={s} onClick={() => handleStatusChange(s)}>
                  {s.replace('_', ' ').toUpperCase()}
                </Button>
              ))}
            </Space>
          </>
        )}
      </Card>

      <Card title="Comments" style={{ marginTop: 16 }}>
        <Timeline
          items={comments.map((c) => ({
            children: (
              <div>
                <Tag>{c.author}</Tag> <small>{formatDate(c.created_at)}</small>
                <p style={{ margin: '4px 0 0' }}>{c.content}</p>
              </div>
            ),
          }))}
        />
        <Space.Compact style={{ width: '100%', marginTop: 8 }}>
          <Input
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            onPressEnter={handleAddComment}
          />
          <Button type="primary" onClick={handleAddComment}>Send</Button>
        </Space.Compact>
      </Card>
    </>
  );
}
