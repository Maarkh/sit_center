# tests/test_admin_api.py
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import timedelta


def _tenant_admin_headers(tenant_id: str):
    """Admin token for a NON-platform tenant (to test the superadmin gate)."""
    from api.auth import create_access_token
    token = create_access_token(
        data={"sub": "tadmin", "scopes": ["admin"], "tenant_id": tenant_id,
              "roles": ["admin"], "permissions": ["admin:tenants", "admin:users"]},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


def test_tenant_admin_cannot_manage_tenants(api_client):
    # a tenant-B admin must not list/create platform tenants (H-1 superadmin gate)
    headers = _tenant_admin_headers("acme")
    assert api_client.get("/admin/tenants", headers=headers).status_code == 403
    assert api_client.post("/admin/tenants", json={"id": "x", "name": "X"}, headers=headers).status_code == 403


def _mock_engine_with_rows(rows):
    """Create a mock engine whose connect().execute() returns rows."""
    engine = MagicMock()
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    conn = MagicMock()
    conn.execute.return_value = result
    engine.connect.return_value.__enter__ = lambda s: conn
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


def _mock_engine_for_write(returning_row=None):
    """Create a mock engine whose begin().execute() returns a row (for INSERT RETURNING)."""
    engine = MagicMock()
    conn = MagicMock()
    if returning_row:
        result = MagicMock()
        result.mappings.return_value.first.return_value = returning_row
        conn.execute.return_value = result
    engine.begin.return_value.__enter__ = lambda s: conn
    engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    return engine


# --- Tenants ---

def test_list_tenants(api_client, auth_headers):
    rows = [{"id": "default", "name": "Default", "is_active": True}]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.admin.get_engine", return_value=engine):
        response = api_client.get("/admin/tenants", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "default"


def test_create_tenant(api_client, auth_headers):
    engine = _mock_engine_for_write()
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/tenants",
            json={"id": "new_tenant", "name": "New Tenant"},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["id"] == "new_tenant"


def test_create_tenant_invalid_id(api_client, auth_headers):
    response = api_client.post(
        "/admin/tenants",
        json={"id": "invalid tenant!", "name": "Bad"},
        headers=auth_headers,
    )
    assert response.status_code == 422


# --- Users ---

def test_list_users(api_client, auth_headers):
    uid = str(uuid4())
    rows = [
        {"id": uid, "username": "alice", "email": "alice@example.com",
         "tenant_id": "default", "is_active": True, "auth_provider": "local"}
    ]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.admin.get_engine", return_value=engine):
        response = api_client.get("/admin/users?tenant_id=default", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["username"] == "alice"


def test_create_user(api_client, auth_headers):
    uid = str(uuid4())
    row = {
        "id": uid, "username": "bob", "email": "bob@test.com",
        "tenant_id": "default", "is_active": True, "auth_provider": "local",
    }
    engine = _mock_engine_for_write(returning_row=row)
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/users",
            json={"username": "bob", "email": "bob@test.com"},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["username"] == "bob"


# --- Roles ---

def test_list_roles(api_client, auth_headers):
    rid = str(uuid4())
    rows = [
        {"id": rid, "name": "viewer", "tenant_id": "default",
         "permissions": ["read:metrics"], "description": "Read-only"}
    ]
    engine = _mock_engine_with_rows(rows)
    with patch("api.routes.admin.get_engine", return_value=engine):
        response = api_client.get("/admin/roles?tenant_id=default", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()[0]["name"] == "viewer"


def test_create_role(api_client, auth_headers):
    rid = str(uuid4())
    row = {
        "id": rid, "name": "editor", "tenant_id": "default",
        "permissions": ["read:metrics", "write:metrics"], "description": "Editor",
    }
    engine = _mock_engine_for_write(returning_row=row)
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/roles",
            json={"name": "editor", "permissions": ["read:metrics", "write:metrics"]},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["name"] == "editor"


# --- User-Role assignment ---

def test_assign_role(api_client, auth_headers):
    # the ownership check requires the user + role to be in the caller's tenant (default)
    engine = _mock_engine_for_write(returning_row={"ut": "default", "rt": "default"})
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.post(
            "/admin/user-roles",
            json={"user_id": str(uuid4()), "role_id": str(uuid4())},
            headers=auth_headers,
        )
    assert response.status_code == 201
    assert response.json()["status"] == "ok"


def test_unassign_role(api_client, auth_headers):
    engine = _mock_engine_for_write()
    with patch("api.routes.admin.get_engine", return_value=engine), \
         patch("api.routes.admin.log_audit"):
        response = api_client.request(
            "DELETE",
            "/admin/user-roles",
            json={"user_id": str(uuid4()), "role_id": str(uuid4())},
            headers=auth_headers,
        )
    assert response.status_code == 204


# --- Auth required ---

def test_admin_endpoints_require_auth(api_client):
    endpoints = ["/admin/tenants", "/admin/users", "/admin/roles"]
    for ep in endpoints:
        response = api_client.get(ep)
        assert response.status_code == 401, f"{ep} should require auth"


def test_admin_endpoints_require_admin_role(api_client, viewer_auth_headers):
    response = api_client.get("/admin/tenants", headers=viewer_auth_headers)
    assert response.status_code == 403
