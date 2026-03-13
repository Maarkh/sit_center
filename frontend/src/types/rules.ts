export interface RuleCondition {
  expr: string;
  for_duration?: string;
  eval_interval?: string;
}

export interface Action {
  type: string;
  config: Record<string, unknown>;
}

export interface RuleRead {
  id: string;
  name: string;
  description: string;
  condition: RuleCondition;
  labels: Record<string, string>;
  actions: Action[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RuleCreate {
  name: string;
  description?: string;
  condition: RuleCondition;
  labels?: Record<string, string>;
  actions?: Action[];
  is_active?: boolean;
}
