import client from './client';
import type {
  IndicatorTreeResponse, DeviationRead, SituationListItem, SituationRead,
  RecommendationRead, PredictiveAlertRead, SituationStatus, IndicatorLight,
  ProcessInstanceListItem, ProcessInstanceRead, StepAssignmentRead, ChecklistItemState,
  ForecastRead, DecisionLogItem, PlaybookStats, PlaybookListItem,
  ScenarioListItem, ScenarioRead, ScenarioResultRead, Assumption,
  GoalRead, IndicatorRead, IndicatorCreate, PlaybookRead, PlaybookCreate, ProcessTemplateListItem,
  DependencyRead, DependencyCreate, MyTask, ProcessTemplateCreate, ProcessTemplateRead,
} from '@/types/dss';

// --- M2: indicator tree ---
export async function getIndicatorTree(): Promise<IndicatorTreeResponse> {
  const { data } = await client.get<IndicatorTreeResponse>('/api/v1/indicators/tree');
  return data;
}

// --- M3: deviations ---
export async function listDeviations(params: { active_only?: boolean; indicator_id?: string; status?: string; limit?: number } = {}): Promise<DeviationRead[]> {
  const { data } = await client.get<DeviationRead[]>('/api/v1/deviations/', { params });
  return data;
}

export async function acknowledgeDeviation(id: string): Promise<DeviationRead> {
  const { data } = await client.post<DeviationRead>(`/api/v1/deviations/${id}/acknowledge`, {});
  return data;
}

export async function resolveDeviation(id: string): Promise<DeviationRead> {
  const { data } = await client.post<DeviationRead>(`/api/v1/deviations/${id}/resolve`, {});
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

// --- M4: indicator dependency edges (feed correlation -> situations) ---
export async function listDependencies(): Promise<DependencyRead[]> {
  const { data } = await client.get<DependencyRead[]>('/api/v1/situations/dependencies');
  return data;
}

export async function createDependency(payload: DependencyCreate): Promise<DependencyRead> {
  const { data } = await client.post<DependencyRead>('/api/v1/situations/dependencies', payload);
  return data;
}

export async function deleteDependency(id: string): Promise<void> {
  await client.delete(`/api/v1/situations/dependencies/${id}`);
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

// --- M2 management: goals + indicators (Settings) ---
export async function listGoals(): Promise<GoalRead[]> {
  const { data } = await client.get<GoalRead[]>('/api/v1/indicators/goals', { params: { active_only: false } });
  return data;
}

export async function createGoal(payload: { name: string; owner_role?: string; description?: string }): Promise<GoalRead> {
  const { data } = await client.post<GoalRead>('/api/v1/indicators/goals', payload);
  return data;
}

export async function updateGoal(id: string, payload: { name: string; owner_role?: string; description?: string }): Promise<GoalRead> {
  const { data } = await client.put<GoalRead>(`/api/v1/indicators/goals/${id}`, payload);
  return data;
}

export async function deleteGoal(id: string): Promise<void> {
  await client.delete(`/api/v1/indicators/goals/${id}`);
}

export async function listIndicators(): Promise<IndicatorRead[]> {
  const { data } = await client.get<IndicatorRead[]>('/api/v1/indicators/', { params: { active_only: false } });
  return data;
}

export async function createIndicator(payload: IndicatorCreate): Promise<IndicatorRead> {
  const { data } = await client.post<IndicatorRead>('/api/v1/indicators/', payload);
  return data;
}

export async function updateIndicator(id: string, payload: IndicatorCreate): Promise<IndicatorRead> {
  const { data } = await client.put<IndicatorRead>(`/api/v1/indicators/${id}`, payload);
  return data;
}

export async function deleteIndicator(id: string): Promise<void> {
  await client.delete(`/api/v1/indicators/${id}`);
}

// --- M7 management: playbooks (Settings) ---
export async function getPlaybook(id: string): Promise<PlaybookRead> {
  const { data } = await client.get<PlaybookRead>(`/api/v1/playbooks/${id}`);
  return data;
}

export async function createPlaybook(payload: PlaybookCreate): Promise<PlaybookRead> {
  const { data } = await client.post<PlaybookRead>('/api/v1/playbooks', payload);
  return data;
}

export async function updatePlaybook(id: string, payload: PlaybookCreate): Promise<PlaybookRead> {
  const { data } = await client.put<PlaybookRead>(`/api/v1/playbooks/${id}`, payload);
  return data;
}

export async function deletePlaybook(id: string): Promise<void> {
  await client.delete(`/api/v1/playbooks/${id}`);
}

export async function listProcessTemplates(): Promise<ProcessTemplateListItem[]> {
  const { data } = await client.get<ProcessTemplateListItem[]>('/api/v1/processes/templates', { params: { active_only: false } });
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

// --- A: my task inbox ---
export async function getMyTasks(openOnly = true): Promise<MyTask[]> {
  const { data } = await client.get<MyTask[]>('/api/v1/processes/assignments/mine', { params: { open_only: openOnly } });
  return data;
}

// --- D: explicit (re)assignment ---
export async function assignStep(assignmentId: string, assignee: string): Promise<StepAssignmentRead> {
  const { data } = await client.post<StepAssignmentRead>(`/api/v1/processes/assignments/${assignmentId}/assign`, { assignee });
  return data;
}

export async function getAssignmentRoles(): Promise<string[]> {
  const { data } = await client.get<string[]>('/api/v1/processes/roles');
  return data;
}

export async function getAssignableUsers(role?: string): Promise<string[]> {
  const { data } = await client.get<string[]>('/api/v1/processes/assignable-users', { params: role ? { role } : {} });
  return data;
}

// --- C: process template authoring ---
export async function getProcessTemplate(id: string): Promise<ProcessTemplateRead> {
  const { data } = await client.get<ProcessTemplateRead>(`/api/v1/processes/templates/${id}`);
  return data;
}

export async function createProcessTemplate(payload: ProcessTemplateCreate): Promise<ProcessTemplateRead> {
  const { data } = await client.post<ProcessTemplateRead>('/api/v1/processes/templates', payload);
  return data;
}

export async function deleteProcessTemplate(id: string): Promise<void> {
  await client.delete(`/api/v1/processes/templates/${id}`);
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
