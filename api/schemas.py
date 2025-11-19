# api/schemas.py
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator


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

    class Config:
        from_attributes = True


# --- Dimensions ---
class DimensionCreate(BaseModel):
    dimension_key: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_\-]+$")
    description: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    is_required: bool = False

class DimensionRead(DimensionCreate):
    created_at: datetime

    class Config:
        from_attributes = True


# --- Actions (для правил) ---
class Action(BaseModel):
    type: str = Field(..., description="telegram, webhook, idoit, incident, etc.")
    config: Dict[str, Any]


# --- Rules ---
class RuleCondition(BaseModel):
    expr: str = Field(..., description="PromQL-style: metric{dim='val'} > 100")
    for_duration: str = Field("1m", alias="for", description="duration: '5m', '1h'")
    eval_interval: str = Field("1m", alias="eval", description="evaluation interval")
    
    class Config:
        populate_by_name = True
        
    # Добавить validator для формата времени
    @validator('for_duration', 'eval_interval')
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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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
    status: Literal["firing", "resolved"]
    sent: bool
    fingerprint: str

    class Config:
        from_attributes = True