# tests/test_frontend_errors.py
"""Tests for the /api/v1/frontend-errors endpoint."""


class TestFrontendErrors:
    def test_accepts_error_report(self, api_client):
        resp = api_client.post(
            "/api/v1/frontend-errors",
            json={
                "message": "TypeError: Cannot read property 'x' of undefined",
                "stack": "at Component (app.js:42)",
                "url": "https://sitcenter.example.com/dashboard",
                "timestamp": "2026-03-13T12:00:00Z",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_accepts_empty_body(self, api_client):
        resp = api_client.post(
            "/api/v1/frontend-errors",
            json={},
        )
        assert resp.status_code == 200

    def test_accepts_malformed_body(self, api_client):
        resp = api_client.post(
            "/api/v1/frontend-errors",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200

    def test_no_auth_required(self, api_client):
        """Frontend errors should be accepted without auth (error might be auth failure)."""
        resp = api_client.post(
            "/api/v1/frontend-errors",
            json={"message": "auth failed"},
        )
        assert resp.status_code == 200
