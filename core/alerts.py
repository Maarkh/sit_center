# core/alerts.py
import time
import hashlib
from datetime import datetime, timezone
import threading
from queue import Queue, Empty
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
from config import logger, get_cache
from core.database import get_engine, get_session
from core.models import Incident
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
