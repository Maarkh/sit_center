# tests/test_cookie_auth.py
"""httpOnly-cookie auth + double-submit CSRF protection."""
from datetime import timedelta


def _admin_token():
    from api.auth import create_access_token
    return create_access_token(
        data={
            "sub": "testadmin",
            "scopes": ["admin"],
            "tenant_id": "default",
            "roles": ["admin"],
            "permissions": ["read:metrics", "write:metrics", "admin:tenants", "admin:users"],
        },
        expires_delta=timedelta(minutes=30),
    )


def test_me_via_cookie(api_client):
    api_client.cookies.set("access_token", _admin_token())
    resp = api_client.get("/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "testadmin"
    assert "admin" in body["scopes"]


def test_me_requires_auth(api_client):
    api_client.cookies.clear()
    resp = api_client.get("/auth/me")
    assert resp.status_code in (401, 403)


def test_csrf_blocks_cookie_post_without_token(api_client):
    api_client.cookies.set("access_token", _admin_token())
    api_client.cookies.set("csrf_token", "abc123")
    # Cookie-authenticated unsafe request with no X-CSRF-Token → blocked.
    resp = api_client.post("/api/v1/metrics/", json={"metric_name": "x", "display_name": "X"})
    assert resp.status_code == 403
    assert "CSRF" in resp.json()["detail"]


def test_csrf_allows_cookie_post_with_matching_token(api_client):
    api_client.cookies.set("access_token", _admin_token())
    api_client.cookies.set("csrf_token", "abc123")
    resp = api_client.post(
        "/api/v1/metrics/",
        json={"metric_name": "csrf_ok_metric", "display_name": "X"},
        headers={"X-CSRF-Token": "abc123"},
    )
    # CSRF passed → not the CSRF 403 (route may 2xx/4xx/5xx, just not blocked by CSRF).
    assert resp.status_code != 403


def test_bearer_post_exempt_from_csrf(api_client, auth_headers):
    api_client.cookies.clear()
    resp = api_client.post(
        "/api/v1/metrics/",
        json={"metric_name": "y", "display_name": "Y"},
        headers=auth_headers,
    )
    # Bearer client (no auth cookie) is not subject to CSRF.
    assert resp.status_code != 403


def test_logout_clears_cookies(api_client):
    resp = api_client.post("/auth/logout")
    assert resp.status_code == 200
    # delete_cookie emits an expiring Set-Cookie for access_token.
    assert "access_token=" in resp.headers.get("set-cookie", "")
