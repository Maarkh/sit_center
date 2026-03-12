# tests/test_data_routes.py
"""Tests for data query routes: Prometheus compat, analytics, and query endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from api.routes.data import _parse_duration, safe_jsonb_eq, validate_label_name
from fastapi import HTTPException


class TestParseDuration:
    def test_valid_seconds(self):
        assert _parse_duration("15s") == 15

    def test_valid_minutes(self):
        assert _parse_duration("5m") == 300

    def test_valid_hours(self):
        assert _parse_duration("2h") == 7200

    def test_valid_days(self):
        assert _parse_duration("1d") == 86400

    def test_invalid_format(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("abc")
        assert exc_info.value.status_code == 400

    def test_too_large_step(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("2d")
        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail

    def test_too_long_string(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("12345678901")
        assert exc_info.value.status_code == 400

    def test_zero_step(self):
        with pytest.raises(HTTPException) as exc_info:
            _parse_duration("0s")
        assert exc_info.value.status_code == 400


class TestValidateLabelName:
    def test_valid_label(self):
        assert validate_label_name("region") == "region"

    def test_valid_underscore_start(self):
        assert validate_label_name("_private") == "_private"

    def test_invalid_special_chars(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_label_name("region;DROP")
        assert exc_info.value.status_code == 400

    def test_too_long(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_label_name("a" * 51)
        assert exc_info.value.status_code == 400


class TestSafeJsonbEq:
    def test_valid_key_value(self):
        expr, params = safe_jsonb_eq("dimensions", "f0", "region", "Moscow")
        assert "key_f0" in params
        assert "val_f0" in params
        assert params["key_f0"] == "region"
        assert params["val_f0"] == "Moscow"

    def test_invalid_key_raises(self):
        with pytest.raises(Exception):
            safe_jsonb_eq("dimensions", "f0", "region;DROP", "Moscow")

    def test_forbidden_chars_in_value(self):
        with pytest.raises(HTTPException):
            safe_jsonb_eq("dimensions", "f0", "region", 'Mos"cow')


class TestPrometheusEndpoints:
    @patch("api.routes.data.get_engine")
    def test_label_values_requires_auth(self, mock_engine, api_client):
        resp = api_client.get("/data/prometheus/api/v1/label/__name__/values")
        assert resp.status_code in (401, 403)

    @patch("api.routes.data.get_engine")
    def test_label_values_with_auth(self, mock_engine, api_client, auth_headers):
        engine = MagicMock()
        mock_engine.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value = [("cpu_usage",), ("memory_used",)]

        resp = api_client.get(
            "/data/prometheus/api/v1/label/__name__/values",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    @patch("api.routes.data.get_engine")
    def test_disallowed_dimension_label(self, mock_engine, api_client, auth_headers):
        resp = api_client.get(
            "/data/prometheus/api/v1/label/secret_field/values",
            headers=auth_headers,
        )
        assert resp.status_code == 403
