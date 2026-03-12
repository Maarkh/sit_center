# tests/test_ml_configs_api.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from uuid import uuid4


@pytest.fixture
def mock_metadata_service():
    from api.main import app
    from api.dependencies import get_metadata_service
    service = MagicMock()
    app.dependency_overrides[get_metadata_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_metadata_service, None)


def _make_config(config_id=None, name="test-config"):
    m = MagicMock()
    m.id = config_id or uuid4()
    m.name = name
    m.metric_name = "cpu_usage"
    m.group_by = ["region"]
    m.methods = ["prophet"]
    m.method_params = {}
    m.retrain_schedule = "0 3 * * *"
    m.auto_alert = True
    m.alert_severity = "warning"
    m.is_active = True
    m.created_at = datetime.now()
    m.updated_at = datetime.now()
    return m


def test_list_ml_configs(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_active_ml_configs.return_value = [_make_config()]
    response = api_client.get("/ml/configs/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-config"


def test_list_ml_configs_all(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_all_ml_configs.return_value = [_make_config()]
    response = api_client.get("/ml/configs/?active_only=false", headers=auth_headers)
    assert response.status_code == 200
    mock_metadata_service.list_all_ml_configs.assert_called_once()


def test_get_ml_config(api_client, auth_headers, mock_metadata_service):
    cfg_id = uuid4()
    mock_metadata_service.list_active_ml_configs.return_value = [_make_config(cfg_id)]
    response = api_client.get(f"/ml/configs/{cfg_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "test-config"


def test_get_ml_config_not_found(api_client, auth_headers, mock_metadata_service):
    mock_metadata_service.list_active_ml_configs.return_value = []
    response = api_client.get(f"/ml/configs/{uuid4()}", headers=auth_headers)
    assert response.status_code == 404


def test_create_ml_config(api_client, auth_headers, mock_metadata_service):
    cfg_id = uuid4()
    mock_metadata_service.create_ml_config.return_value = cfg_id
    mock_metadata_service.list_active_ml_configs.return_value = [_make_config(cfg_id, "new-cfg")]

    response = api_client.post(
        "/ml/configs/",
        json={
            "name": "new-cfg",
            "metric_name": "cpu_usage",
            "methods": ["prophet"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "new-cfg"


def test_delete_ml_config(api_client, auth_headers, mock_metadata_service):
    cfg_id = uuid4()
    mock_engine = MagicMock()
    conn = MagicMock()
    result = MagicMock()
    result.rowcount = 1
    conn.execute.return_value = result
    mock_engine.begin.return_value.__enter__ = lambda s: conn
    mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)
    mock_metadata_service._get_engine.return_value = mock_engine

    response = api_client.delete(f"/ml/configs/{cfg_id}", headers=auth_headers)
    assert response.status_code == 204


def test_ml_configs_require_auth(api_client):
    response = api_client.get("/ml/configs/")
    assert response.status_code == 401
