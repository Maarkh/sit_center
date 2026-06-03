import client from './client';
import type {
  IndicatorTreeResponse, DeviationRead, SituationListItem, SituationRead,
  RecommendationRead, PredictiveAlertRead, SituationStatus, IndicatorLight,
  ProcessInstanceListItem, ProcessInstanceRead, StepAssignmentRead, ChecklistItemState,
  ForecastRead, DecisionLogItem, PlaybookStats, PlaybookListItem,
  ScenarioListItem, ScenarioRead, ScenarioResultRead, Assumption,
} from '@/types/dss';

// --- M2: indicator tree ---
export async function getIndicatorTree(): Promise<IndicatorTreeResponse> {
  const { data } = await client.get<IndicatorTreeResponse>('/api/v1/indicators/tree');
  return data;
}

// --- M3: deviations ---
export async function listDeviations(params: { active_only?: boolean; indicator_id?: string } = {}): Promise<DeviationRead[]> {
  const { data } = await client.get<DeviationRead[]>('/api/v1/deviations/', { params });
  return data;
}

// --- M4: situations ---
export async function listSituations(params: { active_only?: boolean; status?: string } = {}): Promise<SituationListItem[]> {
  const { data } = await client.get<SituationListItem[]>('/api/v1/situations/', { params });
  return data;
}

export async function getSituation(id: string): Promise<SituationRead> {
  const { data } = await client.get<SituationRead>(`/api/v1/situations/${id}`);
  return data;
}

export async function updateSituationStatus(id: string, status: SituationStatus): Promise<SituationListItem> {
  const { data } = await client.patch<SituationListItem>(`/api/v1/situations/${id}/status`, { status });
  return data;
}

export async function correlateNow(window_minutes = 30): Promise<Record<string, number>> {
  const { data } = await client.post<Record<string, number>>('/api/v1/situations/correlate', { window_minutes });
  return data;
}

// --- M5: predictive alerts ---
export async function listPredictiveAlerts(params: { active_only?: boolean } = {}): Promise<PredictiveAlertRead[]> {
  const { data } = await client.get<PredictiveAlertRead[]>('/api/v1/predictions/', { params });
  return data;
}

// --- M7: recommendations ---
export async function generateRecommendations(deviation_id: string): Promise<RecommendationRead[]> {
  const { data } = await client.post<RecommendationRead[]>('/api/v1/recommendations/generate', { deviation_id });
  return data;
}

export async function listRecommendations(params: { deviation_id?: string } = {}): Promise<RecommendationRead[]> {
  const { data } = await client.get<RecommendationRead[]>('/api/v1/recommendations', { params });
  return data;
}

export async function acceptRecommendation(id: string): Promise<RecommendationRead> {
  const { data } = await client.post<RecommendationRead>(`/api/v1/recommendations/${id}/accept`, {});
  return data;
}

export async function dismissRecommendation(id: string): Promise<RecommendationRead> {
  const { data } = await client.post<RecommendationRead>(`/api/v1/recommendations/${id}/dismiss`, {});
  return data;
}

// --- M5: forecast snapshot ---
export async function getLatestForecast(indicatorId: string): Promise<ForecastRead> {
  const { data } = await client.get<ForecastRead>(`/api/v1/predictions/forecasts/${indicatorId}/latest`);
  return data;
}

// --- M8: process instances + step actions ---
export async function listProcessInstances(params: { status?: string } = {}): Promise<ProcessInstanceListItem[]> {
  const { data } = await client.get<ProcessInstanceListItem[]>('/api/v1/processes/instances', { params });
  return data;
}

export async function getProcessInstance(id: string): Promise<ProcessInstanceRead> {
  const { data } = await client.get<ProcessInstanceRead>(`/api/v1/processes/instances/${id}`);
  return data;
}

export async function startStep(assignmentId: string, assignee?: string): Promise<StepAssignmentRead> {
  const { data } = await client.post<StepAssignmentRead>(`/api/v1/processes/assignments/${assignmentId}/start`, { assignee });
  return data;
}

export async function updateStepChecklist(assignmentId: string, checklist_state: ChecklistItemState[]): Promise<StepAssignmentRead> {
  const { data } = await client.patch<StepAssignmentRead>(`/api/v1/processes/assignments/${assignmentId}/checklist`, { checklist_state });
  return data;
}

export async function completeStep(assignmentId: string, report?: string, force = false): Promise<StepAssignmentRead> {
  const { data } = await client.post<StepAssignmentRead>(`/api/v1/processes/assignments/${assignmentId}/complete`, { report, force });
  return data;
}

// --- M10: decision log + playbook win-rate ---
export async function listDecisions(): Promise<DecisionLogItem[]> {
  const { data } = await client.get<DecisionLogItem[]>('/api/v1/recommendations/decisions');
  return data;
}

export async function recordOutcome(recommendationId: string, resolved: boolean, effect_value?: number, note?: string) {
  const { data } = await client.post(`/api/v1/recommendations/${recommendationId}/outcome`, { resolved, effect_value, note });
  return data;
}

export async function listPlaybooks(): Promise<PlaybookListItem[]> {
  const { data } = await client.get<PlaybookListItem[]>('/api/v1/playbooks');
  return data;
}

export async function getPlaybookStats(id: string): Promise<PlaybookStats> {
  const { data } = await client.get<PlaybookStats>(`/api/v1/playbooks/${id}/stats`);
  return data;
}

// --- M6: scenarios (what-if) ---
export async function listScenarios(): Promise<ScenarioListItem[]> {
  const { data } = await client.get<ScenarioListItem[]>('/api/v1/scenarios/');
  return data;
}

export async function getScenario(id: string): Promise<ScenarioRead> {
  const { data } = await client.get<ScenarioRead>(`/api/v1/scenarios/${id}`);
  return data;
}

export async function createScenario(payload: { name: string; description?: string; assumptions: Assumption[] }): Promise<ScenarioRead> {
  const { data } = await client.post<ScenarioRead>('/api/v1/scenarios/', payload);
  return data;
}

export async function runScenario(id: string): Promise<ScenarioResultRead> {
  const { data } = await client.post<ScenarioResultRead>(`/api/v1/scenarios/${id}/run`, {});
  return data;
}

export async function deleteScenario(id: string): Promise<void> {
  await client.delete(`/api/v1/scenarios/${id}`);
}

/**
 * Traffic-light status for an indicator in the cockpit tree (pure — unit-tested):
 *   breach  — has an active (open|acknowledged) deviation;
 *   predict — no breach yet, but a predictive alert projects one;
 *   ok      — active indicator with neither;
 *   idle    — inactive indicator.
 */
export function indicatorStatus(
  indicator: { id: string; is_active: boolean },
  breachingIds: Set<string>,
  predictedIds: Set<string>,
): IndicatorLight {
  if (!indicator.is_active) return 'idle';
  if (breachingIds.has(indicator.id)) return 'breach';
  if (predictedIds.has(indicator.id)) return 'predict';
  return 'ok';
}

export const LIGHT_COLOR: Record<IndicatorLight, string> = {
  breach: '#cf1322',   // red
  predict: '#d48806',  // amber
  ok: '#389e0d',       // green
  idle: '#8c8c8c',     // grey
};
