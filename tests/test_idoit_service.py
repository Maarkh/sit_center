# tests/test_idoit_service.py
"""Tests for i-doit service — push/pull operations."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_engine():
    with patch("core.idoit_service.get_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
        engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        yield engine, conn


class TestIsEnabled:
    def test_enabled_when_both_set(self):
        from core.idoit_service import is_enabled
        with patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = "http://idoit/api"
            s.I_DOIT_API_KEY = "key123"
            assert is_enabled() is True

    def test_disabled_when_no_url(self):
        from core.idoit_service import is_enabled
        with patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = ""
            s.I_DOIT_API_KEY = "key123"
            assert is_enabled() is False

    def test_disabled_when_no_key(self):
        from core.idoit_service import is_enabled
        with patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = "http://idoit/api"
            s.I_DOIT_API_KEY = ""
            assert is_enabled() is False


class TestStatusMapping:
    def test_status_to_idoit(self):
        from core.idoit_service import STATUS_TO_IDOIT
        assert STATUS_TO_IDOIT["new"] == "1"
        assert STATUS_TO_IDOIT["resolved"] == "3"
        assert STATUS_TO_IDOIT["closed"] == "4"

    def test_status_from_idoit(self):
        from core.idoit_service import STATUS_FROM_IDOIT
        assert STATUS_FROM_IDOIT["1"] == "new"
        assert STATUS_FROM_IDOIT["3"] == "resolved"

    def test_priority_mapping(self):
        from core.idoit_service import PRIORITY_TO_IDOIT, PRIORITY_FROM_IDOIT
        assert PRIORITY_TO_IDOIT["critical"] == "1"
        assert PRIORITY_FROM_IDOIT["1"] == "critical"


class TestPushIncidentCreate:
    def test_skips_when_disabled(self, mock_engine):
        from core.idoit_service import push_incident_create
        with patch("core.idoit_service.is_enabled", return_value=False):
            result = push_incident_create(1)
            assert result is None

    @patch("core.idoit_service.requests.post")
    def test_creates_incident_success(self, mock_post, mock_engine):
        engine, conn = mock_engine
        conn.execute.return_value.mappings.return_value.first.return_value = {
            "id": 1,
            "alert_message": "Test alert",
            "description": None,
            "metric": "cpu_usage",
            "region": "RU-MOW",
            "value": "95",
            "priority": "critical",
            "assigned_to": None,
            "status": "new",
        }

        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {
            "result": {"id": "42", "objectID": "42"}
        }

        from core.idoit_service import push_incident_create
        with patch("core.idoit_service.is_enabled", return_value=True), \
             patch("core.idoit_service.settings") as s:
            s.I_DOIT_API_URL = "http://idoit/api"
            s.I_DOIT_API_KEY = "key123"
            result = push_incident_create(1)
            assert result == "42"


class TestPullStatusUpdate:
    def test_pull_valid_status(self, mock_engine):
        engine, conn = mock_engine
        from core.idoit_service import pull_status_update

        with patch("core.idoit_service._log_sync"):
            pull_status_update(1, "3")  # 3 = resolved

        # Should have executed an UPDATE
        conn.execute.assert_called()

    def test_pull_unknown_status_ignored(self, mock_engine):
        engine, conn = mock_engine
        from core.idoit_service import pull_status_update

        with patch("core.idoit_service._log_sync"):
            pull_status_update(1, "99")

        # begin() should not be called for unknown status
        engine.begin.assert_not_called()
