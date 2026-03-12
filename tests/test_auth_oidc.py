# tests/test_auth_oidc.py
import pytest
from unittest.mock import patch


def test_oidc_login_disabled(api_client):
    response = api_client.get("/auth/login/oidc", follow_redirects=False)
    assert response.status_code == 501
    assert "OIDC not enabled" in response.json()["detail"]


def test_oidc_callback_disabled(api_client):
    response = api_client.get("/auth/callback/oidc")
    assert response.status_code == 501
    assert "OIDC not enabled" in response.json()["detail"]
