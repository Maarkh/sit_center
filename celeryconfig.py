# 📄 celeryconfig.py (новый файл)
from celery.schedules import crontab

beat_schedule = {
    'ml-anomaly-10min': {
        'task': 'tasks.run_ml_anomaly_check',
        'schedule': crontab(minute='*/10')
    },
    'retrain-ml-models-daily': {
        'task': 'tasks.retrain_ml_models',
        'schedule': crontab(hour=3, minute=0)
    },
    'update-mv-10min': {
        'task': 'tasks.update_mv_data',
        'schedule': crontab(minute='*/10')
    },
    'create-partition-monthly': {
        'task': 'tasks.create_monthly_partition',
        'schedule': crontab(day_of_month=28, hour=2, minute=0)
    }
}