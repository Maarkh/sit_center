# tests/test_security.py
import pytest
from unittest.mock import patch
from core.metadata_service import MetricDTO


def test_sql_injection_protection(api_client, auth_headers):
    """Проверка защиты от SQL injection"""
    mock_metrics = [MetricDTO(metric_name="api_latency_p99", display_name="Latency", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "api_latency_p99",
                "start": 1234567890,
                "end": 1234567900,
                "step": "1s; DROP TABLE canonical_metrics; --"
            },
            headers=auth_headers,
        )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "step" in detail.lower()


def test_rate_limiting(api_client):
    """Проверка rate limiting"""
    rate_limit_hit = False

    for i in range(20):
        response = api_client.post("/token", data={"username": "test", "password": "test"})
        if response.status_code == 429:
            rate_limit_hit = True
            break

    assert rate_limit_hit, "Rate limiting should have been triggered"


def test_metric_whitelist(api_client, auth_headers):
    """Проверка whitelist метрик"""
    mock_metrics = [MetricDTO(metric_name="cpu_usage", display_name="CPU", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": "malicious_metric",
                "start": 1234567890,
                "end": 1234567900,
                "step": "1m"
            },
            headers=auth_headers,
        )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_sql_injection_dimensions(api_client, auth_headers):
    """Тест защиты от SQL injection в dimensions"""
    mock_metrics = [MetricDTO(metric_name="api_latency_p99", display_name="Latency", is_active=True)]
    with patch("core.metadata_service.metadata_service") as mock_ms:
        mock_ms.list_metrics.return_value = mock_metrics
        response = api_client.get(
            "/data/prometheus/api/v1/query_range",
            params={
                "query": 'api_latency_p99{region="x";DROP TABLE--"}',
                "start": 1234567890,
                "end": 1234567900,
                "step": "1m"
            },
            headers=auth_headers,
        )
    # Should be 400 Bad Request, not 500 or 200
    assert response.status_code == 400


def test_secret_masking_in_logs():
    """Убедимся, что секреты не попадают в логи"""
    from config import mask_secrets
    result = mask_secrets("redis://:super_secret_pass@localhost:6379")
    assert "super_secret_pass" not in result
    assert "***" in result
