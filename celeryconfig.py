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
}