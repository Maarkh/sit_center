# core/alerts.py
import time
import hashlib
from datetime import datetime, timedelta, timezone
import threading
from queue import Queue, Empty
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import pandas as pd
from config import settings, logger, get_cache
from core.database import get_engine, get_session
from core.notifications import notify
from core.smart_alerts import check_growth_alert, check_deviation_alert
from core.alert_settings import AlertSettings
from core.metric_service import get_metric_by_column
from core.models import AlertEvent, Incident
from sqlalchemy.exc import IntegrityError
import json

incident_queue = Queue(maxsize=100)
buffer_event = threading.Event()
_incident_processor_started = False
_last_check_times = {}

@dataclass
class AlertLog:
    timestamp: float
    metric: str
    region: str
    value: float
    priority: str = "info"

def get_engine_proxy():
    return get_engine()

def generate_alert_hash(metric: str, region: str, value: float) -> str:
    # Not security-sensitive: just a stable dedup/fingerprint key, not a digest of secrets.
    return hashlib.md5(f"{metric}_{region}_{value}".encode(), usedforsecurity=False).hexdigest()

def is_alert_suppressed(alert_hash: str, tenant_id: str = "default") -> bool:
    """Проверяет, подавлен ли алерт."""
    try:
        return get_cache().get(f"alert_suppression:{tenant_id}:{alert_hash}") is not None
    except Exception:
        return False


def are_alerts_suppressed(alert_hashes: list, tenant_id: str = "default") -> dict:
    """Пакетная проверка подавления алертов."""
    if not alert_hashes:
        return {}

    cache = get_cache()
    keys = [f"alert_suppression:{tenant_id}:{h}" for h in alert_hashes]

    try:
        pipe = cache.pipeline()
        for key in keys:
            pipe.exists(key)
        results = pipe.execute()

        return {h: bool(r) for h, r in zip(alert_hashes, results)}
    except Exception:
        return {h: False for h in alert_hashes}

def suppress_alert(alert_hash: str, minutes: int, tenant_id: str = "default"):
    if alert_hash.startswith("escalation_"):
        return
    get_cache().setex(f"alert_suppression:{tenant_id}:{alert_hash}", minutes * 60, "1")

def track_escalation_data(metric: str, region: str, value: float, tenant_id: str = "default"):
    cache = get_cache()
    key = f"escalation_tracker:{tenant_id}:{metric}:{region}"
    hist = cache.get(key)
    hist = json.loads(hist) if hist else []
    hist.append({"timestamp": time.time(), "value": value})
    hist = hist[-10:]
    cache.setex(key, 3600, json.dumps(hist))

def is_steady_increase(vals: List[float]) -> bool:
    return len(vals) >= 3 and all(vals[i] > vals[i-1] for i in range(1, len(vals)))

def check_escalation_alert(metric: str, region: str, current_value: float, is_suppressed: bool, tenant_id: str = "default") -> Optional[Tuple[str, str]]:
    if not is_suppressed:
        return None
    cache = get_cache()
    key = f"escalation_tracker:{tenant_id}:{metric}:{region}"
    hist_raw = cache.get(key)
    if not hist_raw:
        return None
    try:
        hist = json.loads(hist_raw)
        if len(hist) < 3:
            return None
        vals = [h["value"] for h in hist]
        if is_steady_increase(vals):
            growth = ((current_value - vals[0]) / vals[0]) * 100 if vals[0] > 0 else 100
            if growth > 50:
                return (f"🚨 ЭСКАЛАЦИЯ: {metric} в {region} вырос на {growth:.1f}% до {current_value}!", "critical")
            elif growth > 25:
                return (f"⚠️ Эскалация: {metric} в {region} вырос на {growth:.1f}%", "warning")
    except Exception as e:
        logger.warning(f"Ошибка эскалации: {e}")
    return None

def create_incident_buffered(alert_message: str, metric: str, region: str, value: float, priority: str, tenant_id: str = "default"):
    data = {
        "alert_message": alert_message,
        "metric": metric,
        "region": region,
        "value": str(value),
        "priority": priority,
        "tenant_id": tenant_id,
        "detected_at": datetime.now(timezone.utc),
    }
    try:
        incident_queue.put(data, timeout=1)
        if incident_queue.qsize() >= 80:
            buffer_event.set()
    except Exception as e:
        logger.error(f"Очередь переполнена: {e}")
        _create_incident_directly(data)

