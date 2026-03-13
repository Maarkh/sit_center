# tests/test_latest_by_region.py
"""Tests for the /data/latest-by-region endpoint."""
from unittest.mock import patch, MagicMock


class TestLatestByRegion:
    @patch("api.routes.data.get_engine")
    def test_requires_auth(self, mock_engine, api_client):
        resp = api_client.get("/data/latest-by-region?metric_name=cpu_usage")
        assert resp.status_code in (401, 403)

    @patch("api.routes.data.get_engine")
    def test_returns_region_values(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = [
            {"region": "Moscow", "value": 75.5},
            {"region": "SPb", "value": 42.3},
        ]

        resp = api_client.get(
            "/data/latest-by-region?metric_name=cpu_usage",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["region"] == "Moscow"
        assert data[0]["value"] == 75.5

    @patch("api.routes.data.get_engine")
    def test_empty_result(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get(
            "/data/latest-by-region?metric_name=nonexistent",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_invalid_metric_name(self, api_client, auth_headers):
        resp = api_client.get(
            "/data/latest-by-region?metric_name=drop;table",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_missing_metric_name(self, api_client, auth_headers):
        resp = api_client.get(
            "/data/latest-by-region",
            headers=auth_headers,
        )
        assert resp.status_code == 422
