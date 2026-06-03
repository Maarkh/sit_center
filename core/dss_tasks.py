# core/dss_tasks.py
"""Celery tasks for the DSS modules (M3 deviation detection, M8 step SLA)."""
from celery_app import celery_app
from config import logger


def _active_tenant_ids():
    """Active tenant ids, falling back to ['default'] if the table is absent."""
    try:
        from sqlalchemy import text
        from core.database import get_engine
        with get_engine().connect() as conn:
            rows = conn.execute(
                text("SELECT id FROM tenants WHERE is_active = true")
            ).scalars().all()
        return list(rows) or ["default"]
    except Exception:
        return ["default"]


@celery_app.task(time_limit=120)
def evaluate_indicators_task():
    """M3: evaluate every active indicator against its corridor, per tenant."""
    try:
        from core.deviation_engine import indicator_evaluator
        totals = {"evaluated": 0, "skipped": 0, "breaching": 0,
                  "opened": 0, "resolved": 0, "chronic": 0}
        for tenant_id in _active_tenant_ids():
            s = indicator_evaluator.evaluate_tenant(tenant_id=tenant_id)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info(
            "Indicator evaluation: %d evaluated, %d breaching, %d opened, "
            "%d resolved, %d chronic",
            totals["evaluated"], totals["breaching"], totals["opened"],
            totals["resolved"], totals["chronic"],
        )
        return totals
    except Exception as e:
        logger.exception("Indicator evaluation failed")
        return {"error": str(e)}


@celery_app.task(time_limit=180)
def correlate_situations_task(window_minutes: int = 30):
    """M4: correlate active deviations into situations, per tenant."""
    try:
        from core.situation_engine import situation_engine
        totals = {"clusters": 0, "created": 0, "updated": 0, "resolved": 0}
        for tenant_id in _active_tenant_ids():
            s = situation_engine.correlate_tenant(tenant_id=tenant_id, window_minutes=window_minutes)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info("Situation correlation: %d clusters, %d created, %d updated, %d resolved",
                    totals["clusters"], totals["created"], totals["updated"], totals["resolved"])
        return totals
    except Exception as e:
        logger.exception("Situation correlation failed")
        return {"error": str(e)}


@celery_app.task(time_limit=600)
def predict_indicators_task(horizon_hours: int = 24):
    """M5: forecast each active indicator and raise predictive alerts on projected
    corridor breaches, per tenant. No-op where Prophet/data is unavailable."""
    try:
        from core.predictive_engine import predictive_engine
        totals = {"evaluated": 0, "skipped": 0, "raised": 0, "resolved": 0}
        for tenant_id in _active_tenant_ids():
            s = predictive_engine.evaluate_tenant(tenant_id=tenant_id, horizon_hours=horizon_hours)
            for k in totals:
                totals[k] += s.get(k, 0)
        logger.info("Predictive: %d evaluated, %d raised, %d resolved, %d skipped",
                    totals["evaluated"], totals["raised"], totals["resolved"], totals["skipped"])
        return totals
    except Exception as e:
        logger.exception("Predictive task failed")
        return {"error": str(e)}


@celery_app.task(time_limit=120)
def check_process_step_sla_task():
    """M8: escalate process step assignments that are past their due_at."""
    try:
        from core.process_engine import process_engine
        total = 0
        for tenant_id in _active_tenant_ids():
            total += process_engine.escalate_overdue_steps(tenant_id=tenant_id)
        logger.info("Process step SLA check: %d steps escalated", total)
        return {"escalated": total}
    except Exception as e:
        logger.exception("Process step SLA check failed")
        return {"error": str(e)}
