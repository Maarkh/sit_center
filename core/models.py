# core/models.py

from sqlalchemy import Column, Integer, String, DateTime, Float, Index, func, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import enum
import uuid

class Base(DeclarativeBase):
    pass


# === Каноническая метрика (только для ORM-запросов, необязательна, но удобна) ===
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String, default="local")
    external_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    roles = relationship("Role", secondary="user_roles", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    permissions = Column(JSONB, nullable=False, default=list)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    users = relationship("User", secondary="user_roles", back_populates="roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class CanonicalMetric(Base):
    __tablename__ = "canonical_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    dimensions = Column(JSONB, nullable=False, default=dict)
    tags = Column(JSONB, nullable=False, default=dict)
    source = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False, default="default")

    __table_args__ = (
        Index("ix_canonical_ts", "timestamp"),
        Index("ix_canonical_metric", "metric_name"),
        Index("ix_canonical_dims_gin", "dimensions", postgresql_using="gin"),
        Index("ix_canonical_tags_gin", "tags", postgresql_using="gin"),
    )


# === Другие модели (остаются без изменений, кроме удаления Monitoring) ===

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    column_name = Column(String, unique=True, nullable=False)  # ← legacy alias! будет устаревать
    display_name = Column(String, nullable=False)
    threshold = Column(Integer, nullable=False, default=1)
    priority = Column(Integer, nullable=False, default=1)
    weight = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_metrics_column_name", "column_name"),
        Index("ix_metrics_is_active", "is_active"),
    )


class MLAnomaly(Base):
    __tablename__ = "ml_anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ml_config_id = Column(UUID(as_uuid=True), nullable=True)  # ← связь с metadata_ml_configs
    metric_name = Column(String, nullable=False)
    dimensions = Column(JSONB, nullable=False, default=dict)  # ← вместо region
    timestamp = Column(DateTime(timezone=True), nullable=False)
    value = Column(Float, nullable=False)
    predicted = Column(Float)
    residual = Column(Float)
    confidence = Column(Float)
    method = Column(String, default="prophet")  # prophet, lstm, clustering
    model_version = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())

    def __repr__(self):
        dims = ", ".join(f"{k}={v}" for k, v in self.dimensions.items())
        return f"<MLAnomaly {self.metric_name}[{dims}]={self.value} @ {self.timestamp}>"


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), nullable=True)
    ml_config_id = Column(UUID(as_uuid=True), nullable=True)
    metric_name = Column(String, nullable=False)
    dimensions = Column(JSONB, nullable=False, default=dict)
    value = Column(Float, nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    detected_at = Column(DateTime(timezone=True), default=func.now())
    status = Column(String, default="firing")  # firing, acknowledged, resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    fingerprint = Column(String, nullable=False, index=True)
    escalation_level = Column(Integer, default=0)
    last_escalation = Column(DateTime(timezone=True), nullable=True)
    alert_hash = Column(String, index=True)
    tenant_id = Column(String, nullable=False, default="default")

    incident_created = Column(Boolean, default=False)
    incident_created_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_alerts_firing", "status", postgresql_where=(status == "firing")),
        Index("ix_alerts_fingerprint", "fingerprint"),
    )

class IncidentStatus(enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_message = Column(Text, nullable=False)
    metric = Column(String, nullable=False)
    region = Column(String, nullable=False)
    value = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    status = Column(String, default=IncidentStatus.NEW.value)
    detected_at = Column(DateTime(timezone=True), default=func.now())
    assigned_to = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    tenant_id = Column(String, nullable=False, default="default")
    description = Column(Text, nullable=True)
    alert_event_id = Column(UUID(as_uuid=True), nullable=True)
    sla_policy_id = Column(UUID(as_uuid=True), ForeignKey("sla_policies.id"), nullable=True)
    response_deadline = Column(DateTime(timezone=True), nullable=True)
    resolution_deadline = Column(DateTime(timezone=True), nullable=True)
    response_breached = Column(Boolean, default=False)
    resolution_breached = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)
    escalation_chain_id = Column(UUID(as_uuid=True), ForeignKey("escalation_chains.id"), nullable=True)
    last_escalated_at = Column(DateTime(timezone=True), nullable=True)
    external_id = Column(String, nullable=True)
    external_system = Column(String, default="idoit")
    external_url = Column(String, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    incident = relationship("Incident", back_populates="comments")


class ConfigTable(Base):
    __tablename__ = "config_tables"

    name = Column(String, primary_key=True)
    model_class = Column(String, nullable=False)
    cache_key = Column(String, nullable=False)
    ttl = Column(Integer, default=300)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    schema_name = Column(String, default="public")
    
class MetadataMetric(Base):
    __tablename__ = "metadata_metrics"

    metric_name = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    description = Column(Text)
    unit = Column(String, default="")
    default_threshold = Column(Float)
    default_critical_threshold = Column(Float)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    # В классе MetadataMetric — добавьте:
    ml_configs = relationship("MetadataMLConfig", back_populates="metric", cascade="all, delete-orphan")

class MetadataDimension(Base):
    __tablename__ = "metadata_dimensions"

    dimension_key = Column(String, primary_key=True)
    description = Column(Text)
    allowed_values = Column(JSONB)
    is_required = Column(Boolean, default=False)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())