def _create_incident_directly(data: Dict):
    s = get_session()
    try:
        incident = Incident(**data)
        s.add(incident)
        s.commit()
        # Apply SLA policy
        try:
            from core.sla_service import apply_sla_to_incident
            apply_sla_to_incident(
                incident.id,
                data.get("tenant_id", "default"),
                data.get("priority", "medium"),
                data.get("detected_at", datetime.now(timezone.utc)),
            )
        except Exception as e:
            logger.warning(f"Failed to apply SLA to auto-created incident: {e}")
        # Push to i-doit
        try:
            from core.idoit_service import push_incident_create
            push_incident_create(incident.id)
        except Exception as e:
            logger.warning(f"Failed to push auto-created incident to i-doit: {e}")
    except Exception as e:
        s.rollback()
        logger.error(f"❌ Прямое создание инцидента упало: {e}")
    finally:
        s.close()

def process_incident_buffer():
    logger.info("🔄 Запущен процессор инцидентов")
    while True:
        try:
            buffer_event.wait(timeout=30)
            buffer_event.clear()
            batch = []
            while not incident_queue.empty() and len(batch) < 20:
                try:
                    batch.append(incident_queue.get_nowait())
                except Empty:
                    break
            if not batch:
                continue

            s = get_session()
            try:
                s.bulk_insert_mappings(Incident, batch)
                s.commit()
                logger.info(f"✅ Пакет инцидентов: {len(batch)}")
            except Exception as e:
                s.rollback()
                logger.error(f"❌ Ошибка пакета: {e}")
                for item in batch:
                    incident_queue.put_nowait(item)
            finally:
                s.close()
        except Exception as e:
            logger.exception(f"💥 Критическая ошибка в процессоре: {e}")
            time.sleep(5)

def start_incident_buffer_processor():
    global _incident_processor_started
    if _incident_processor_started:
        return
    _incident_processor_started = True
    t = threading.Thread(target=process_incident_buffer, daemon=True, name="IncidentProcessor")
    t.start()
    logger.info("✅ Процессор инцидентов запущен")

def get_alert_history(tenant_id: str = "default") -> List[AlertLog]:
    try:
        raw = get_cache().get(f"alert_history:{tenant_id}")
        if raw:
            return [AlertLog(**item) for item in json.loads(raw)]
    except Exception as e:
        logger.warning(f"Ошибка чтения истории: {e}")
    return []

def save_alert_history(history: List[AlertLog], tenant_id: str = "default"):
    if len(history) > 100:
        history = history[-100:]
    try:
        data = [a.__dict__ for a in history]
        get_cache().setex(f"alert_history:{tenant_id}", 86400, json.dumps(data))
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")

