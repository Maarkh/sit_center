export type ChannelType = 'telegram' | 'email' | 'webhook' | 'whatsapp_twilio';

export interface NotificationChannel {
  id: string;
  name: string;
  type: ChannelType;
  config: Record<string, unknown>;
  event_types: string[];
  min_priority: string;
  enabled: boolean;
}

export interface ChannelCreate {
  name: string;
  type: ChannelType;
  config: Record<string, unknown>;
  event_types: string[];
  min_priority: string;
  enabled: boolean;
}