class MetadataRule(Base):
    __tablename__ = "metadata_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    condition = Column(JSONB, nullable=False)
    labels = Column(JSONB, default=dict)
    actions = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
class MetadataMLConfig(Base):
    __tablename__ = "metadata_ml_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    metric_name = Column(String, ForeignKey("metadata_metrics.metric_name"), nullable=False)
    tenant_id = Column(String, nullable=False, default="default")
    group_by = Column(ARRAY(String), nullable=False, default=list)  # TEXT[] → ARRAY(String)
    methods = Column(ARRAY(String), nullable=False, default=lambda: ["prophet"])
    method_params = Column(JSONB, nullable=False, default=dict)
    retrain_schedule = Column(String, default="0 3 * * *")
    auto_alert = Column(Boolean, default=True)
    alert_severity = Column(String, default="warning")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Связи
    metric = relationship("MetadataMetric", back_populates="ml_configs")


class SlaPolicy(Base):
    __tablename__ = "sla_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    name = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    response_time_minutes = Column(Integer, nullable=False)
    resolution_time_minutes = Column(Integer, nullable=False)
    escalation_after_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


class EscalationChain(Base):
    __tablename__ = "escalation_chains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, default="default")
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    levels = relationship("EscalationLevel", back_populates="chain", cascade="all, delete-orphan", order_by="EscalationLevel.level")


class EscalationLevel(Base):
    __tablename__ = "escalation_levels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_id = Column(UUID(as_uuid=True), ForeignKey("escalation_chains.id", ondelete="CASCADE"), nullable=False)
    level = Column(Integer, nullable=False)
    notify_role = Column(String, nullable=False)
    notify_users = Column(JSONB, default=list)
    escalate_after_minutes = Column(Integer, nullable=False)
    chain = relationship("EscalationChain", back_populates="levels")


# ============================================================================
# DSS — M2: Indicator & Goal Model (иерархия Цель→Показатель→Фактор→Метрика)
# ============================================================================

class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    owner_role = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    indicators = relationship("Indicator", back_populates="goal")


class Indicator(Base):
    __tablename__ = "indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String, nullable=False, default="")
    target_low = Column(Float, nullable=True)
    target_high = Column(Float, nullable=True)
    corridor_type = Column(String, nullable=False, default="static")   # static | baseline
    baseline_model_ref = Column(String, nullable=True)
    direction = Column(String, nullable=False, default="both")          # both | below | above
    chronicle_threshold = Column(Integer, nullable=False, default=3)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    goal = relationship("Goal", back_populates="indicators")
    factors = relationship("Factor", back_populates="indicator", cascade="all, delete-orphan")
    subscriptions = relationship("IndicatorSubscription", back_populates="indicator", cascade="all, delete-orphan")


class Factor(Base):
    __tablename__ = "factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), default=func.now())

    indicator = relationship("Indicator", back_populates="factors")
    metrics = relationship("FactorMetric", back_populates="factor", cascade="all, delete-orphan")


class FactorMetric(Base):
    __tablename__ = "factor_metrics"

    factor_id = Column(UUID(as_uuid=True), ForeignKey("factors.id", ondelete="CASCADE"), primary_key=True)
    metric_name = Column(String, primary_key=True)

    factor = relationship("Factor", back_populates="metrics")


class IndicatorSubscription(Base):
    __tablename__ = "indicator_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    subscriber_role = Column(String, nullable=True)
    subscriber_user = Column(String, nullable=True)
    channel = Column(String, nullable=False, default="in_app")
    created_at = Column(DateTime(timezone=True), default=func.now())

    indicator = relationship("Indicator", back_populates="subscriptions")


# ============================================================================
# DSS — M3: Deviation & Chronicle
# ============================================================================

class Deviation(Base):
    __tablename__ = "deviations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    dimensions = Column(JSONB, nullable=False, default=dict)
    direction = Column(String, nullable=False)         # below | above
    value = Column(Float, nullable=True)
    target_low = Column(Float, nullable=True)
    target_high = Column(Float, nullable=True)
    severity = Column(String, nullable=False, default="warning")
    status = Column(String, nullable=False, default="open")   # open | acknowledged | resolved
    periods = Column(Integer, nullable=False, default=1)
    fingerprint = Column(String, nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=False, default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)


class Chronicle(Base):
    __tablename__ = "chronicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    fingerprint = Column(String, nullable=False)
    episodes = Column(Integer, nullable=False, default=0)
    total_periods = Column(Integer, nullable=False, default=0)
    max_periods = Column(Integer, nullable=False, default=0)
    first_seen = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=False, default=func.now())


# ============================================================================
# DSS — M8: Process / Workflow Engine
# ============================================================================

