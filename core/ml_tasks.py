# core/ml_tasks.py
from celery_app import celery_app
from config import logger


@celery_app.task(time_limit=60)
def evaluate_rules_task():
    try:
        from core.rule_engine import rule_engine
        from core.notifications import notify
        results = rule_engine.evaluate_all_rules()
        fired = [r for r in results if r.fired]
        for r in fired:
            msg = f"Rule '{r.rule_name}': {r.metric_name} {r.operator} {r.threshold} (current: {r.current_value:.2f})"
            notify(msg, "warning")
        logger.info("Rule evaluation: %d rules checked, %d fired", len(results), len(fired))
        return {"checked": len(results), "fired": len(fired)}
    except Exception as e:
        logger.exception("Rule evaluation failed")
        return {"error": str(e)}


@celery_app.task(queue="ml", time_limit=600)
def run_ml_anomaly_check():
    try:
        from core.ml_anomaly import find_recent_ml_anomalies
        count = find_recent_ml_anomalies(time_filter="6h")
        logger.info(f"ML: found {count} anomalies")
        return count
    except Exception as e:
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
