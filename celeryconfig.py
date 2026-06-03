# 📄 celeryconfig.py (новый файл)
from celery.schedules import crontab

beat_schedule = {
    'ml-anomaly-10min': {
        'task': 'core.ml_tasks.run_ml_anomaly_check',
        'schedule': crontab(minute='*/10')
    },
    'retrain-ml-models-daily': {
        'task': 'core.ml_tasks.retrain_ml_models',
        'schedule': crontab(hour=3, minute=0)
    },
    'update-mv-10min': {
        'task': 'tasks.update_mv_data',
        'schedule': crontab(minute='*/10')
    },
    'evaluate-rules-1min': {
        'task': 'core.ml_tasks.evaluate_rules_task',
        'schedule': crontab(minute='*/1')
    },
    'check-sla-breaches-5min': {
        'task': 'tasks.check_sla_breaches_task',
        'schedule': crontab(minute='*/5')
    },
    'check-auto-escalation-5min': {
        'task': 'tasks.check_auto_escalation_task',
        'schedule': crontab(minute='*/5')
    },
    # DSS M3: evaluate indicators against their corridor + maintain chronicles.
    'evaluate-indicators-2min': {
        'task': 'core.dss_tasks.evaluate_indicators_task',
        'schedule': crontab(minute='*/2')
    },
    # DSS M8: escalate process steps that are past their SLA deadline.
    'check-process-step-sla-5min': {
        'task': 'core.dss_tasks.check_process_step_sla_task',
        'schedule': crontab(minute='*/5')
    },
    # DSS M5: forecast indicators and raise predictive (early-warning) alerts.
    'predict-indicators-15min': {
        'task': 'core.dss_tasks.predict_indicators_task',
        'schedule': crontab(minute='*/15')
    },
    # DSS M4: correlate active deviations into situations (runs after deviation eval).
    'correlate-situations-3min': {
        'task': 'core.dss_tasks.correlate_situations_task',
        'schedule': crontab(minute='*/3')
    },
    # DSS M10: auto-derive decision outcomes from finished processes (learning loop).
    'evaluate-decision-outcomes-10min': {
        'task': 'core.dss_tasks.evaluate_decision_outcomes_task',
        'schedule': crontab(minute='*/10')
    },
}