class ProcessTemplate(Base):
    __tablename__ = "process_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    steps = relationship("ProcessStep", back_populates="template",
                         cascade="all, delete-orphan", order_by="ProcessStep.step_order")


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    template_id = Column(UUID(as_uuid=True), ForeignKey("process_templates.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    step_type = Column(String, nullable=False, default="sequential")
    assignee_role = Column(String, nullable=True)
    checklist = Column(JSONB, nullable=False, default=list)
    due_after_minutes = Column(Integer, nullable=True)
    template = relationship("ProcessTemplate", back_populates="steps")


class ProcessInstance(Base):
    __tablename__ = "process_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    template_id = Column(UUID(as_uuid=True), ForeignKey("process_templates.id"), nullable=False)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    deviation_id = Column(UUID(as_uuid=True), ForeignKey("deviations.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=True)
    status = Column(String, nullable=False, default="running")   # running | completed | cancelled
    started_by = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    assignments = relationship("StepAssignment", back_populates="instance",
                               cascade="all, delete-orphan", order_by="StepAssignment.step_order")


class StepAssignment(Base):
    __tablename__ = "step_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    instance_id = Column(UUID(as_uuid=True), ForeignKey("process_instances.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(UUID(as_uuid=True), ForeignKey("process_steps.id", ondelete="SET NULL"), nullable=True)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String, nullable=False, default="sequential")
    name = Column(String, nullable=False)
    assignee_role = Column(String, nullable=True)
    assignee = Column(String, nullable=True)
    checklist_state = Column(JSONB, nullable=False, default=list)
    status = Column(String, nullable=False, default="pending")   # pending|active|in_progress|done|skipped
    report = Column(Text, nullable=True)
    due_after_minutes = Column(Integer, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    escalated = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    instance = relationship("ProcessInstance", back_populates="assignments")


# ============================================================================
# DSS — M7: Knowledge Base & Recommendation
# ============================================================================

class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    trigger_severity = Column(String, nullable=True)    # NULL | warning | critical
    trigger_direction = Column(String, nullable=True)   # NULL | below | above
    effect_score = Column(Float, nullable=False, default=1.0)
    process_template_id = Column(UUID(as_uuid=True), ForeignKey("process_templates.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    actions = relationship("PlaybookAction", back_populates="playbook",
                           cascade="all, delete-orphan", order_by="PlaybookAction.action_order")


class PlaybookAction(Base):
    __tablename__ = "playbook_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False)
    action_order = Column(Integer, nullable=False)
    action = Column(Text, nullable=False)
    checklist = Column(JSONB, nullable=False, default=list)
    playbook = relationship("Playbook", back_populates="actions")


class PlaybookIndicator(Base):
    __tablename__ = "playbook_indicators"

    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="CASCADE"), primary_key=True)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), primary_key=True)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    deviation_id = Column(UUID(as_uuid=True), ForeignKey("deviations.id", ondelete="CASCADE"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="SET NULL"), nullable=True)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    rationale = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="proposed")   # proposed | accepted | dismissed
    process_instance_id = Column(UUID(as_uuid=True), ForeignKey("process_instances.id", ondelete="SET NULL"), nullable=True)
    decided_by = Column(String, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


# ============================================================================
# DSS — M5: Forecasting & Predictive Alerts
# ============================================================================

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String, nullable=False)
    horizon_hours = Column(Integer, nullable=False)
    model_version = Column(String, nullable=True)
    points = Column(JSONB, nullable=False, default=list)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())


class PredictiveAlert(Base):
    __tablename__ = "predictive_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    direction = Column(String, nullable=False)         # below | above
    projected_value = Column(Float, nullable=True)
    target_low = Column(Float, nullable=True)
    target_high = Column(Float, nullable=True)
    breach_eta = Column(DateTime(timezone=True), nullable=True)
    horizon_hours = Column(Integer, nullable=False)
    confidence = Column(String, nullable=False, default="medium")   # medium | high
    status = Column(String, nullable=False, default="open")          # open | acknowledged | resolved
    fingerprint = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=False, default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)


# ============================================================================
# DSS — M4: Situation & Correlation
# ============================================================================

class IndicatorDependency(Base):
    __tablename__ = "indicator_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    src_indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    dst_indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), default=func.now())


class Situation(Base):
    __tablename__ = "situations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    title = Column(String, nullable=False)
    root_cause_indicator_id = Column(UUID(as_uuid=True), ForeignKey("indicators.id", ondelete="SET NULL"), nullable=True)
    root_cause_hypothesis = Column(Text, nullable=True)
    impact_score = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False, default="open")   # open | investigating | resolved | closed
    deviation_count = Column(Integer, nullable=False, default=0)
    opened_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)


class SituationDeviation(Base):
    __tablename__ = "situation_deviations"

    situation_id = Column(UUID(as_uuid=True), ForeignKey("situations.id", ondelete="CASCADE"), primary_key=True)
    deviation_id = Column(UUID(as_uuid=True), ForeignKey("deviations.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), default=func.now())


# ============================================================================
# DSS — M10: Decision Log & Learning Loop
# ============================================================================

class DecisionOutcome(Base):
    __tablename__ = "decision_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, default="default")
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, unique=True)
    resolved = Column(Boolean, nullable=False)
    effect_value = Column(Float, nullable=True)
    note = Column(Text, nullable=True)
    auto = Column(Boolean, nullable=False, default=False)
    evaluated_by = Column(String, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=func.now())