def check_for_alerts(df: pd.DataFrame, col: str, selected: str, last_alert_region: str, alert_settings: AlertSettings, tenant_id: str = "default") -> Tuple[bool, str]:
    now = time.time()
    if col in _last_check_times and now - _last_check_times[col] < 30:
        return False, last_alert_region
    _last_check_times[col] = now

    if df.empty or col not in df.columns:
        return False, last_alert_region

    if not alert_settings.alerts_enabled:
        return False, last_alert_region

    metric = get_metric_by_column(col)
    if not metric:
        return False, last_alert_region

    max_idx = df[col].idxmax()
    region = str(df.iloc[max_idx].get("region", "N/A"))
    val = df.iloc[max_idx].get(col, 0)
    if hasattr(val, "item"):
        val = val.item()
    if not pd.notna(val):
        return False, last_alert_region

    alert_hash = generate_alert_hash(col, region, val)
    is_suppressed = is_alert_suppressed(alert_hash, tenant_id=tenant_id)

    escalation = check_escalation_alert(col, region, val, is_suppressed, tenant_id=tenant_id)
    if escalation:
        msg, prio = escalation
        notify(msg, prio)
        create_incident_buffered(msg, col, region, val, prio, tenant_id=tenant_id)
        track_escalation_data(col, region, val, tenant_id=tenant_id)
        return True, region

    if is_suppressed:
        return False, last_alert_region

    # Основные проверки
    msg = None
    prio = "info"

    if alert_settings.smart_growth_enabled:
        msg = check_growth_alert(df, col, selected, alert_settings)
        if msg:
            prio = "critical"

    if not msg and alert_settings.smart_deviation_enabled:
        msg = check_deviation_alert(df, col, selected, alert_settings)
        if msg:
            prio = "warning"

    if not msg and val > alert_settings.thresholds.get(selected, metric.threshold):
        msg = f"🚨 {selected}: {region} — {int(val)}"
        crit_mult = alert_settings.priority_multipliers.get("critical", 1.5)
        prio = "critical" if val > alert_settings.thresholds.get(selected, metric.threshold) * crit_mult else "warning"

    if not msg:
        try:
            from core.ml_anomaly import find_recent_ml_anomalies
            anomalies = find_recent_ml_anomalies(
                time_filter="1h",
                metrics=[col],
                tenant_id=tenant_id,
            )
            recent = [
                a for a in anomalies
                if a["metric_name"] == col and a["dimensions"].get("region") == region
                and pd.Timestamp(a["timestamp"]) > pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=30)
            ]
            if recent:
                latest = recent[0]
                msg = f"🤖 ML: {region} — {latest['value']:.1f} (прогноз: {latest['predicted']:.1f})"
                prio = "critical"
        except Exception as e:
            logger.warning(f"ML проверка упала: {e}")

    if not msg:
        return False, last_alert_region

    # Сохранение алерта
    s = get_session()

    # Best-effort lock so two concurrent workers don't both create this same
    # (tenant, alert). Redis being down must NOT block alerting → best-effort:
    # on any Redis error we simply proceed without the lock.
    lock_key = f"alert_create_lock:{tenant_id}:{alert_hash}"
    lock_acquired = False
    try:
        lock_acquired = bool(get_cache().set(lock_key, "1", nx=True, ex=15))
        if not lock_acquired:
            # Another worker is already creating this exact alert right now.
            s.close()
            return False, last_alert_region
    except Exception:
        lock_acquired = False

    try:
        existing = s.query(AlertEvent).filter_by(alert_hash=alert_hash, tenant_id=tenant_id).first()
        if existing and existing.sent_at and (
            datetime.now(timezone.utc) - existing.sent_at < timedelta(minutes=alert_settings.get_suppression_minutes(selected))
        ):
            suppress_alert(alert_hash, alert_settings.get_suppression_minutes(selected), tenant_id=tenant_id)
            return False, last_alert_region

        new_alert = AlertEvent(
            alert_hash=alert_hash,
            metric_name=selected,
            dimensions={"region": region},
            value=val,
            event_time=datetime.now(timezone.utc),
            detected_at=datetime.now(timezone.utc),
            status="firing",
            sent=False,
            fingerprint=alert_hash,
            tenant_id=tenant_id,
        )
        s.add(new_alert)
        # Persist the alert row FIRST. The side-effects below (notification,
        # incident, pub/sub) are irreversible, so they must run only after the
        # row is durably committed — otherwise a failed commit would send a
        # notification for an alert that was never recorded.
        s.commit()
        alert_id = str(new_alert.id)
        event_time_iso = new_alert.event_time.isoformat()

        # Отправка (queued + idempotent). A failure here must not orphan or
        # roll back the already-committed alert row.
        try:
            notify(msg, prio)
        except Exception as e:
            logger.warning(f"Notification enqueue failed (alert {alert_id} already recorded): {e}")

        # Инцидент
        try:
            create_incident_buffered(msg, selected, region, val, prio, tenant_id=tenant_id)
            new_alert.incident_created = True
            new_alert.incident_created_at = datetime.now(timezone.utc)
        except Exception as e:
            logger.warning(f"Incident buffering failed for alert {alert_id}: {e}")

        new_alert.sent = True
        new_alert.sent_at = datetime.now(timezone.utc)
        s.commit()

        # Publish to Redis Pub/Sub for WebSocket clients
        alert_payload = {
            "type": "alert",
            "id": alert_id,
            "metric": selected,
            "dimensions": {"region": region},
            "value": float(val),
            "status": "firing",
            "event_time": event_time_iso,
            "tenant_id": tenant_id,
        }
        try:
            from core.pubsub import publish_alert
            publish_alert(alert_payload)
        except Exception as e:
            logger.warning(f"Failed to publish alert to pubsub: {e}")

        # Publish to Kafka if enabled
        try:
            if settings.KAFKA_ENABLED:
                from core.kafka_producer import publish_alert_event
                publish_alert_event(alert_payload)
        except Exception as e:
            logger.warning(f"Failed to publish alert to Kafka: {e}")

        # История
        history = get_alert_history(tenant_id=tenant_id)
        history.append(AlertLog(time.time(), selected, region, val, prio))
        save_alert_history(history, tenant_id=tenant_id)

        logger.info(f"✅ Алерт создан: {alert_id}")
        return True, region

    except IntegrityError:
        s.rollback()
        return False, last_alert_region
    except Exception as e:
        s.rollback()
        logger.exception(f"❌ Ошибка алерта: {e}")
        return False, last_alert_region
    finally:
        s.close()
        if lock_acquired:
            try:
                get_cache().delete(lock_key)
            except Exception:
                pass
