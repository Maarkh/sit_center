# api/schemas_dss.py
"""Pydantic schemas for the DSS (Decision Support System) modules:
M2 Indicator & Goal Model, M3 Deviation & Chronicle, M8 Process/Workflow.

Kept separate from the monitoring schemas in api/schemas.py so the decision-support
surface can grow without bloating the original module.
"""
import re
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

_METRIC_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


CorridorType = Literal["static", "baseline"]
Direction = Literal["both", "below", "above"]
Channel = Literal["in_app", "telegram", "email", "webhook"]


# ======================================================================
# M2 — Goals
# ======================================================================
class GoalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    owner_role: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class GoalUpdate(GoalCreate):
    pass


class GoalRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    owner_role: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# M2 — Factors (модель влияния: фактор = набор метрик с весом)
# ======================================================================
class FactorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    weight: float = Field(1.0, gt=0)
    metrics: List[str] = Field(default_factory=list, description="metric_name из canonical_metrics")

    @field_validator("metrics")
    @classmethod
    def _validate_metric_names(cls, v: List[str]) -> List[str]:
        for name in v:
            if not _METRIC_NAME_RE.match(name):
                raise ValueError(f"invalid metric name: {name!r}")
        # de-dup, preserve order
        return list(dict.fromkeys(v))


class FactorRead(BaseModel):
    id: UUID
    name: str
    weight: float
    metrics: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# M2 — Indicators (показатель + целевой коридор)
# ======================================================================
class _IndicatorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    unit: str = ""
    goal_id: Optional[UUID] = None
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    corridor_type: CorridorType = "static"
    baseline_model_ref: Optional[str] = None
    direction: Direction = "both"
    chronicle_threshold: int = Field(3, ge=1, le=100)
    is_active: bool = True

    @model_validator(mode="after")
    def _check_corridor(self):
        if self.target_low is not None and self.target_high is not None:
            if self.target_low > self.target_high:
                raise ValueError("target_low must be <= target_high")
        # A static corridor that can never be breached is almost always a mistake.
        if self.corridor_type == "static" and self.target_low is None and self.target_high is None:
            raise ValueError("static corridor needs at least one of target_low / target_high")
        return self


class IndicatorCreate(_IndicatorBase):
    factors: List[FactorCreate] = Field(default_factory=list)


class IndicatorUpdate(_IndicatorBase):
    # Factors are managed via their own endpoints; an update of the indicator core
    # does not silently wipe them.
    pass


