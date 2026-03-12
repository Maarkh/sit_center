# tests/test_ml_smoke.py
"""
ML smoke tests that work WITHOUT heavy ML dependencies (Prophet, TensorFlow, torch).
These run in CI to verify ML pipeline logic, error handling, and graceful degradation.

Note: We do NOT import core.ml_anomaly directly because it pulls in tensorflow/torch
at module level. Instead, we test through the Celery task layer (which uses local
imports) and mock the ML internals.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from uuid import uuid4


# --- ML task layer (safe to import — uses lazy local imports) ---

def test_ml_tasks_import():
    """Verify ml_tasks module has expected Celery tasks."""
    from core.ml_tasks import run_ml_anomaly_check, retrain_ml_models, evaluate_rules_task
    assert callable(run_ml_anomaly_check)
    assert callable(retrain_ml_models)
    assert callable(evaluate_rules_task)


def test_run_ml_anomaly_check_handles_import_error():
    """ML anomaly check task gracefully handles missing ML libs."""
    from core.ml_tasks import run_ml_anomaly_check
    # ml_tasks does `from core.ml_anomaly import find_recent_ml_anomalies` inside the function.
    # We mock at the sys.modules level to simulate import failure.
    mock_module = MagicMock()
    mock_module.find_recent_ml_anomalies = MagicMock(side_effect=ImportError("No prophet"))
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = run_ml_anomaly_check()
        assert result == 0


def test_run_ml_anomaly_check_handles_runtime_error():
    """ML anomaly check task returns 0 on runtime failure."""
    from core.ml_tasks import run_ml_anomaly_check
    mock_module = MagicMock()
    mock_module.find_recent_ml_anomalies = MagicMock(side_effect=RuntimeError("DB down"))
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = run_ml_anomaly_check()
        assert result == 0


def test_run_ml_anomaly_check_success():
    """ML anomaly check returns anomaly list on success."""
    from core.ml_tasks import run_ml_anomaly_check
    mock_module = MagicMock()
    mock_module.find_recent_ml_anomalies = MagicMock(return_value=[{"id": 1}])
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = run_ml_anomaly_check()
        # The task calls find_recent_ml_anomalies and returns its result
        assert result is not None


def test_retrain_ml_models_handles_error():
    """Retrain task returns error status on failure."""
    from core.ml_tasks import retrain_ml_models
    mock_module = MagicMock()
    mock_module.retrain_all_models = MagicMock(side_effect=RuntimeError("DB down"))
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = retrain_ml_models()
        assert result["status"] == "error"
        assert "DB down" in result["message"]


def test_retrain_ml_models_success():
    """Retrain task returns success on happy path."""
    from core.ml_tasks import retrain_ml_models
    mock_module = MagicMock()
    mock_module.retrain_all_models = MagicMock()
    with patch.dict("sys.modules", {"core.ml_anomaly": mock_module}):
        result = retrain_ml_models()
        assert result["status"] == "success"


def test_evaluate_rules_task_handles_error():
    """Rule evaluation task returns error on failure."""
    from core.ml_tasks import evaluate_rules_task
    mock_re_module = MagicMock()
    mock_re_module.rule_engine.evaluate_all_rules.side_effect = RuntimeError("boom")
    with patch.dict("sys.modules", {"core.rule_engine": mock_re_module}):
        result = evaluate_rules_task()
        assert "error" in result


def test_evaluate_rules_task_success():
    """Rule evaluation returns check/fired counts."""
    from core.ml_tasks import evaluate_rules_task
    mock_result = MagicMock()
    mock_result.fired = True
    mock_result.rule_name = "test"
    mock_result.metric_name = "cpu"
    mock_result.operator = ">"
    mock_result.threshold = 80
    mock_result.current_value = 95.0

    mock_re_module = MagicMock()
    mock_re_module.rule_engine.evaluate_all_rules.return_value = [mock_result]
    with patch.dict("sys.modules", {"core.rule_engine": mock_re_module}), \
         patch("core.notifications.notify"):
        result = evaluate_rules_task()
        assert result["checked"] == 1
        assert result["fired"] == 1


# --- MLConfigDTO structure ---

def test_ml_config_dto_structure():
    """Verify MLConfigDTO has required fields."""
    from core.metadata_service import MLConfigDTO
    cfg = MLConfigDTO(
        name="test",
        metric_name="cpu_usage",
        group_by=["region"],
        methods=["prophet"],
        method_params={},
        retrain_schedule="0 3 * * *",
        auto_alert=True,
        alert_severity="warning",
        is_active=True,
        id=uuid4(),
    )
    assert cfg.metric_name == "cpu_usage"
    assert "prophet" in cfg.methods
    assert cfg.auto_alert is True


def test_ml_config_dto_defaults():
    """MLConfigDTO with minimal + default fields."""
    from core.metadata_service import MLConfigDTO
    cfg = MLConfigDTO(
        name="minimal",
        metric_name="m",
        group_by=[],
        methods=["prophet"],
        method_params={},
    )
    assert cfg.is_active is True
    assert cfg.group_by == []
    assert cfg.alert_severity == "warning"


# --- Anomaly serialization ---

def test_serialize_anomalies_empty():
    """serialize_anomalies works for empty list."""
    from core.utils import serialize_anomalies
    result = serialize_anomalies([])
    assert result is not None


def test_serialize_anomalies_with_data():
    """serialize_anomalies works for non-empty list."""
    from core.utils import serialize_anomalies
    anomaly = {
        "metric_name": "cpu",
        "timestamp": datetime.now(timezone.utc),
        "value": 42.5,
        "predicted": 40.0,
        "residual": 2.5,
    }
    result = serialize_anomalies([anomaly])
    assert result is not None


# --- Forecast endpoint (ML consumer) ---

def test_forecast_endpoint_handles_import_error(api_client, auth_headers):
    """Forecast returns 501 when ML libs are unavailable."""
    mock_svc = MagicMock()
    mock_metric = MagicMock()
    mock_metric.metric_name = "test_metric"
    mock_svc.list_metrics.return_value = [mock_metric]

    with patch("core.metadata_service.metadata_service", mock_svc), \
         patch("api.routes.forecasts._generate_forecast", side_effect=ImportError("No prophet")):
        resp = api_client.get("/forecasts/predict?metric_name=test_metric", headers=auth_headers)
    assert resp.status_code == 501


# --- ML config API (consumer of ML metadata) ---

def test_ml_configs_endpoint_returns_list(api_client, auth_headers):
    """GET /ml/configs/ returns a list (may be empty)."""
    from api.main import app
    from api.dependencies import get_metadata_service
    mock_svc = MagicMock()
    mock_svc.list_active_ml_configs.return_value = []
    app.dependency_overrides[get_metadata_service] = lambda: mock_svc
    try:
        resp = api_client.get("/ml/configs/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.pop(get_metadata_service, None)
