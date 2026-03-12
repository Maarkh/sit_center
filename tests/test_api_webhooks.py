# tests/test_api_webhooks.py
import pytest
from unittest.mock import patch


def test_grafana_webhook_no_api_key(api_client):
    response = api_client.post(
        "/webhooks/grafana",
        json={"title": "Test Alert", "message": "body", "status": "firing"},
    )
    assert response.status_code == 403


def test_grafana_webhook_invalid_api_key(api_client):
    response = api_client.post(
        "/webhooks/grafana",
        json={"title": "Test Alert", "message": "body", "status": "firing"},
        headers={"X-API-KEY": "wrong_key"},
    )
    assert response.status_code == 403


def test_grafana_webhook_valid(api_client):
    from config import settings
    with patch("api.routes.webhooks.notify") as mock_notify:
        response = api_client.post(
            "/webhooks/grafana",
            json={"title": "Test Alert", "message": "body", "status": "firing"},
            headers={"X-API-KEY": settings.WEBHOOK_API_KEY},
        )
        assert response.status_code == 200
        mock_notify.assert_called_once()


def test_idoit_webhook_valid(api_client):
    from config import settings
    with patch("api.routes.webhooks.notify"), \
         patch("api.routes.webhooks.create_idoit_incident", return_value={"success": True, "id": 1}):
        response = api_client.post(
            "/webhooks/idoit",
            json={
                "title": "Test",
                "message": "details",
                "priority": "warning",
                "metric": "cpu",
                "region": "Moscow",
            },
            headers={"X-API-KEY": settings.WEBHOOK_API_KEY},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
