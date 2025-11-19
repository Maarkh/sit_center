# tests/integration/test_end_to_end.py
from fastapi.testclient import TestClient
from sqlalchemy import text
from api.main import app
from core.notifications import notify
from unittest.mock import patch
from core.database import get_engine

client = TestClient(app)

def test_webhook_to_db_to_api():
    # 1. Постим в webhook
    resp = client.post("/webhooks/grafana", json={
        "title": "Test",
        "message": "OK",
        "status": "firing"
    })
    assert resp.status_code == 200

    # 2. Ждём Celery (в тестах — вызываем напрямую)
    from tasks import run_alerts_check_task
    run_alerts_check_task() # type: ignore

    # 3. Проверяем, что запись появилась в canonical_metrics
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT metric_name, value FROM canonical_metrics
            WHERE metric_name = 'grafana_test' LIMIT 1
        """)).first()
        assert row is not None

    # 4. Проверяем API
    resp = client.post("/data/query", json={
        "metric_name": "grafana_test",
        "limit": 1
    })
    assert resp.status_code == 200
    assert len(resp.json()["points"]) > 0