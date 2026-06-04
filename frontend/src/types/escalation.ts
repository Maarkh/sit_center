export interface EscalationLevel {
  id?: string;
  level: number;
  notify_role: string;
  notify_users: string[];
  escalate_after_minutes: number;
}

export interface EscalationChain {
  id: string;
  name: string;
  is_active: boolean;
  levels: EscalationLevel[];
}

export interface EscalationChainCreate {
  name: string;
  levels: Array<{
    level: number;
    notify_role: string;
    notify_users: string[];
    escalate_after_minutes: number;
  }>;
}