class IndicatorRead(BaseModel):
    id: UUID
    goal_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    unit: str = ""
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    corridor_type: str
    baseline_model_ref: Optional[str] = None
    direction: str
    chronicle_threshold: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    factors: List[FactorRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# M2 — Subscriptions
# ======================================================================
class SubscriptionCreate(BaseModel):
    subscriber_role: Optional[str] = Field(None, max_length=100)
    subscriber_user: Optional[str] = Field(None, max_length=100)
    channel: Channel = "in_app"

    @model_validator(mode="after")
    def _check_target(self):
        if not self.subscriber_role and not self.subscriber_user:
            raise ValueError("either subscriber_role or subscriber_user is required")
        return self


class SubscriptionRead(BaseModel):
    id: UUID
    indicator_id: UUID
    subscriber_role: Optional[str] = None
    subscriber_user: Optional[str] = None
    channel: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# M2 — Tree (Цель → Показатель → Фактор → Метрика) для кокпита
# ======================================================================
class IndicatorTreeNode(BaseModel):
    id: UUID
    name: str
    unit: str = ""
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    direction: str
    is_active: bool
    factors: List[FactorRead] = Field(default_factory=list)


class GoalTreeNode(BaseModel):
    id: UUID
    name: str
    owner_role: Optional[str] = None
    is_active: bool
    indicators: List[IndicatorTreeNode] = Field(default_factory=list)


class IndicatorTreeResponse(BaseModel):
    goals: List[GoalTreeNode] = Field(default_factory=list)
    # Indicators not attached to any goal.
    unassigned: List[IndicatorTreeNode] = Field(default_factory=list)


# ======================================================================
# M3 — Deviations & Chronicles
# ======================================================================
class DeviationRead(BaseModel):
    id: UUID
    indicator_id: UUID
    dimensions: dict = Field(default_factory=dict)
    direction: str
    value: Optional[float] = None
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    severity: str
    status: str
    periods: int
    fingerprint: str
    detected_at: datetime
    last_seen: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeviationAck(BaseModel):
    note: Optional[str] = Field(None, max_length=1000)


class ChronicleRead(BaseModel):
    id: UUID
    indicator_id: UUID
    fingerprint: str
    episodes: int
    total_periods: int
    max_periods: int
    first_seen: datetime
    last_seen: datetime

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# M8 — Process / Workflow Engine
# ======================================================================
StepType = Literal["sequential", "parallel"]
InstanceStatus = Literal["running", "completed", "cancelled"]
AssignmentStatus = Literal["pending", "active", "in_progress", "done", "skipped"]


class ProcessStepCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    step_order: int = Field(..., ge=0, description="одинаковый порядок = параллельные шаги")
    step_type: StepType = "sequential"
    assignee_role: Optional[str] = Field(None, max_length=100)
    checklist: List[str] = Field(default_factory=list)
    due_after_minutes: Optional[int] = Field(None, gt=0)


class ProcessStepRead(BaseModel):
    id: UUID
    step_order: int
    name: str
    step_type: str
    assignee_role: Optional[str] = None
    checklist: List[str] = Field(default_factory=list)
    due_after_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True
    steps: List[ProcessStepCreate] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _check_steps(self):
        if not self.steps:
            raise ValueError("a template needs at least one step")
        return self


class ProcessTemplateRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    steps: List[ProcessStepRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProcessTemplateListItem(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    step_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessInstanceCreate(BaseModel):
    template_id: UUID
    title: Optional[str] = Field(None, max_length=300)
    incident_id: Optional[int] = None
    deviation_id: Optional[UUID] = None


class ChecklistItemState(BaseModel):
    item: str
    done: bool = False


class StepStartRequest(BaseModel):
    assignee: Optional[str] = Field(None, max_length=100)


class ChecklistUpdateRequest(BaseModel):
    checklist_state: List[ChecklistItemState]


class StepCompleteRequest(BaseModel):
    report: Optional[str] = Field(None, max_length=5000)
    # Allow completion even if checklist items remain unchecked (with a reason in report).
    force: bool = False


class StepAssignmentRead(BaseModel):
    id: UUID
    instance_id: UUID
    step_id: Optional[UUID] = None
    step_order: int
    step_type: str
    name: str
    assignee_role: Optional[str] = None
    assignee: Optional[str] = None
    checklist_state: List[ChecklistItemState] = Field(default_factory=list)
    status: str
    report: Optional[str] = None
    due_at: Optional[datetime] = None
    escalated: bool = False
    started_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessInstanceRead(BaseModel):
    id: UUID
    template_id: UUID
    incident_id: Optional[int] = None
    deviation_id: Optional[UUID] = None
    title: Optional[str] = None
    status: str
    started_by: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    assignments: List[StepAssignmentRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProcessInstanceListItem(BaseModel):
    id: UUID
    template_id: UUID
    title: Optional[str] = None
    status: str
    incident_id: Optional[int] = None
    deviation_id: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ======================================================================
# M7 — Knowledge Base & Recommendation
# ======================================================================
TriggerSeverity = Literal["warning", "critical"]


class PlaybookActionCreate(BaseModel):
    action: str = Field(..., min_length=1, max_length=500)
    checklist: List[str] = Field(default_factory=list)


class PlaybookActionRead(BaseModel):
    id: UUID
    action_order: int
    action: str
    checklist: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PlaybookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    trigger_severity: Optional[TriggerSeverity] = None
    trigger_direction: Optional[Direction] = None
    effect_score: float = Field(1.0, ge=0)
    process_template_id: Optional[UUID] = None
    indicator_ids: List[UUID] = Field(default_factory=list, description="scope; empty = applies to all")
    actions: List[PlaybookActionCreate] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("trigger_direction")
    @classmethod
    def _no_both(cls, v):
        # 'both' is an indicator-level concept; a playbook triggers on one concrete side.
        if v == "both":
            raise ValueError("trigger_direction must be 'below' or 'above' (or omitted)")
        return v


class PlaybookUpdate(PlaybookCreate):
    pass


class PlaybookRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    trigger_severity: Optional[str] = None
    trigger_direction: Optional[str] = None
    effect_score: float
    process_template_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    indicator_ids: List[UUID] = Field(default_factory=list)
    actions: List[PlaybookActionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PlaybookListItem(BaseModel):
    id: UUID
    name: str
    trigger_severity: Optional[str] = None
    trigger_direction: Optional[str] = None
    effect_score: float
    process_template_id: Optional[UUID] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RecommendationGenerateRequest(BaseModel):
    deviation_id: Optional[UUID] = None
    incident_id: Optional[int] = None

    @model_validator(mode="after")
    def _exactly_one(self):
        if bool(self.deviation_id) == bool(self.incident_id):
            raise ValueError("provide exactly one of deviation_id / incident_id")
        return self


class RecommendationRead(BaseModel):
    id: UUID
    deviation_id: Optional[UUID] = None
    incident_id: Optional[int] = None
    playbook_id: Optional[UUID] = None
    playbook_name: Optional[str] = None
    rank: int
    score: float
    confidence: float
    rationale: Optional[str] = None
    status: str
    process_instance_id: Optional[UUID] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationDecision(BaseModel):
    note: Optional[str] = Field(None, max_length=1000)


# ======================================================================
# M5 — Forecasting & Predictive Alerts
# ======================================================================
class PredictiveAlertRead(BaseModel):
    id: UUID
    indicator_id: UUID
    direction: str
    projected_value: Optional[float] = None
    target_low: Optional[float] = None
    target_high: Optional[float] = None
    breach_eta: Optional[datetime] = None
    horizon_hours: int
    confidence: str
    status: str
    fingerprint: str
    created_at: datetime
    last_seen: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PredictiveAlertAck(BaseModel):
    note: Optional[str] = Field(None, max_length=1000)


class ForecastPointDSS(BaseModel):
    ts: datetime
    yhat: float
    yhat_low: Optional[float] = None
    yhat_high: Optional[float] = None


class ForecastRead(BaseModel):
    id: UUID
    indicator_id: UUID
    metric_name: str
    horizon_hours: int
    model_version: Optional[str] = None
    generated_at: datetime
    points: List[ForecastPointDSS] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PredictRunRequest(BaseModel):
    indicator_id: UUID
    horizon_hours: int = Field(24, ge=1, le=168)


# ======================================================================
# M4 — Situation & Correlation
# ======================================================================
class DependencyCreate(BaseModel):
    src_indicator_id: UUID
    dst_indicator_id: UUID
    weight: float = Field(1.0, gt=0)

    @model_validator(mode="after")
    def _no_self(self):
        if self.src_indicator_id == self.dst_indicator_id:
            raise ValueError("src and dst indicators must differ")
        return self


class DependencyRead(BaseModel):
    id: UUID
    src_indicator_id: UUID
    dst_indicator_id: UUID
    weight: float

    model_config = ConfigDict(from_attributes=True)


class SituationListItem(BaseModel):
    id: UUID
    title: str
    root_cause_indicator_id: Optional[UUID] = None
    impact_score: float
    status: str
    deviation_count: int
    opened_at: datetime
    closed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SituationRead(BaseModel):
    id: UUID
    title: str
    root_cause_indicator_id: Optional[UUID] = None
    root_cause_hypothesis: Optional[str] = None
    impact_score: float
    status: str
    deviation_count: int
    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    deviations: List[DeviationRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SituationStatusUpdate(BaseModel):
    status: Literal["open", "investigating", "resolved", "closed"]
    note: Optional[str] = Field(None, max_length=1000)


class CorrelateRequest(BaseModel):
    window_minutes: int = Field(30, ge=1, le=1440)


# ======================================================================
# M10 — Decision Log & Learning Loop
# ======================================================================
class OutcomeCreate(BaseModel):
    resolved: bool
    effect_value: Optional[float] = None
    note: Optional[str] = Field(None, max_length=1000)


class OutcomeRead(BaseModel):
    id: UUID
    recommendation_id: UUID
    resolved: bool
    effect_value: Optional[float] = None
    note: Optional[str] = None
    auto: bool
    evaluated_by: Optional[str] = None
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionLogItem(BaseModel):
    """A decision = an accepted recommendation, with its context and outcome."""
    recommendation_id: UUID
    playbook_id: Optional[UUID] = None
    playbook_name: Optional[str] = None
    deviation_id: Optional[UUID] = None
    incident_id: Optional[int] = None
    process_instance_id: Optional[UUID] = None
    score: float
    confidence: float
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    # Outcome (null until evaluated).
    resolved: Optional[bool] = None
    effect_value: Optional[float] = None
    outcome_auto: Optional[bool] = None
    evaluated_at: Optional[datetime] = None


class PlaybookStats(BaseModel):
    playbook_id: UUID
    accepted: int        # accepted decisions
    decided: int         # decisions with a recorded outcome
    resolved: int        # outcomes that resolved the situation
    win_rate: Optional[float] = None   # resolved / decided (null if no outcomes yet)


# ======================================================================
# M6 — Model & Scenario (what-if)
# ======================================================================
AssumptionMode = Literal["target", "delta", "delta_pct"]


class Assumption(BaseModel):
    indicator_id: UUID
    mode: AssumptionMode = "target"
    value: float


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    situation_id: Optional[UUID] = None
    assumptions: List[Assumption] = Field(..., min_length=1)


class ScenarioUpdate(ScenarioCreate):
    pass


class ScenarioResultItem(BaseModel):
    indicator_id: UUID
    indicator_name: Optional[str] = None
    baseline: Optional[float] = None
    projected: Optional[float] = None
    baseline_breach: Optional[str] = None
    projected_breach: Optional[str] = None
    improved: bool = False
    worsened: bool = False


class ScenarioResultRead(BaseModel):
    id: UUID
    scenario_id: UUID
    results: List[ScenarioResultItem] = Field(default_factory=list)
    potential_value: float
    breaches_avoided: int
    computed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScenarioRead(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    situation_id: Optional[UUID] = None
    assumptions: List[Assumption] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_result: Optional[ScenarioResultRead] = None

    model_config = ConfigDict(from_attributes=True)


class ScenarioListItem(BaseModel):
    id: UUID
    name: str
    situation_id: Optional[UUID] = None
    created_at: datetime
    potential_value: Optional[float] = None
    breaches_avoided: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
