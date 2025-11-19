# core/metadata_service.py
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import uuid
import hashlib
from sqlalchemy import text, create_engine
from config import get_cache, get_database_url, logger, mask_secrets
from core.locking import global_lock


# --- Dataclasses (DTO) ---

@dataclass
class MetricDTO:
    metric_name: str
    display_name: str
    description: Optional[str] = None
    unit: str = ""
    default_threshold: Optional[float] = None
    default_critical_threshold: Optional[float] = None
    is_active: bool = True

@dataclass
class DimensionDTO:
    dimension_key: str
    description: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    is_required: bool = False

@dataclass
class ActionDTO:
    action_type: str
    config: Dict[str, Any]
    is_active: bool = True
    id: Optional[int] = None

@dataclass
class RuleDTO:
    name: str
    condition: Dict[str, Any]  # { "expr": "...", "for": "5m", "eval": "1m" }
    labels: Dict[str, str]
    actions: List[Dict[str, Any]]
    description: Optional[str] = None
    is_active: bool = True
    id: Optional[uuid.UUID] = None

@dataclass
class MLConfigDTO:
    name: str
    metric_name: str
    group_by: List[str]
    methods: List[str]
    method_params: Dict[str, Any]
    retrain_schedule: str = "0 3 * * *"
    auto_alert: bool = True
    alert_severity: str = "warning"
    is_active: bool = True
    id: Optional[uuid.UUID] = None


# --- Сервис ---

