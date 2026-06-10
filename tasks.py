# tasks.py
import pandas as pd
from sqlalchemy import text
from celery_app import celery_app
from core.database import get_engine
from core.smart_alerts import check_growth_alert
from core.alert_settings import load_alert_settings_cached
from config import logger, get_redis
from core.notifications import notify
from celery.signals import task_failure
from datetime import datetime, timezone
from hashlib import md5


def get_data_from_db(time_filter: str = "1h") -> pd.DataFrame:
    delta_map = {"1h": 1, "6h": 6, "24h": 24}
    hours = delta_map.get(time_filter, 1)
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)

    engine = get_engine()
    
    # 🔒 ИСПРАВЛЕНО: безопасный параметризованный запрос
    query = text("""
        SELECT
            date_trunc('hour', cm.timestamp AT TIME ZONE 'UTC') AS hour,
            cm.dimensions->>'region' AS region,
            MAX(CASE WHEN cm.metric_name = 'complaints' THEN cm.value END) AS complaints,
            MAX(CASE WHEN cm.metric_name = 'closed' THEN cm.value END) AS closed
        FROM canonical_metrics cm
        WHERE cm.metric_name = ANY(:metric_names)
          AND cm.timestamp >= :cutoff
          AND cm.dimensions ? 'region'
        GROUP BY hour, cm.dimensions->>'region'
        ORDER BY hour DESC
    """)
    return pd.read_sql(query, engine, params={
        "metric_names": ["complaints", "closed"],
        "cutoff": cutoff
    }) # type: ignore


@celery_app.task(bind=True, max_retries=3)
def run_alerts_check_task(self, time_filter: str = "1h"):
    try:
        df = get_data_from_db(time_filter)
        if df.empty:
            return {"status": "no_data"}

        alert_settings = load_alert_settings_cached()
        alerts = []

        for col, name in [("complaints", "Жалобы"), ("closed", "Сеть")]:
            msg = check_growth_alert(df, col, name, alert_settings)
            if msg:
                notify(msg, "critical")
                alerts.append({"metric": name, "alert": msg})

        return {"status": "success", "alerts": alerts}
    except Exception as exc:
        logger.exception("❌ Celery task failed")
        raise self.retry(exc=exc, countdown=30)



@celery_app.task(bind=True, max_retries=3)
def send_notification(self, message: str, priority: str, idempotency_key: str = None,
                      event_type: str = "system", tenant_id: str = "default"): # type: ignore
    if not idempotency_key:
        # Non-security fingerprint for de-duplicating notifications.
        idempotency_key = md5(f"{message}:{priority}:{event_type}".encode(), usedforsecurity=False).hexdigest()[:16]

    cache = get_redis()
    cache_key = f"notification_sent:{idempotency_key}"
    if cache.get(cache_key):
        logger.info(f"🔇 Дубликат уведомления (idempotency_key={idempotency_key})")
        return True

    try:
        from core.notification_channels import dispatch
        result = dispatch(message, priority, event_type, tenant_id)
        # Delivered if a channel sent it, or nothing was subscribed (intentional
        # silence — don't retry forever). Retry only when matched channels all failed.
        delivered = result.get("sent", 0) > 0 or result.get("silent", False)
        if not delivered:
            raise RuntimeError(f"all channels failed: {result}")
        if result.get("sent", 0) > 0:
            cache.setex(cache_key, 3600, "1")  # 1 час дедупликации
        return True
    except Exception as e:
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task
def update_mv_data():
    try:
        from core.data import create_mv
        if create_mv():
            logger.info("✅ MV обновлены")
        else:
            logger.warning("⚠️ Не удалось обновить MV")
    except Exception:
        logger.exception("⚠️ Ошибка при обновлении MV")


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    try:
        task_name = getattr(sender, "name", sender)
        if task_name == "tasks.send_notification":
            args = kwargs.get("args", [])
            message = str(args[0]) if len(args) > 0 else ""
            priority = str(args[1]) if len(args) > 1 else "info"
            
            payload = {
                "task_id": task_id or "",
                "message": message,
                "priority": priority,
                "error": str(exception),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            try:
                get_redis().xadd("dlq:notifications", payload) # type: ignore
                logger.error(f"🚨 DLQ запись: {message[:50]}...")
            except Exception:
                logger.exception("❌ Ошибка записи в DLQ")
    except Exception:
        logger.exception("💥 Ошибка в handle_task_failure")
        
@celery_app.task
def check_sla_breaches_task():
    try:
        from core.sla_service import check_sla_breaches
        result = check_sla_breaches()
        if result["response_breaches"] or result["resolution_breaches"]:
            logger.warning(f"SLA breaches: {result}")
        return result
    except Exception:
        logger.exception("SLA breach check failed")


@celery_app.task
def check_auto_escalation_task():
    try:
        from core.sla_service import check_auto_escalation
        check_auto_escalation()
    except Exception:
        logger.exception("Auto-escalation check failed")


@celery_app.task
def healthcheck():
    return {"status": "ok"}


# Self-monitoring: a beat-scheduled heartbeat is the deadman for the whole DSS loop —
# if Celery beat hangs/dies, every scheduled task silently stops, so this key going stale
# is the signal. The beat pod's liveness probe reads it; alert on its absence in prod.
DLQ_DEPTH_WARN = 100


@celery_app.task
def beat_heartbeat():
    try:
        r = get_redis()
        r.set("beat:heartbeat", datetime.now(timezone.utc).isoformat(), ex=180)
        # surface notification DLQ growth (write+replay queue) as an alertable signal
        try:
            depth = r.xlen("dlq:notifications")
            if depth and depth >= DLQ_DEPTH_WARN:
                logger.warning("notification DLQ depth high: %d (>= %d)", depth, DLQ_DEPTH_WARN)
            return {"heartbeat": True, "dlq_depth": int(depth or 0)}
        except Exception:
            return {"heartbeat": True}
    except Exception:
        logger.exception("beat_heartbeat failed")
        return {"heartbeat": False}


