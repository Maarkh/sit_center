# tests/test_api_metrics.py
import pytest
from unittest.mock import patch, MagicMock
from core.metadata_service import MetricDTO


@pytest.fixture
def mock_metadata_service():
    with patch("api.routes.metrics.get_metadata_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


def test_list_metrics(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_metrics.return_value = [
        MetricDTO(
            metric_name="test_metric",
            display_name="Test Metric",
            description="A test metric",
            unit="count",
            is_active=True,
        )
    ]
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
    mock_metadata_service.create_metric.return_value = "new_metric"
    mock_metadata_service.get_metric.return_value = MetricDTO(
        metric_name="new_metric",
        display_name="New Metric",
        is_active=True,
    )
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
