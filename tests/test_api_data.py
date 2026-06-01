# tests/test_api_data.py
from unittest.mock import patch, MagicMock
from core.metadata_service import MetricDTO


def test_prometheus_label_values_name(api_client, auth_headers):
    with patch("api.routes.data.get_engine") as mock_engine:
        conn = MagicMock()
        mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value = [("metric_a",), ("metric_b",)]

        response = api_client.get("/data/prometheus/api/v1/label/__name__/values", headers=auth_headers)
        assert response.status_code == 200
        assert "metric_a" in response.json()


def test_prometheus_label_values_forbidden_dimension(api_client, auth_headers):
    response = api_client.get("/data/prometheus/api/v1/label/forbidden_dim/values", headers=auth_headers)
    assert response.status_code == 403


def test_query_range_invalid_step(api_client, auth_headers):
    mock_metrics = [MetricDTO(metric_name="test_metric", display_name="Test", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "test_metric",
                "start": 1000000,
                "end": 1000100,
                "step": "invalid",
            },
            headers=auth_headers,
        )
    assert response.status_code == 400


def test_query_range_sql_injection_step(api_client, auth_headers):
    mock_metrics = [MetricDTO(metric_name="test_metric", display_name="Test", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "test_metric",
                "start": 1000000,
                "end": 1000100,
                "step": "1s; DROP TABLE--",
            },
            headers=auth_headers,
        )
    assert response.status_code == 400
