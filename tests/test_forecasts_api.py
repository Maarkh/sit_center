# tests/test_forecasts_api.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_forecast_deps():
    """Mock metadata_service that's imported locally inside forecast route."""
    mock_service = MagicMock()
    with patch("core.metadata_service.metadata_service", mock_service):
        yield mock_service


def _make_metric(name="cpu_usage"):
    m = MagicMock()
    m.metric_name = name
    return m


def test_forecast_metric_not_found(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = []
    response = api_client.get(
        "/forecasts/predict?metric_name=nonexistent&horizon_hours=24",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_forecast_ml_not_available(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = [_make_metric()]

    with patch("api.routes.forecasts._generate_forecast", side_effect=ImportError("No prophet")):
        response = api_client.get(
            "/forecasts/predict?metric_name=cpu_usage",
            headers=auth_headers,
        )
    assert response.status_code == 501


def test_forecast_not_enough_data(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = [_make_metric()]

    with patch("api.routes.forecasts._generate_forecast",
               side_effect=ValueError("Not enough data")):
        response = api_client.get(
            "/forecasts/predict?metric_name=cpu_usage",
            headers=auth_headers,
        )
    assert response.status_code == 400


def test_forecast_success(api_client, auth_headers, mock_forecast_deps):
    mock_forecast_deps.list_metrics.return_value = [_make_metric()]

    from api.schemas import ForecastPoint
    points = [
        ForecastPoint(
            timestamp=datetime.now(timezone.utc),
            value=42.5,
            lower=38.0,
            upper=47.0,
        )
    ]

    with patch("api.routes.forecasts._generate_forecast", return_value=points):
        response = api_client.get(
            "/forecasts/predict?metric_name=cpu_usage&horizon_hours=12&region=RU-MOW",
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["metric_name"] == "cpu_usage"
    assert data["horizon_hours"] == 12
    assert len(data["points"]) == 1
    assert data["dimensions"]["region"] == "RU-MOW"


def test_forecast_requires_auth(api_client):
    response = api_client.get("/forecasts/predict?metric_name=x")
    assert response.status_code == 401
