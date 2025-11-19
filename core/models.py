# core/models.py

from sqlalchemy import Column, Integer, String, DateTime, Float, Index, func, JSON, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import enum
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass


# === Каноническая метрика (только для ORM-запросов, необязательна, но удобна) ===
class CanonicalMetric(Base):
    __tablename__ = "canonical_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    dimensions = Column(JSONB, nullable=False, default=dict)
    tags = Column(JSONB, nullable=False, default=dict)
    source = Column(String, nullable=True)

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
    status = Column(String, default="firing")  # firing, resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    fingerprint = Column(String, nullable=False, index=True)
    escalation_level = Column(Integer, default=0)
    last_escalation = Column(DateTime(timezone=True), nullable=True)
    alert_hash = Column(String, index=True)
    
    # 🔴 ДОБАВЛЕНО — критически недостающие поля:
    incident_created = Column(Boolean, default=False)
    incident_created_at = Column(DateTime(timezone=True), nullable=True)

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
    detected_at = Column(DateTime, default=datetime.utcnow)
    assigned_to = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    comments = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan")


class IncidentComment(Base):
    __tablename__ = "incident_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
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
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
class MetadataMLConfig(Base):
    __tablename__ = "metadata_ml_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    metric_name = Column(String, ForeignKey("metadata_metrics.metric_name"), nullable=False)
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