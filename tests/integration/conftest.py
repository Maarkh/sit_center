# tests/integration/conftest.py
"""
Integration test fixtures — connect to real PostgreSQL + Redis.

Start test infrastructure:
    docker compose -f docker-compose.test.yml up -d
Run integration tests:
    pytest tests/integration/ -v --tb=short
"""
import os
import pytest
import time

# Set env vars BEFORE importing application modules
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_pass")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5444")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6399")
os.environ.setdefault("REDIS_PASSWORD", "")
os.environ.setdefault("SECRET_KEY", "integration-test-secret")
os.environ.setdefault("ADMIN_USERNAME", "admin")
# bcrypt hash of "admin" (the password the admin_token fixture logs in with).
os.environ.setdefault("ADMIN_PASSWORD", "$2b$12$og87/j8zmULE7nd6EUpud.rS/8xpxmW5GaciRZBG.hkHQztviVeri")
os.environ.setdefault("I_DOIT_API_KEY", "test")
os.environ.setdefault("I_DOIT_API_URL", "http://localhost/api")
os.environ.setdefault("WEBHOOK_API_KEY", "test-key")
os.environ.setdefault("KAFKA_ENABLED", "false")
os.environ.setdefault("CLICKHOUSE_ENABLED", "false")
os.environ.setdefault("LDAP_ENABLED", "false")
os.environ.setdefault("OIDC_ENABLED", "false")


# Connection params come from env (set by the CI job to point at the service
# containers, or by docker-compose.test.yml defaults for local runs).
PG_HOST = os.environ.get("POSTGRES_SERVER", "localhost")
PG_PORT = int(os.environ.get("POSTGRES_PORT", "5444"))
PG_USER = os.environ.get("POSTGRES_USER", "test_user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "test_pass")
PG_DB = os.environ.get("POSTGRES_DB", "test_db")
RD_HOST = os.environ.get("REDIS_HOST", "localhost")
RD_PORT = int(os.environ.get("REDIS_PORT", "6399"))
DB_URL = os.environ.get("DATABASE_URL") or f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"


def _wait_for_pg(max_wait=30):
    """Block until PostgreSQL is ready."""
    import psycopg2
    start = time.time()
    while time.time() - start < max_wait:
        try:
            conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, dbname=PG_DB)
            conn.close()
            return True
        except Exception:
            time.sleep(0.5)
    pytest.skip(f"PostgreSQL not available at {PG_HOST}:{PG_PORT} — run docker compose -f docker-compose.test.yml up -d")


def _wait_for_redis(max_wait=15):
    """Block until Redis is ready."""
    import redis as r
    start = time.time()
    while time.time() - start < max_wait:
        try:
            client = r.Redis(host=RD_HOST, port=RD_PORT)
            client.ping()
            client.close()
            return True
        except Exception:
            time.sleep(0.5)
    pytest.skip(f"Redis not available at {RD_HOST}:{RD_PORT} — run docker compose -f docker-compose.test.yml up -d")


@pytest.fixture(scope="session", autouse=True)
def _wait_for_infra():
    _wait_for_pg()
    _wait_for_redis()


@pytest.fixture(scope="session")
def db_engine():
    from sqlalchemy import create_engine
    engine = create_engine(DB_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def real_redis():
    import redis as r
    client = r.Redis(host="localhost", port=6399, decode_responses=True)
    yield client
    client.flushdb()
    client.close()


@pytest.fixture(scope="session")
def integration_client():
    """FastAPI TestClient connected to real test DB."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_token(integration_client):
    """Get a real admin JWT token."""
    resp = integration_client.post("/token", data={
        "username": "admin",
        "password": "admin",
    })
    if resp.status_code != 200:
        pytest.skip(f"Cannot get admin token: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
