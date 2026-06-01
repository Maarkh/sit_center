# tests/test_rules_api.py
"""Tests for rules API: CRUD, RBAC, audit logging."""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def _make_rule(rule_id=None, is_active=True):
    from datetime import datetime
    mock = MagicMock()
    mock.id = rule_id or uuid4()
    mock.name = "test_rule"
    mock.description = "Test rule description"
    mock.condition = {"expr": "cpu > 90", "for": "1m", "eval": "1m"}
    mock.labels = {"severity": "critical"}
    mock.actions = [{"type": "notify", "config": {"channel": "telegram"}}]
    mock.is_active = is_active
    mock.created_at = datetime.now()
    mock.updated_at = datetime.now()
    return mock


class TestListRules:
    def test_list_active_rules(self, api_client, auth_headers, mock_metadata_service):
        rule = _make_rule()
        mock_metadata_service.list_active_rules.return_value = [rule]

        resp = api_client.get("/rules/?active_only=true", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "test_rule"

    def test_viewer_can_read_rules(self, api_client, viewer_auth_headers, mock_metadata_service):
        mock_metadata_service.list_active_rules.return_value = []
        resp = api_client.get("/rules/", headers=viewer_auth_headers)
        assert resp.status_code == 200


class TestCreateRule:
    @patch("api.routes.rules.log_audit")
    def test_create_rule(self, mock_audit, api_client, auth_headers, mock_metadata_service):
        import json as _json
        from datetime import datetime
        rule_id = uuid4()
        mock_metadata_service.create_rule.return_value = rule_id
        mock_metadata_service._deserialize_json.side_effect = lambda x: _json.loads(x) if isinstance(x, str) else x

        mock_engine = MagicMock()
        mock_metadata_service._get_engine.return_value = mock_engine
        conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.mappings.return_value.first.return_value = {
            "id": rule_id,
            "name": "new_rule",
            "description": "desc",
            "condition": '{"expr": "cpu > 90", "for": "1m", "eval": "1m"}',
            "labels": '{"env": "prod"}',
            "actions": '[{"type": "notify", "config": {"channel": "telegram"}}]',
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        resp = api_client.post(
            "/rules/",
            json={
                "name": "new_rule",
                "description": "desc",
                "condition": {"expr": "cpu > 90", "for": "1m", "eval": "1m"},
                "labels": {"env": "prod"},
                "actions": [{"type": "notify", "config": {"channel": "telegram"}}],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

    def test_viewer_cannot_create_rule(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/rules/",
            json={
                "name": "test",
                "condition": {},
                "labels": {},
                "actions": {},
            },
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteRule:
    @patch("api.routes.rules.log_audit")
    def test_delete_rule(self, mock_audit, api_client, auth_headers, mock_metadata_service):
        rule_id = uuid4()
        mock_engine = MagicMock()
        mock_metadata_service._get_engine.return_value = mock_engine
        conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        result = MagicMock()
        result.rowcount = 1
        conn.execute.return_value = result

        resp = api_client.delete(f"/rules/{rule_id}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_nonexistent_rule(self, api_client, auth_headers, mock_metadata_service):
        rule_id = uuid4()
        mock_engine = MagicMock()
        mock_metadata_service._get_engine.return_value = mock_engine
        conn = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        result = MagicMock()
        result.rowcount = 0
        conn.execute.return_value = result

        resp = api_client.delete(f"/rules/{rule_id}", headers=auth_headers)
        assert resp.status_code == 404
