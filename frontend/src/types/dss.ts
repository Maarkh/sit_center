// DSS (Decision Support) types — mirror api/schemas_dss.py.

// --- M2 Indicator & Goal Model ---
export interface FactorRead {
  id: string;
  name: string;
  weight: number;
  metrics: string[];
}

export interface IndicatorTreeNode {
  id: string;
  name: string;
  unit: string;
  target_low: number | null;
  target_high: number | null;
  direction: string;
  is_active: boolean;
  factors: FactorRead[];
}

export interface GoalTreeNode {
  id: string;
  name: string;
  owner_role: string | null;
  is_active: boolean;
  indicators: IndicatorTreeNode[];
}

export interface IndicatorTreeResponse {
  goals: GoalTreeNode[];
  unassigned: IndicatorTreeNode[];
}

// --- M3 Deviation & Chronicle ---
export interface DeviationRead {
  id: string;
  indicator_id: string;
  dimensions: Record<string, unknown>;
  direction: string;
  value: number | null;
  target_low: number | null;
  target_high: number | null;
  severity: string;
  status: string;
  periods: number;
  fingerprint: string;
  detected_at: string;
  last_seen: string;
  resolved_at: string | null;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
}

// --- M4 Situation & Correlation ---
export interface SituationListItem {
  id: string;
  title: string;
  root_cause_indicator_id: string | null;
  impact_score: number;
  status: string;
  deviation_count: number;
  opened_at: string;
  closed_at: string | null;
}

export interface SituationRead {
  id: string;
  title: string;
  root_cause_indicator_id: string | null;
  root_cause_hypothesis: string | null;
  impact_score: number;
  status: string;
  deviation_count: number;
  opened_at: string;
  updated_at: string;
  closed_at: string | null;
  deviations: DeviationRead[];
}

export type SituationStatus = 'open' | 'investigating' | 'resolved' | 'closed';

// --- M7 Knowledge & Recommendation ---
export interface RecommendationRead {
  id: string;
  deviation_id: string | null;
  incident_id: number | null;
  playbook_id: string | null;
  playbook_name: string | null;
  rank: number;
  score: number;
  confidence: number;
  rationale: string | null;
  status: string;
  process_instance_id: string | null;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
}

// --- M5 Predictive ---
export interface PredictiveAlertRead {
  id: string;
  indicator_id: string;
  direction: string;
  projected_value: number | null;
  target_low: number | null;
  target_high: number | null;
  breach_eta: string | null;
  horizon_hours: number;
  confidence: string;
  status: string;
  fingerprint: string;
  created_at: string;
  last_seen: string;
  resolved_at: string | null;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
}

// Traffic-light status for an indicator in the cockpit tree.
export type IndicatorLight = 'breach' | 'predict' | 'ok' | 'idle';

// --- M8 Process / Workflow ---
export interface ChecklistItemState {
  item: string;
  done: boolean;
}

export interface StepAssignmentRead {
  id: string;
  instance_id: string;
  step_id: string | null;
  step_order: number;
  step_type: string;
  name: string;
  assignee_role: string | null;
  assignee: string | null;
  checklist_state: ChecklistItemState[];
  status: string;
  report: string | null;
  due_at: string | null;
  escalated: boolean;
  started_at: string | null;
  activated_at: string | null;
  completed_at: string | null;
  completed_by: string | null;
}

export interface ProcessInstanceRead {
  id: string;
  template_id: string;
  incident_id: number | null;
  deviation_id: string | null;
  title: string | null;
  status: string;
  started_by: string | null;
  started_at: string;
  completed_at: string | null;
  assignments: StepAssignmentRead[];
}

export interface ProcessInstanceListItem {
  id: string;
  template_id: string;
  title: string | null;
  status: string;
  incident_id: number | null;
  deviation_id: string | null;
  started_at: string;
  completed_at: string | null;
}

