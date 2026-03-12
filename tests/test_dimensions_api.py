# tests/test_dimensions_api.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def _make_dim(key="region", desc="Region dimension"):
    m = MagicMock()
    m.dimension_key = key
    m.description = desc
    m.allowed_values = ["RU-MOW", "RU-SPE"]
    m.is_required = False
    m.created_at = datetime.now()
    return m


def test_list_dimensions(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_dimensions.return_value = [_make_dim()]
    response = api_client.get("/dimensions/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["dimension_key"] == "region"


def test_get_dimension(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.get_dimension.return_value = _make_dim("service", "Service dim")
    response = api_client.get("/dimensions/service", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["dimension_key"] == "service"


def test_get_dimension_not_found(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.get_dimension.return_value = None
    response = api_client.get("/dimensions/nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_create_dimension(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.create_dimension.return_value = "env"
    mock_metadata_service.get_dimension.return_value = _make_dim("env", "Environment")

    response = api_client.post(
        "/dimensions/",
        json={"dimension_key": "env", "description": "Environment", "is_required": False},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["dimension_key"] == "env"


def test_create_dimension_invalid_key(api_client, auth_headers, mock_metadata_service):
    response = api_client.post(
        "/dimensions/",
        json={"dimension_key": "bad key!", "description": "Invalid"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_dimensions_require_auth(api_client):
    response = api_client.get("/dimensions/")
    assert response.status_code == 401
