# tests/test_rbac.py
"""Test RBAC and tenant isolation across all route modules."""
import pytest
from unittest.mock import patch, MagicMock


class TestUnauthenticatedAccess:
    """All endpoints must reject requests without auth headers."""

    PROTECTED_ROUTES = [
        ("GET", "/alerts/"),
        ("GET", "/metrics/"),
        ("GET", "/rules/"),
        ("GET", "/dimensions/"),
        ("GET", "/ml/configs/"),
        ("GET", "/incidents/"),
        ("GET", "/data/"),
        ("GET", "/data/prometheus/api/v1/label/__name__/values"),
        ("GET", "/audit/logs"),
    ]

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
    def test_no_auth_returns_401(self, api_client, method, path):
        resp = api_client.request(method, path)
        assert resp.status_code in (401, 403), f"{method} {path} returned {resp.status_code}"


class TestViewerPermissions:
    """Viewer users should only have read access."""

    @patch("api.routes.alerts.get_engine")
    def test_viewer_can_read_alerts(self, mock_engine, api_client, viewer_auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/alerts/", headers=viewer_auth_headers)
        assert resp.status_code == 200

    def test_viewer_cannot_suppress_alert(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/alerts/00000000-0000-0000-0000-000000000001/suppress",
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_metric(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/metrics/",
            json={"metric_name": "test", "display_name": "Test", "is_active": True},
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_rule(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/rules/",
            json={"name": "test", "condition": {}, "labels": {}, "actions": {}},
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_write_ml_config(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/ml/configs/",
            json={
                "metric_name": "test",
                "method": "prophet",
                "params": {},
                "is_active": True,
            },
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_incident(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/incidents/",
            json={
                "alert_message": "test",
                "metric": "test_metric",
                "region": "RU-MOW",
                "priority": "low",
            },
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403


class TestTenantIsolation:
    """Ensure tenant_id is passed to queries from auth context."""

    @patch("api.routes.alerts.get_engine")
    def test_alert_query_includes_tenant_id(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        api_client.get("/alerts/", headers=auth_headers)

        # Verify the SQL call included tenant_id param
        call_args = conn.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("parameters", {})
        assert "tenant_id" in params or "tenant_id" in str(call_args)
