# tests/test_health.py
"""Tests for the /health endpoint with dependency checks."""
from unittest.mock import patch, MagicMock


class TestHealth:
    def test_health_ok_when_all_deps_up(self, api_client, mock_redis):
        """Health returns ok when DB and Redis are available."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.database.get_engine", return_value=mock_engine), \
             patch("config.get_redis", return_value=mock_redis):
            resp = api_client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "situational-center-api"
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert data["checks"]["database"]["status"] == "ok"
        assert data["checks"]["redis"]["status"] == "ok"

    def test_health_degraded_when_db_down(self, api_client, mock_redis):
        """Health returns degraded (503) when DB is unreachable."""
        with patch("core.database.get_engine", side_effect=Exception("connection refused")), \
             patch("config.get_redis", return_value=mock_redis):
            resp = api_client.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"]["status"] == "error"
        assert data["checks"]["redis"]["status"] == "ok"

    def test_health_degraded_when_redis_down(self, api_client):
        """Health returns degraded (503) when Redis is unreachable."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.database.get_engine", return_value=mock_engine), \
             patch("config.get_redis", side_effect=Exception("redis down")):
            resp = api_client.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"]["status"] == "ok"
        assert data["checks"]["redis"]["status"] == "error"

    def test_health_no_auth_required(self, api_client, mock_redis):
        """Health endpoint should be accessible without authentication."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.database.get_engine", return_value=mock_engine), \
             patch("config.get_redis", return_value=mock_redis):
            resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_health_includes_latency(self, api_client, mock_redis):
        """Health response includes latency_ms for successful checks."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.database.get_engine", return_value=mock_engine), \
             patch("config.get_redis", return_value=mock_redis):
            resp = api_client.get("/health")

        data = resp.json()
        assert "latency_ms" in data["checks"]["database"]
        assert "latency_ms" in data["checks"]["redis"]
        assert isinstance(data["checks"]["database"]["latency_ms"], (int, float))
