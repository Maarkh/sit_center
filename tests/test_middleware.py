# tests/test_middleware.py
"""Tests for middleware: request ID injection and rate limiting."""
from unittest.mock import patch, MagicMock


class TestRequestId:
    def test_response_has_request_id(self, api_client, mock_redis):
        """Every response should include X-Request-ID header."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.database.get_engine", return_value=mock_engine), \
             patch("config.get_redis", return_value=mock_redis):
            resp = api_client.get("/health")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) > 0

    def test_propagates_incoming_request_id(self, api_client, mock_redis):
        """If client sends X-Request-ID, it should be echoed back."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        with patch("core.database.get_engine", return_value=mock_engine), \
             patch("config.get_redis", return_value=mock_redis):
            resp = api_client.get("/health", headers={"X-Request-ID": "test-req-123"})
        assert resp.headers["x-request-id"] == "test-req-123"


class TestRateLimiting:
    def test_token_endpoint_has_rate_limit(self, api_client):
        """POST /token should return 429 after exceeding rate limit."""
        # First 5 requests should work (even if auth fails)
        for _ in range(5):
            api_client.post("/token", data={"username": "x", "password": "x"})

        # 6th request should be rate-limited
        resp = api_client.post("/token", data={"username": "x", "password": "x"})
        assert resp.status_code == 429
