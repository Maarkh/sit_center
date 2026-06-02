# tests/conftest.py
import os
os.environ["TESTING"] = "1"
# Auth cookies over http (TestClient) — the cookie jar won't replay Secure cookies
# on http, which would break cookie-auth tests.
os.environ.setdefault("COOKIE_SECURE", "false")

import pytest
import fakeredis
from unittest.mock import patch
from celery_app import celery_app


@pytest.fixture(autouse=True, scope="session")
def celery_eager():
    celery_app.conf.update(task_always_eager=True)
    yield


@pytest.fixture()
def fake_redis_instance():
    """A standalone fakeredis instance for direct use in tests."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True)
def mock_redis(fake_redis_instance):
    """Patch get_redis / get_cache globally so no real Redis is needed."""
    with patch("config.get_redis", return_value=fake_redis_instance), \
         patch("config.get_cache", return_value=fake_redis_instance):
        yield fake_redis_instance


@pytest.fixture()
def api_client():
    """FastAPI TestClient with mocked dependencies."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture()
def auth_headers():
    """Return valid Authorization headers for admin user."""
    from api.auth import create_access_token
    from datetime import timedelta
    token = create_access_token(
        data={
            "sub": "testadmin",
            "scopes": ["admin"],
            "tenant_id": "default",
            "roles": ["admin"],
            "permissions": [
                "read:metrics", "write:metrics", "read:rules", "write:rules",
                "read:alerts", "write:alerts", "read:ml", "write:ml",
                "admin:tenants", "admin:users", "read:audit",
            ],
        },
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def viewer_auth_headers():
    """Return valid Authorization headers for viewer user (read-only)."""
    from api.auth import create_access_token
    from datetime import timedelta
    token = create_access_token(
        data={
            "sub": "testviewer",
            "scopes": [],
            "tenant_id": "default",
            "roles": ["viewer"],
            "permissions": ["read:metrics", "read:rules", "read:alerts"],
        },
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}