class MetadataService:
    def __init__(self):
        self._engine = None
        self._cache = get_cache()
        self._logger = logger.getChild("metadata_service")

    def _get_engine(self):
        if self._engine is None:
            self._engine = create_engine(get_database_url(), pool_pre_ping=True)
        return self._engine

    # --- Общие утилиты ---
    def _serialize_json(self, data: Any) -> str:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    def _deserialize_json(self, raw: Optional[str]) -> Any:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return raw

    def _invalidate_cache(self, prefix: str):
        """Очистка кэша по префиксу (простая реализация)"""
        # В production — использовать SCAN + DEL или Redis key prefix
        self._logger.debug(f"Кэш-инвалидация по префиксу: {prefix}")

    # --- CRUD: Metrics ---

    def create_metric(self, dto: MetricDTO) -> str:
        with global_lock("metadata_metric_create", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_metrics (
                        metric_name, display_name, description, unit,
                        default_threshold, default_critical_threshold, is_active
                    ) VALUES (
                        :metric_name, :display_name, :description, :unit,
                        :default_threshold, :default_critical_threshold, :is_active
                    )
                    ON CONFLICT (metric_name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        unit = EXCLUDED.unit,
                        default_threshold = EXCLUDED.default_threshold,
                        default_critical_threshold = EXCLUDED.default_critical_threshold,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING metric_name;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, asdict(dto))
                    metric_name = result.scalar_one()
                    self._invalidate_cache("metrics")
                    self._logger.info(f"✅ Метрика '{metric_name}' создана/обновлена")
                    return metric_name
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания метрики {dto.metric_name}: {mask_secrets(str(e))}")
                raise

    def get_metric(self, metric_name: str) -> Optional[MetricDTO]:
        key = f"metadata:metric:{metric_name}"
        cached = self._cache.get(key)
        if cached:
            return MetricDTO(**json.loads(cached)) # type: ignore

        try:
            engine = self._get_engine()
            query = text("SELECT * FROM metadata_metrics WHERE metric_name = :name AND is_active = true")
            with engine.connect() as conn:
                row = conn.execute(query, {"name": metric_name}).mappings().first()
                if not row:
                    return None
                dto = MetricDTO(**row)
                self._cache.setex(key, 300, self._serialize_json(asdict(dto)))
                return dto
        except Exception as e:
            self._logger.error(f"❌ Ошибка чтения метрики {metric_name}: {mask_secrets(str(e))}")
            return None

    def list_metrics(self, active_only: bool = True) -> List[MetricDTO]:
        key = "metadata:metrics:active" if active_only else "metadata:metrics:all"
        cached = self._cache.get(key)
        if cached:
            return [MetricDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            where = "WHERE is_active = true" if active_only else ""
            query = text(f"SELECT * FROM metadata_metrics {where} ORDER BY metric_name")
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = [MetricDTO(**row) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка метрик: {mask_secrets(str(e))}")
            return []

    # --- CRUD: Dimensions ---

    def create_dimension(self, dto: DimensionDTO) -> str:
        with global_lock("metadata_dimension_create", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_dimensions (
                        dimension_key, description, allowed_values, is_required
                    ) VALUES (
                        :dimension_key, :description, :allowed_values, :is_required
                    )
                    ON CONFLICT (dimension_key) DO UPDATE SET
                        description = EXCLUDED.description,
                        allowed_values = EXCLUDED.allowed_values,
                        is_required = EXCLUDED.is_required,
                        created_at = NOW()
                    RETURNING dimension_key;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, {
                        "dimension_key": dto.dimension_key,
                        "description": dto.description,
                        "allowed_values": self._serialize_json(dto.allowed_values),
                        "is_required": dto.is_required
                    })
                    dim_key = result.scalar_one()
                    self._invalidate_cache("dimensions")
                    self._logger.info(f"✅ Измерение '{dim_key}' создано/обновлено")
                    return dim_key
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания измерения {dto.dimension_key}: {mask_secrets(str(e))}")
                raise

    def get_dimension(self, dimension_key: str) -> Optional[DimensionDTO]:
        key = f"metadim:{dimension_key}"
        cached = self._cache.get(key)
        if cached:
            return DimensionDTO(**json.loads(cached)) # type: ignore

        try:
            engine = self._get_engine()
            query = text("SELECT * FROM metadata_dimensions WHERE dimension_key = :key")
            with engine.connect() as conn:
                row = conn.execute(query, {"key": dimension_key}).mappings().first()
                if not row:
                    return None
                dto = DimensionDTO(**row)
                self._cache.setex(key, 300, self._serialize_json(asdict(dto)))
                return dto
        except Exception as e:
            self._logger.error(f"❌ Ошибка чтения измерения {dimension_key}: {mask_secrets(str(e))}")
            return None

    def list_dimensions(self) -> List[DimensionDTO]:
        key = "metadimensions:all"
        cached = self._cache.get(key)
        if cached:
            return [DimensionDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("SELECT * FROM metadata_dimensions ORDER BY dimension_key")
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = [DimensionDTO(**row) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка измерений: {mask_secrets(str(e))}")
            return []

    # --- CRUD: Rules ---

    def create_rule(self, dto: RuleDTO) -> uuid.UUID:
        rule_id = dto.id or uuid.uuid4()
        with global_lock(f"metadata_rule_{rule_id}", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_rules (
                        id, name, description, condition, labels, actions, is_active
                    ) VALUES (
                        :id, :name, :description, :condition, :labels, :actions, :is_active
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        condition = EXCLUDED.condition,
                        labels = EXCLUDED.labels,
                        actions = EXCLUDED.actions,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING id;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, {
                        "id": rule_id,
                        "name": dto.name,
                        "description": dto.description,
                        "condition": self._serialize_json(dto.condition),
                        "labels": self._serialize_json(dto.labels),
                        "actions": self._serialize_json(dto.actions),
                        "is_active": dto.is_active
                    })
                    created_id = result.scalar_one()
                    self._invalidate_cache("rules")
                    self._logger.info(f"✅ Правило '{dto.name}' (id={created_id}) создано/обновлено")
                    return created_id
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания правила {dto.name}: {mask_secrets(str(e))}")
                raise

    def list_active_rules(self) -> List[RuleDTO]:
        key = "metadata:rules:active"
        cached = self._cache.get(key)
        if cached:
            return [RuleDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, description, condition, labels, actions, is_active
                FROM metadata_rules
                WHERE is_active = true
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = []
                for row in rows:
                    dto = RuleDTO(
                        id=row["id"],
                        name=row["name"],
                        description=row["description"],
                        condition=self._deserialize_json(row["condition"]),
                        labels=self._deserialize_json(row["labels"]),
                        actions=self._deserialize_json(row["actions"]),
                        is_active=row["is_active"]
                    )
                    dtos.append(dto)
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка правил: {mask_secrets(str(e))}")
            return []

    # --- CRUD: ML Configs ---

    def create_ml_config(self, dto: MLConfigDTO) -> uuid.UUID:
        config_id = dto.id or uuid.uuid4()
        with global_lock(f"metadata_ml_{config_id}", timeout=10):
            try:
                engine = self._get_engine()
                query = text("""
                    INSERT INTO metadata_ml_configs (
                        id, name, metric_name, group_by, methods, method_params,
                        retrain_schedule, auto_alert, alert_severity, is_active
                    ) VALUES (
                        :id, :name, :metric_name, :group_by, :methods, :method_params,
                        :retrain_schedule, :auto_alert, :alert_severity, :is_active
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        metric_name = EXCLUDED.metric_name,
                        group_by = EXCLUDED.group_by,
                        methods = EXCLUDED.methods,
                        method_params = EXCLUDED.method_params,
                        retrain_schedule = EXCLUDED.retrain_schedule,
                        auto_alert = EXCLUDED.auto_alert,
                        alert_severity = EXCLUDED.alert_severity,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                    RETURNING id;
                """)
                with engine.begin() as conn:
                    result = conn.execute(query, {
                        "id": config_id,
                        "name": dto.name,
                        "metric_name": dto.metric_name,
                        "group_by": dto.group_by,
                        "methods": dto.methods,
                        "method_params": self._serialize_json(dto.method_params),
                        "retrain_schedule": dto.retrain_schedule,
                        "auto_alert": dto.auto_alert,
                        "alert_severity": dto.alert_severity,
                        "is_active": dto.is_active
                    })
                    created_id = result.scalar_one()
                    self._invalidate_cache("ml_configs")
                    self._logger.info(f"✅ ML-конфиг '{dto.name}' (id={created_id}) создан/обновлён")
                    return created_id
            except Exception as e:
                self._logger.error(f"❌ Ошибка создания ML-конфига {dto.name}: {mask_secrets(str(e))}")
                raise

    def list_active_ml_configs(self) -> List[MLConfigDTO]:
        key = "metadata:ml_configs:active"
        cached = self._cache.get(key)
        if cached:
            return [MLConfigDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, metric_name, group_by, methods, method_params,
                       retrain_schedule, auto_alert, alert_severity, is_active
                FROM metadata_ml_configs
                WHERE is_active = true
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = []
                for row in rows:
                    dto = MLConfigDTO(
                        id=row["id"],
                        name=row["name"],
                        metric_name=row["metric_name"],
                        group_by=row["group_by"],
                        methods=row["methods"],
                        method_params=self._deserialize_json(row["method_params"]),
                        retrain_schedule=row["retrain_schedule"],
                        auto_alert=row["auto_alert"],
                        alert_severity=row["alert_severity"],
                        is_active=row["is_active"]
                    )
                    dtos.append(dto)
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка ML-конфигов: {mask_secrets(str(e))}")
            return []

    def list_all_ml_configs(self) -> List[MLConfigDTO]:
        # Аналогично list_active, но без WHERE is_active = true
        key = "metaml_configs:all"
        cached = self._cache.get(key)
        if cached:
            return [MLConfigDTO(**item) for item in json.loads(cached)] # type: ignore

        try:
            engine = self._get_engine()
            query = text("""
                SELECT id, name, metric_name, group_by, methods, method_params,
                    retrain_schedule, auto_alert, alert_severity, is_active
                FROM metadata_ml_configs
                ORDER BY name
            """)
            with engine.connect() as conn:
                rows = conn.execute(query).mappings().all()
                dtos = [MLConfigDTO(
                    id=row["id"],
                    name=row["name"],
                    metric_name=row["metric_name"],
                    group_by=row["group_by"],
                    methods=row["methods"],
                    method_params=self._deserialize_json(row["method_params"]),
                    retrain_schedule=row["retrain_schedule"],
                    auto_alert=row["auto_alert"],
                    alert_severity=row["alert_severity"],
                    is_active=row["is_active"]
                ) for row in rows]
                self._cache.setex(key, 300, self._serialize_json([asdict(d) for d in dtos]))
                return dtos
        except Exception as e:
            self._logger.error(f"❌ Ошибка списка всех ML-конфигов: {mask_secrets(str(e))}")
            return []

    # --- Утилиты ---

    @staticmethod
    def make_fingerprint(metric_name: str, dimensions: Dict[str, str], rule_id: Optional[uuid.UUID] = None) -> str:
        """Генерирует стабильный fingerprint для подавления дублей"""
        parts = [metric_name] + sorted([f"{k}={v}" for k, v in dimensions.items()])
        if rule_id:
            parts.append(str(rule_id))
        return hashlib.md5(":".join(parts).encode()).hexdigest()



# Экземпляр сервиса — синглтон
metadata_service = MetadataService()

def get_or_create_default_ml_configs(metric_name: str) -> List[MLConfigDTO]:
    configs = [c for c in metadata_service.list_active_ml_configs() if c.metric_name == metric_name]
    if not configs:
        return [MLConfigDTO(
            name=f"Auto-{metric_name}",
            metric_name=metric_name,
            group_by=["region"],
            methods=["prophet"],
            method_params={},
            is_active=True,
            id=None
        )]
    return configs
