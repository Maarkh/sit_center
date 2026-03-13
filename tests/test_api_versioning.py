# tests/test_api_versioning.py
"""Test that API v1 prefix routes work alongside legacy routes."""
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_metadata_service():
    with patch("api.routes.metrics.get_metadata_service") as mock:
        service = MagicMock()
        mock.return_value = service
        service.list_metrics.return_value = []
        yield service


class TestApiVersioning:
    def test_health_no_prefix(self, api_client, mock_redis):
        with patch("core.database.get_engine") as mock_engine:
            engine = MagicMock()
            mock_engine.return_value = engine
            conn = MagicMock()
            engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
            engine.connect.return_value.__exit__ = MagicMock(return_value=False)

            resp = api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_metrics_v1_prefix(self, api_client, auth_headers, mock_metadata_service):
        resp = api_client.get("/api/v1/metrics/", headers=auth_headers)
        assert resp.status_code == 200

    def test_metrics_legacy_prefix(self, api_client, auth_headers, mock_metadata_service):
        resp = api_client.get("/metrics/", headers=auth_headers)
        assert resp.status_code == 200

    @patch("api.routes.alerts.get_engine")
    def test_alerts_v1_prefix(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/api/v1/alerts/", headers=auth_headers)
        assert resp.status_code == 200
