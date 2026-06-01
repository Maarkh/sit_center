# tests/test_auth_oidc.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.responses import RedirectResponse
from config import settings


# --- Disabled paths (OIDC_ENABLED=false) ---

def test_oidc_login_disabled(api_client):
    response = api_client.get("/auth/login/oidc", follow_redirects=False)
    assert response.status_code == 501
    assert "OIDC not enabled" in response.json()["detail"]


def test_oidc_callback_disabled(api_client):
    response = api_client.get("/auth/callback/oidc")
    assert response.status_code == 501
    assert "OIDC not enabled" in response.json()["detail"]


# --- Enabled flow (OIDC_ENABLED=true, oauth client mocked) ---

def _mock_engine():
    """Engine whose begin()/connect() yield a conn returning no DB rows."""
    engine = MagicMock()
    conn = MagicMock()
    engine.begin.return_value.__enter__ = MagicMock(return_value=conn)
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.mappings.return_value.first.return_value = None
    return engine


def test_oidc_login_enabled_redirects(api_client):
    mock_oauth = MagicMock()
    mock_oauth.keycloak.authorize_redirect = AsyncMock(
        return_value=RedirectResponse(
            "https://keycloak.example/realms/sit-center/protocol/openid-connect/auth"
        )
    )
    with patch.object(settings, "OIDC_ENABLED", True), \
         patch("core.oidc_auth.oauth", mock_oauth):
        resp = api_client.get("/auth/login/oidc", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "keycloak" in resp.headers["location"]
    mock_oauth.keycloak.authorize_redirect.assert_awaited_once()


def test_oidc_callback_success_issues_token(api_client):
    token = {
        "userinfo": {
            "preferred_username": "alice",
            "email": "alice@example.com",
            "sub": "kc-1",
        },
        "access_token_claims": {"realm_access": {"roles": ["viewer"]}},
    }
    mock_oauth = MagicMock()
    mock_oauth.keycloak.authorize_access_token = AsyncMock(return_value=token)
    with patch.object(settings, "OIDC_ENABLED", True), \
         patch("core.oidc_auth.oauth", mock_oauth), \
         patch("core.database.get_engine", return_value=_mock_engine()), \
         patch("core.audit.log_audit"):
        resp = api_client.get("/auth/callback/oidc", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "token=" in resp.headers["location"]


def test_oidc_callback_auth_failure(api_client):
    mock_oauth = MagicMock()
    mock_oauth.keycloak.authorize_access_token = AsyncMock(side_effect=Exception("bad code"))
    with patch.object(settings, "OIDC_ENABLED", True), \
         patch("core.oidc_auth.oauth", mock_oauth):
        resp = api_client.get("/auth/callback/oidc")
    assert resp.status_code == 401
    assert "OIDC authentication failed" in resp.json()["detail"]


def test_oidc_callback_no_username(api_client):
    token = {"userinfo": {"email": "noone@example.com"}}  # no preferred_username / sub
    mock_oauth = MagicMock()
    mock_oauth.keycloak.authorize_access_token = AsyncMock(return_value=token)
    with patch.object(settings, "OIDC_ENABLED", True), \
         patch("core.oidc_auth.oauth", mock_oauth):
        resp = api_client.get("/auth/callback/oidc")
    assert resp.status_code == 401
    assert "No username" in resp.json()["detail"]
