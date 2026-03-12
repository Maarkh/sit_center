# tests/test_api_alerts.py
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone


@pytest.fixture
def mock_db_engine():
    with patch("api.routes.alerts.get_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield engine


def test_list_alerts_empty(api_client, auth_headers, mock_db_engine):
    conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    mock_db_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.all.return_value = []

    response = api_client.get("/alerts/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_alert_not_found(api_client, auth_headers, mock_db_engine):
    conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    mock_db_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.first.return_value = None

    alert_id = uuid4()
    response = api_client.get(f"/alerts/{alert_id}", headers=auth_headers)
    assert response.status_code == 404


def test_list_alerts_with_data(api_client, auth_headers, mock_db_engine):
    alert_id = uuid4()
    now = datetime.now(timezone.utc)
    row = {
        "id": alert_id,
        "rule_id": None,
        "ml_config_id": None,
        "metric_name": "complaints",
        "dimensions": {"region": "Moscow"},
        "value": 42.0,
        "event_time": now,
        "detected_at": now,
        "status": "firing",
        "sent": True,
        "fingerprint": "abc123",
    }
    conn = MagicMock()
    mock_db_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    mock_db_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.all.return_value = [row]

    response = api_client.get("/alerts/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["metric_name"] == "complaints"
