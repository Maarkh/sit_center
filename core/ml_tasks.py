# core/ml_tasks.py
from celery_app import celery_app
from config import logger


def _active_tenant_ids():
    """Return active tenant ids, falling back to ['default'] if the table is absent."""
    try:
        from sqlalchemy import text
        from core.database import get_engine
        with get_engine().connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM tenants WHERE is_active = true")
            ).scalars().all()
        return list(rows) or ["default"]
    except Exception:
        # No tenants table (dev DB) or DB error → evaluate the default tenant only.
        return ["default"]


@celery_app.task(time_limit=60)
def evaluate_rules_task():
    try:
        from core.rule_engine import rule_engine
        from core.notifications import notify
        total_checked = 0
        total_fired = 0
        # Evaluate each tenant's rules against ONLY that tenant's metrics so rules
        # from one tenant never fire on another tenant's data.
        for tenant_id in _active_tenant_ids():
            results = rule_engine.evaluate_all_rules(tenant_id=tenant_id)
            fired = [r for r in results if r.fired]
            for r in fired:
                msg = f"Rule '{r.rule_name}': {r.metric_name} {r.operator} {r.threshold} (current: {r.current_value:.2f})"
                notify(msg, "warning")
            total_checked += len(results)
            total_fired += len(fired)
        logger.info("Rule evaluation: %d rules checked, %d fired", total_checked, total_fired)
        return {"checked": total_checked, "fired": total_fired}
    except Exception as e:
        logger.exception("Rule evaluation failed")
        return {"error": str(e)}


@celery_app.task(queue="ml", time_limit=600)
def run_ml_anomaly_check():
    try:
        from core.ml_anomaly import find_recent_ml_anomalies
        total = 0
        # Run detection per tenant so one tenant's metrics never feed another
        # tenant's anomaly models or results.
        for tenant_id in _active_tenant_ids():
            result = find_recent_ml_anomalies(time_filter="6h", tenant_id=tenant_id)
            total += result if isinstance(result, int) else len(result or [])
        logger.info(f"ML: found {total} anomalies")
        return total
    except Exception:
        logger.exception("ML task failed")
        return 0


@celery_app.task(queue="ml", time_limit=600)
def retrain_ml_models():
    try:
        from core.ml_anomaly import retrain_all_models
        retrain_all_models()
        return {"status": "success"}
    except Exception as e:
        logger.exception("Retrain ML failed")
        return {"status": "error", "message": str(e)}
