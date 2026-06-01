# tests/test_api_metrics.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def test_list_metrics(api_client, auth_headers, mock_metadata_service):
    now = datetime.now()
    mock_metric = MagicMock()
    mock_metric.metric_name = "test_metric"
    mock_metric.display_name = "Test Metric"
    mock_metric.description = "A test metric"
    mock_metric.unit = "count"
    mock_metric.default_threshold = None
    mock_metric.default_critical_threshold = None
    mock_metric.is_active = True
    mock_metric.created_at = now
    mock_metric.updated_at = now
    mock_metadata_service.list_metrics.return_value = [mock_metric]
    response = api_client.get("/metrics/?active_only=true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["metric_name"] == "test_metric"


def test_get_metric_not_found(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.get_metric.return_value = None
    response = api_client.get("/metrics/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_create_metric(api_client, auth_headers, mock_metadata_service):
    now = datetime.now()
    mock_metadata_service.create_metric.return_value = "new_metric"
    mock_metric = MagicMock()
    mock_metric.metric_name = "new_metric"
    mock_metric.display_name = "New Metric"
    mock_metric.description = None
    mock_metric.unit = ""
    mock_metric.default_threshold = None
    mock_metric.default_critical_threshold = None
    mock_metric.is_active = True
    mock_metric.created_at = now
    mock_metric.updated_at = now
    mock_metadata_service.get_metric.return_value = mock_metric
    response = api_client.post(
        "/metrics/",
        json={
            "metric_name": "new_metric",
            "display_name": "New Metric",
            "is_active": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["metric_name"] == "new_metric"
