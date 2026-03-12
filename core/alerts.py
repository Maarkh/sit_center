# core/alerts.py
import time
import hashlib
from datetime import datetime, timedelta, timezone
import threading
from queue import Queue, Empty
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass
import pandas as pd
from config import settings, logger, get_cache, get_database_url
from core.database import get_engine
from core.notifications import notify
from core.smart_alerts import check_growth_alert, check_deviation_alert
from core.alert_settings import AlertSettings, load_alert_settings_cached
from core.metric_service import get_metric_by_column
from core.models import AlertEvent, Incident
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import json

incident_queue = Queue(maxsize=100)
buffer_event = threading.Event()
HISTORY_KEY = "alert_history"
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
    return hashlib.md5(f"{metric}_{region}_{value}".encode()).hexdigest()

def is_alert_suppressed(alert_hash: str) -> bool:
    """Проверяет, подавлен ли алерт."""
    try:
        return get_cache().get(f"alert_suppression:{alert_hash}") is not None
    except Exception:
        return False


def are_alerts_suppressed(alert_hashes: list) -> dict:
    """Пакетная проверка подавления алертов."""
    if not alert_hashes:
        return {}
    
    cache = get_cache()
    keys = [f"alert_suppression:{h}" for h in alert_hashes]
    
    try:
        # Используем pipeline для одного запроса
        pipe = cache.pipeline()
        for key in keys:
            pipe.exists(key)
        results = pipe.execute()
        
        return {h: bool(r) for h, r in zip(alert_hashes, results)}
    except Exception:
        return {h: False for h in alert_hashes}

def suppress_alert(alert_hash: str, minutes: int):
    if alert_hash.startswith("escalation_"):
        return
    get_cache().setex(f"alert_suppression:{alert_hash}", minutes * 60, "1")

def track_escalation_data(metric: str, region: str, value: float):
    cache = get_cache()
    key = f"escalation_tracker:{metric}:{region}"
    hist = cache.get(key)
    hist = json.loads(hist) if hist else []
    hist.append({"timestamp": time.time(), "value": value})
    hist = hist[-10:]
    cache.setex(key, 3600, json.dumps(hist))

def is_steady_increase(vals: List[float]) -> bool:
    return len(vals) >= 3 and all(vals[i] > vals[i-1] for i in range(1, len(vals)))

def check_escalation_alert(metric: str, region: str, current_value: float, is_suppressed: bool) -> Optional[Tuple[str, str]]:
    if not is_suppressed:
        return None
    cache = get_cache()
    key = f"escalation_tracker:{metric}:{region}"
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

def create_incident_buffered(alert_message: str, metric: str, region: str, value: float, priority: str):
    data = {
        "alert_message": alert_message,
        "metric": metric,
        "region": region,
        "value": str(value),
        "priority": priority,
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
    engine = get_engine_proxy()
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        incident = Incident(**data)
        s.add(incident)
        s.commit()
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

            engine = get_engine_proxy()
            Session = sessionmaker(bind=engine)
            s = Session()
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
    t = threading.Thread(target=process_incident_buffer, daemon=True, name="IncidentProcessor")
    t.start()
    logger.info("✅ Процессор инцидентов запущен")

def get_alert_history() -> List[AlertLog]:
    try:
        raw = get_cache().get(HISTORY_KEY)
        if raw:
            return [AlertLog(**item) for item in json.loads(raw)]
    except Exception as e:
        logger.warning(f"Ошибка чтения истории: {e}")
    return []

def save_alert_history(history: List[AlertLog]):
    if len(history) > 100:
        history = history[-100:]
    try:
        data = [a.__dict__ for a in history]
        get_cache().setex(HISTORY_KEY, 86400, json.dumps(data))
    except Exception as e:
        logger.error(f"Ошибка сохранения истории: {e}")

def check_for_alerts(df: pd.DataFrame, col: str, selected: str, last_alert_region: str, alert_settings: AlertSettings) -> Tuple[bool, str]:
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
    is_suppressed = is_alert_suppressed(alert_hash)

    escalation = check_escalation_alert(col, region, val, is_suppressed)
    if escalation:
        msg, prio = escalation
        notify(msg, prio)
        create_incident_buffered(msg, col, region, val, prio)
        track_escalation_data(col, region, val)
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
                metrics=[col]
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
    engine = get_engine_proxy()
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        existing = s.query(AlertEvent).filter_by(alert_hash=alert_hash).first()
        if existing and existing.sent_at and (
            datetime.now(timezone.utc) - existing.sent_at < timedelta(minutes=alert_settings.get_suppression_minutes(selected))
        ):
            suppress_alert(alert_hash, alert_settings.get_suppression_minutes(selected))
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
            fingerprint=alert_hash
        )
        s.add(new_alert)
        s.flush()

        # Отправка
        notify(msg, prio)
        new_alert.sent = True
        new_alert.sent_at = datetime.now(timezone.utc)

        # Инцидент
        create_incident_buffered(msg, selected, region, val, prio)
        new_alert.incident_created = True
        new_alert.incident_created_at = datetime.now(timezone.utc)

        s.commit()

        # Publish to Redis Pub/Sub for WebSocket clients
        alert_payload = {
            "type": "alert",
            "id": str(new_alert.id),
            "metric": selected,
            "dimensions": {"region": region},
            "value": float(val),
            "status": "firing",
            "event_time": new_alert.event_time.isoformat(),
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
        history = get_alert_history()
        history.append(AlertLog(time.time(), selected, region, val, prio))
        save_alert_history(history)

        logger.info(f"✅ Алерт создан: {new_alert.id}")
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

if __name__ != "__main__":
    start_incident_buffer_processor()