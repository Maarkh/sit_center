# tests/test_audit_api.py
from unittest.mock import patch, MagicMock
from datetime import datetime


def _mock_engine_with_rows(rows):
    engine = MagicMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    conn = MagicMock()
    conn.execute.return_value = result
    engine.connect.return_value.__enter__ = lambda s: conn
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


def test_get_audit_logs(api_client, auth_headers):
    rows = [
        {
            "id": 1,
            "username": "admin",
            "tenant_id": "default",
            "action": "create",
            "resource_type": "metric",
            "resource_id": "cpu_usage",
            "changes": {},
            "ip_address": "127.0.0.1",
            "timestamp": datetime.now(),
        }
    ]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.audit.get_engine", return_value=engine):
        response = api_client.get("/audit/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["action"] == "create"


def test_audit_logs_filter_by_action(api_client, auth_headers):
    engine = _mock_engine_with_rows([])
    with patch("api.routes.audit.get_engine", return_value=engine):
        response = api_client.get(
            "/audit/logs?action=login&resource_type=session",
            headers=auth_headers,
        )
    assert response.status_code == 200


def test_audit_logs_require_auth(api_client):
    response = api_client.get("/audit/logs")
    assert response.status_code == 401


def test_audit_logs_require_read_audit_permission(api_client, viewer_auth_headers):
    response = api_client.get("/audit/logs", headers=viewer_auth_headers)
    assert response.status_code == 403
