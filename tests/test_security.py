# tests/test_security.py
import pytest
from fastapi.testclient import TestClient
from api.main import app
from config import logger
import time

client = TestClient(app)

def test_sql_injection_protection():
    """Проверка защиты от SQL injection"""
    # Попытка SQL injection в step
    response = client.get(
        "/data/prometheus/api/v1/query_range",
        params={
            "query": "api_latency_p99",
            "start": 1234567890,
            "end": 1234567900,
            "step": "1s; DROP TABLE canonical_metrics; --"
        }
    )
    assert response.status_code == 400
    assert "Invalid step" in response.json()["detail"]

def test_rate_limiting():
    """Проверка rate limiting"""
    rate_limit_hit = False
    
    # Отправляем запросы до срабатывания rate limit
    for i in range(20):
        response = client.post("/token", data={"username": "test", "password": "test"})
        if response.status_code == 429:
            rate_limit_hit = True
            break
        time.sleep(0.05)  # Небольшая задержка
    
    assert rate_limit_hit, "Rate limiting should have been triggered"
    
    # Проверяем, что после ожидания можно снова делать запросы
    time.sleep(60)  # Ждём сброс rate limit
    response = client.post("/token", data={"username": "test", "password": "test"})
    assert response.status_code in [200, 400, 401]

def test_metric_whitelist():
    """Проверка whitelist метрик"""
    response = client.get(
        "/data/prometheus/api/v1/query_range",
        params={
            "query": "malicious_metric",
            "start": 1234567890,
            "end": 1234567900,
            "step": "1m"
        }
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
def test_sql_injection_dimensions():
    """Тест защиты от SQL injection в dimensions"""
    response = client.get(
        "/data/prometheus/api/v1/query_range",
        params={
            "query": 'api_latency_p99{region="x";DROP TABLE--"}',
            "start": 1234567890,
            "end": 1234567900,
            "step": "1m"
        }
    )
    # Должен быть 400 Bad Request, а не 500 или 200
    assert response.status_code == 400
    assert "Invalid dimension key" in response.json()["detail"] or "forbidden characters" in response.text


def test_secret_masking_in_logs():
    """Убедимся, что секреты не попадают в логи"""
    import io
    from contextlib import redirect_stderr
    
    captured = io.StringIO()
    with redirect_stderr(captured):
        try:
            # Имитация ошибки подключения с паролем
            raise ConnectionError("redis://:super_secret_pass@localhost:6379")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
    
    log_output = captured.getvalue()
    assert "super_secret_pass" not in log_output
    assert "***" in log_output