# tests/test_incidents.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_db_engine():
    with patch("api.routes.incidents.get_engine") as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield engine


def _make_incident_row(overrides=None):
    row = {
        "id": 1,
        "alert_message": "High latency",
        "metric": "api_latency_p99",
        "region": "RU-MOW",
        "value": "500",
        "priority": "critical",
        "status": "new",
        "detected_at": datetime.now(timezone.utc),
        "assigned_to": None,
        "started_at": None,
        "resolved_at": None,
        "closed_at": None,
        "description": None,
        "alert_event_id": None,
        "response_deadline": None,
        "resolution_deadline": None,
        "response_breached": False,
        "resolution_breached": False,
        "escalation_level": 0,
        "last_escalated_at": None,
        "external_id": None,
        "external_system": None,
        "external_url": None,
    }
    if overrides:
        row.update(overrides)
    return row


def _setup_conn(engine, return_value):
    """Set up context-managed connection mock."""
    conn = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    return conn


class TestListIncidents:
    def test_list_incidents_empty(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, [])
        conn.execute.return_value.scalar.return_value = 0
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/incidents/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_incidents_with_filters(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, [])
        conn.execute.return_value.scalar.return_value = 1
        conn.execute.return_value.mappings.return_value.all.return_value = [
            _make_incident_row({"status": "in_progress"})
        ]

        resp = api_client.get(
            "/incidents/?status=in_progress&priority=critical",
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_list_incidents_breached_filter(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, [])
        conn.execute.return_value.scalar.return_value = 0
        conn.execute.return_value.mappings.return_value.all.return_value = []

        resp = api_client.get("/incidents/?breached=true", headers=auth_headers)
        assert resp.status_code == 200


class TestCreateIncident:
    @patch("api.routes.incidents.log_audit")
    def test_create_incident(self, mock_audit, api_client, auth_headers, mock_db_engine):
        row = _make_incident_row()
        conn = _setup_conn(mock_db_engine, row)
        conn.execute.return_value.mappings.return_value.first.return_value = row

        with patch("core.sla_service.apply_sla_to_incident"), \
             patch("core.idoit_service.push_incident_create", return_value=None):
            resp = api_client.post(
                "/incidents/",
                json={
                    "alert_message": "High latency",
                    "metric": "api_latency_p99",
                    "region": "RU-MOW",
                    "priority": "critical",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        assert resp.json()["alert_message"] == "High latency"


class TestGetIncident:
    def test_get_incident_found(self, api_client, auth_headers, mock_db_engine):
        row = _make_incident_row()
        conn = _setup_conn(mock_db_engine, row)
        conn.execute.return_value.mappings.return_value.first.return_value = row

        resp = api_client.get("/incidents/1", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_incident_not_found(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.mappings.return_value.first.return_value = None

        resp = api_client.get("/incidents/999", headers=auth_headers)
        assert resp.status_code == 404


class TestStatusTransitions:
    def test_valid_transition(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        # First call: check current status
        conn.execute.return_value.mappings.return_value.first.side_effect = [
            {"status": "new"},  # SELECT status
            _make_incident_row({"status": "in_progress"}),  # SELECT after update
        ]

        with patch("api.routes.incidents.log_audit"), \
             patch("core.idoit_service.push_status_update"):
            resp = api_client.patch(
                "/incidents/1/status",
                json={"status": "in_progress"},
                headers=auth_headers,
            )
        assert resp.status_code == 200

    def test_invalid_transition_closed_to_new(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.mappings.return_value.first.return_value = {"status": "closed"}

        resp = api_client.patch(
            "/incidents/1/status",
            json={"status": "new"},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "Cannot transition" in resp.json()["detail"]


class TestAssignIncident:
    def test_assign_success(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.first.return_value = (1,)
        conn.execute.return_value.mappings.return_value.first.return_value = _make_incident_row(
            {"assigned_to": "ops-user"}
        )

        with patch("api.routes.incidents.log_audit"), \
             patch("core.idoit_service.push_assignment"):
            resp = api_client.patch(
                "/incidents/1/assign",
                json={"assigned_to": "ops-user"},
                headers=auth_headers,
            )
        assert resp.status_code == 200

    def test_assign_not_found(self, api_client, auth_headers, mock_db_engine):
        conn = _setup_conn(mock_db_engine, None)
        conn.execute.return_value.first.return_value = None

        resp = api_client.patch(
            "/incidents/1/assign",
            json={"assigned_to": "ops-user"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
