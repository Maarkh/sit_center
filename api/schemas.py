# api/schemas.py
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


# --- Metrics ---
class MetricCreate(BaseModel):
    metric_name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    unit: str = ""
    default_threshold: Optional[float] = None
    default_critical_threshold: Optional[float] = None
    is_active: bool = True

class MetricUpdate(MetricCreate):
    pass  # PUT — полная замена

class MetricRead(MetricCreate):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Push ingestion (http_push data source) ---
class MetricPointIn(BaseModel):
    metric_name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    value: float
    timestamp: Optional[datetime] = None  # defaults to NOW() on insert
    dimensions: Dict[str, str] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)

class MetricBatchIn(BaseModel):
    metrics: List[MetricPointIn] = Field(..., min_length=1, max_length=1000)


# --- Dimensions ---
class DimensionCreate(BaseModel):
    dimension_key: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$")
    description: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    is_required: bool = False

class DimensionRead(DimensionCreate):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Actions (для правил) ---
class Action(BaseModel):
    type: str = Field(..., description="telegram, webhook, idoit, incident, etc.")
    config: Dict[str, Any]


# --- Rules ---
class RuleCondition(BaseModel):
    expr: str = Field(..., description="PromQL-style: metric{dim='val'} > 100")
    for_duration: str = Field("1m", alias="for", description="duration: '5m', '1h'")
    eval_interval: str = Field("1m", alias="eval", description="evaluation interval")
    
    model_config = ConfigDict(populate_by_name=True)

    # Добавить validator для формата времени
    @field_validator('for_duration', 'eval_interval')
    @classmethod
    def validate_duration(cls, v):
        import re
        if not re.match(r'^\d+[smhd]$', v):
            raise ValueError('Duration must be in format: 1s, 5m, 1h, 1d')
        return v

class RuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    condition: RuleCondition
    labels: Dict[str, str] = Field(default_factory=dict)
    actions: List[Action] = Field(default_factory=list)
    is_active: bool = True

class RuleUpdate(RuleCreate):
    pass

class RuleRead(RuleCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- ML Configs ---
class MLConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    metric_name: str
    group_by: List[str] = Field(default_factory=list)
    methods: List[str] = Field(["prophet"])
    method_params: Dict[str, Any] = Field(default_factory=dict)
    retrain_schedule: str = "0 3 * * *"
    auto_alert: bool = True
    alert_severity: Literal["info", "warning", "critical"] = "warning"
    is_active: bool = True

class MLConfigUpdate(MLConfigCreate):
    pass

class MLConfigRead(MLConfigCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Data Query ---
class DataQueryRequest(BaseModel):
    metric_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    dimensions: Optional[Dict[str, str]] = None  # exact match: {"region": "RU-MOW"}
    dimension_in: Optional[Dict[str, List[str]]] = None  # IN: {"service": ["auth", "billing"]}
    limit: int = Field(1000, ge=1, le=10000)

class DataPoint(BaseModel):
    timestamp: datetime
    value: float
    dimensions: Dict[str, str]
    tags: Dict[str, str]

class DataQueryResponse(BaseModel):
    metric_name: str
    points: List[DataPoint]
    total: int


# --- Alerts ---
class AlertRead(BaseModel):
    id: UUID
    rule_id: Optional[UUID] = None
    ml_config_id: Optional[UUID] = None
    metric_name: str
    dimensions: Dict[str, str]
    value: float
    event_time: datetime
    detected_at: datetime
    status: Literal["firing", "acknowledged", "resolved"]
    sent: bool
    fingerprint: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Incidents ---
class IncidentCreate(BaseModel):
    alert_message: str = Field(..., min_length=1, max_length=1000)
    metric: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    value: Optional[str] = None
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    alert_event_id: Optional[UUID] = None


class IncidentStatusUpdate(BaseModel):
    status: Literal["new", "in_progress", "escalated", "resolved", "closed"]
    comment: Optional[str] = None


class IncidentAssign(BaseModel):
    assigned_to: str = Field(..., min_length=1, max_length=100)
    comment: Optional[str] = None


class IncidentCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class IncidentCommentRead(BaseModel):
    id: int
    incident_id: int
    author: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentRead(BaseModel):
    id: int
    alert_message: str
    metric: str
    region: str
    value: Optional[str] = None
    priority: str
    status: str
    detected_at: datetime
    assigned_to: Optional[str] = None
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    description: Optional[str] = None
    alert_event_id: Optional[UUID] = None
    response_deadline: Optional[datetime] = None
    resolution_deadline: Optional[datetime] = None
    response_breached: bool = False
    resolution_breached: bool = False
    escalation_level: int = 0
    last_escalated_at: Optional[datetime] = None
    external_id: Optional[str] = None
    external_system: Optional[str] = None
    external_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    items: List[IncidentRead]
    total: int


# --- SLA ---
class SlaPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    priority: Literal["critical", "high", "medium", "low"]
    response_time_minutes: int = Field(..., gt=0)
    resolution_time_minutes: int = Field(..., gt=0)
    escalation_after_minutes: int = Field(..., gt=0)


class SlaPolicyRead(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    priority: str
    response_time_minutes: int
    resolution_time_minutes: int
    escalation_after_minutes: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Forecasts ---
class ForecastPoint(BaseModel):
    timestamp: datetime
    value: float
    lower: Optional[float] = None
    upper: Optional[float] = None


class ForecastResponse(BaseModel):
    metric_name: str
    dimensions: Dict[str, str]
    horizon_hours: int
    points: List[ForecastPoint]