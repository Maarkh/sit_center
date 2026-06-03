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
