# 📄 celeryconfig.py (новый файл)
import os
from celery.schedules import crontab

# Indicator evaluation cadence (seconds). Default 120s for production; the demo sets
# EVAL_EVERY_SECONDS=20 so brief spikes are caught quickly (paired with EVAL_WINDOW_MIN).
_EVAL_EVERY_SECONDS = float(os.environ.get("EVAL_EVERY_SECONDS", "120"))

beat_schedule = {
    # DECOMMISSIONED: the legacy ml_anomaly detector is statistically unreliable —
    # it scores in-sample (train == predict, no holdout/backtest), forces
    # contamination=0.1 (a ~10% false-positive factory), percentile-clips the very
    # outliers it hunts, and its confidence column mixes 3 incompatible/inverted
    # formulas — so ml_anomalies.confidence is noise. DSS deviation/predictive engines
    # supersede it. Re-enable only after a rebuild with a holdout split + calibrated
    # threshold. (retrain only fed this detector, so it's parked too.)
    # 'ml-anomaly-10min': {
    #     'task': 'core.ml_tasks.run_ml_anomaly_check',
    #     'schedule': crontab(minute='*/10')
    # },
    # 'retrain-ml-models-daily': {
    #     'task': 'core.ml_tasks.retrain_ml_models',
    #     'schedule': crontab(hour=3, minute=0)
    # },
    'update-mv-10min': {
        'task': 'tasks.update_mv_data',
        'schedule': crontab(minute='*/10')
    },
    # Self-monitoring deadman: refresh beat:heartbeat every 60s (TTL 180s). The beat
    # pod's liveness probe + prod alerting watch this — if beat dies, the DSS loop stops.
    'beat-heartbeat-60s': {
        'task': 'tasks.beat_heartbeat',
        'schedule': 60.0
    },
    # Retired: classic rule detection (rule_engine → alert_events) is superseded by the
    # DSS indicator/corridor → deviation pipeline (evaluate-indicators-2min). The
    # rule_engine code stays for reference; it's simply no longer scheduled.
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
        'schedule': _EVAL_EVERY_SECONDS
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
    # B (zero-touch): auto-create baseline indicators for unwatched live metrics.
    # No-op unless AUTO_PROVISION_INDICATORS=true; cheap when there's nothing to do.
    'auto-provision-indicators-30min': {
        'task': 'core.dss_tasks.auto_provision_indicators_task',
        'schedule': crontab(minute='*/30')
    },
    # DSS M10: auto-derive decision outcomes from finished processes (learning loop).
    'evaluate-decision-outcomes-10min': {
        'task': 'core.dss_tasks.evaluate_decision_outcomes_task',
        'schedule': crontab(minute='*/10')
    },
    # DSS M5: score forecasts against actuals (MAE/RMSE/MAPE) and alert on model drift.
    'monitor-forecast-drift-daily': {
        'task': 'core.dss_tasks.monitor_forecast_drift_task',
        'schedule': crontab(hour=4, minute=0)
    },
}