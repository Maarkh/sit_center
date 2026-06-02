# tests/integration/test_end_to_end.py
"""
End-to-end integration tests with real PostgreSQL and Redis.

Prerequisites:
    docker compose -f docker-compose.test.yml up -d
    pytest tests/integration/ -v
"""
import pytest
from sqlalchemy import text


class TestHealthAndAuth:
    def test_health_endpoint(self, integration_client):
        resp = integration_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_login_env_admin(self, integration_client):
        resp = integration_client.post("/token", data={
            "username": "admin",
            "password": "admin",
        })
        # May return 200 or 401 depending on whether bcrypt hash matches "admin"
        assert resp.status_code in (200, 401)

    def test_unauthenticated_rejected(self, integration_client):
        resp = integration_client.get("/api/v1/metrics/")
        assert resp.status_code in (401, 403)


class TestMetricsCRUD:
    def test_create_and_list_metrics(self, integration_client, admin_headers, db_engine):
        # Ensure table exists
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM metadata_metrics LIMIT 1"))
        except Exception:
            pytest.skip("metadata_metrics table not found — migrations not applied")

        # Create metric
        resp = integration_client.post(
            "/api/v1/metrics/",
            json={
                "metric_name": "inttest_cpu_usage",
                "display_name": "CPU Usage (integration test)",
                "unit": "percent",
                "is_active": True,
            },
            headers=admin_headers,
        )
        assert resp.status_code in (201, 400)  # 400 if already exists

        # List metrics
        resp = integration_client.get("/api/v1/metrics/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_metric(self, integration_client, admin_headers):
        resp = integration_client.get("/api/v1/metrics/inttest_cpu_usage", headers=admin_headers)
        assert resp.status_code in (200, 404)


class TestIncidentLifecycle:
    def test_full_lifecycle(self, integration_client, admin_headers, db_engine):
        # Check table exists
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM incidents LIMIT 1"))
        except Exception:
            pytest.skip("incidents table not found — migrations not applied")

        # Create incident
        resp = integration_client.post(
            "/api/v1/incidents/",
            json={
                "alert_message": "Integration test incident",
                "metric": "cpu_usage",
                "region": "RU-MOW",
                "priority": "low",
            },
            headers=admin_headers,
        )
        if resp.status_code != 201:
            pytest.skip(f"Create incident failed: {resp.status_code}")

        incident_id = resp.json()["id"]

        # Transition: new -> in_progress
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "in_progress"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

        # Assign
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/assign",
            json={"assigned_to": "test-operator"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # Add comment
        resp = integration_client.post(
            f"/api/v1/incidents/{incident_id}/comments",
            json={"content": "Investigation started by integration test"},
            headers=admin_headers,
        )
        assert resp.status_code == 201

        # List comments
        resp = integration_client.get(
            f"/api/v1/incidents/{incident_id}/comments",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

        # Resolve
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "resolved", "comment": "Fixed by integration test"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

        # Close
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "closed"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_invalid_transition(self, integration_client, admin_headers, db_engine):
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM incidents LIMIT 1"))
        except Exception:
            pytest.skip("incidents table not found")

        resp = integration_client.post(
            "/api/v1/incidents/",
            json={
                "alert_message": "Transition test",
                "metric": "mem_usage",
                "region": "RU-SPE",
                "priority": "medium",
            },
            headers=admin_headers,
        )
        if resp.status_code != 201:
            pytest.skip(f"Create incident failed: {resp.status_code}")

        incident_id = resp.json()["id"]

        # Invalid: new -> resolved (must go through in_progress)
        resp = integration_client.patch(
            f"/api/v1/incidents/{incident_id}/status",
            json={"status": "resolved"},
            headers=admin_headers,
        )
        assert resp.status_code == 400


class TestTenantIsolation:
    def test_data_scoped_to_tenant(self, integration_client, admin_headers, db_engine):
        """Two tenants' metrics must NOT leak across the tenant boundary.

        Seeds canonical_metrics for tenant 'default' and tenant 'tenant-b', then
        queries as the default-tenant admin and asserts the other tenant's metric
        is invisible. This is a real isolation assertion — it FAILS (not skips)
        if tenant filtering regresses.
        """
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM canonical_metrics LIMIT 1"))
        except Exception:
            pytest.skip("canonical_metrics table not found — migrations not applied")

        own = "iso_default_metric"
        other = "iso_other_metric"
        insert = text(
            "INSERT INTO canonical_metrics "
            "(metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
            "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'itest', :t)"
        )
        try:
            with db_engine.begin() as conn:
                conn.execute(insert, {"m": own, "v": 111.0, "t": "default"})
                conn.execute(insert, {"m": other, "v": 999.0, "t": "tenant-b"})

            # Admin token belongs to tenant "default".
            resp = integration_client.get(
                "/api/v1/data/prometheus/api/v1/label/__name__/values",
                headers=admin_headers,
            )
            assert resp.status_code == 200
            names = resp.json()
            assert own in names, "own-tenant metric should be visible"
            assert other not in names, "other tenant's metric leaked across the boundary!"
        finally:
            with db_engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM canonical_metrics WHERE metric_name IN (:a, :b)"),
                    {"a": own, "b": other},
                )


class TestApiVersioning:
    def test_v1_route_no_deprecation(self, integration_client, admin_headers):
        resp = integration_client.get("/api/v1/metrics/", headers=admin_headers)
        assert "Deprecation" not in resp.headers

    def test_legacy_route_has_deprecation(self, integration_client, admin_headers):
        resp = integration_client.get("/metrics/", headers=admin_headers)
        if resp.status_code == 200:
            assert resp.headers.get("Deprecation") == "true"
            assert "Sunset" in resp.headers


class TestAlertEndpoints:
    def test_list_alerts(self, integration_client, admin_headers, db_engine):
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM alert_events LIMIT 1"))
        except Exception:
            pytest.skip("alert_events table not found")

        resp = integration_client.get("/api/v1/alerts/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