// --- M5 Forecast snapshot ---
export interface ForecastPointDSS {
  ts: string;
  yhat: number;
  yhat_low: number | null;
  yhat_high: number | null;
}

export interface ForecastRead {
  id: string;
  indicator_id: string;
  metric_name: string;
  horizon_hours: number;
  model_version: string | null;
  generated_at: string;
  points: ForecastPointDSS[];
}

// --- M10 Decision log ---
export interface DecisionLogItem {
  recommendation_id: string;
  playbook_id: string | null;
  playbook_name: string | null;
  deviation_id: string | null;
  incident_id: number | null;
  process_instance_id: string | null;
  score: number;
  confidence: number;
  decided_by: string | null;
  decided_at: string | null;
  resolved: boolean | null;
  effect_value: number | null;
  outcome_auto: boolean | null;
  evaluated_at: string | null;
}

export interface PlaybookStats {
  playbook_id: string;
  accepted: number;
  decided: number;
  resolved: number;
  win_rate: number | null;
}

export interface PlaybookListItem {
  id: string;
  name: string;
  trigger_severity: string | null;
  trigger_direction: string | null;
  effect_score: number;
  process_template_id: string | null;
  is_active: boolean;
}

// --- M6 Scenarios (what-if) ---
export type AssumptionMode = 'target' | 'delta' | 'delta_pct';

export interface Assumption {
  indicator_id: string;
  mode: AssumptionMode;
  value: number;
}

export interface ScenarioResultItem {
  indicator_id: string;
  indicator_name: string | null;
  baseline: number | null;
  projected: number | null;
  baseline_breach: string | null;
  projected_breach: string | null;
  improved: boolean;
  worsened: boolean;
}

export interface ScenarioResultRead {
  id: string;
  scenario_id: string;
  results: ScenarioResultItem[];
  potential_value: number;
  breaches_avoided: number;
  computed_at: string;
}

export interface ScenarioRead {
  id: string;
  name: string;
  description: string | null;
  situation_id: string | null;
  assumptions: Assumption[];
  created_by: string | null;
  created_at: string;
  updated_at: string;
  latest_result: ScenarioResultRead | null;
}

export interface ScenarioListItem {
  id: string;
  name: string;
  situation_id: string | null;
  created_at: string;
  potential_value: number | null;
  breaches_avoided: number | null;
}

// --- M2 management (Settings forms) ---
export interface GoalRead {
  id: string;
  name: string;
  description: string | null;
  owner_role: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FactorCreate {
  name: string;
  weight: number;
  metrics: string[];
}

export interface IndicatorRead {
  id: string;
  goal_id: string | null;
  name: string;
  description: string | null;
  unit: string;
  target_low: number | null;
  target_high: number | null;
  corridor_type: string;
  baseline_model_ref: string | null;
  direction: string;
  chronicle_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  factors: FactorRead[];
}

export interface IndicatorCreate {
  name: string;
  description?: string;
  unit?: string;
  goal_id?: string | null;
  target_low?: number | null;
  target_high?: number | null;
  corridor_type?: string;
  direction?: string;
  chronicle_threshold?: number;
  is_active?: boolean;
  factors?: FactorCreate[];
}

// --- M7 management (Settings forms) ---
export interface PlaybookActionRead {
  id: string;
  action_order: number;
  action: string;
  checklist: string[];
}

export interface PlaybookRead {
  id: string;
  name: string;
  description: string | null;
  trigger_severity: string | null;
  trigger_direction: string | null;
  effect_score: number;
  process_template_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  indicator_ids: string[];
  actions: PlaybookActionRead[];
}

export interface PlaybookCreate {
  name: string;
  description?: string;
  trigger_severity?: string | null;
  trigger_direction?: string | null;
  effect_score?: number;
  process_template_id?: string | null;
  indicator_ids?: string[];
  actions?: { action: string; checklist: string[] }[];
}

export interface ProcessTemplateListItem {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  step_count: number;
  created_at: string;
}
