"""HTTP push ingestion route (M1) — auth + dispatch; registry/DB helpers mocked."""
from unittest.mock import patch


def _batch():
    return {"metrics": [{"metric_name": "ext_cpu", "value": 12.5}]}


def test_ingest_requires_api_key(api_client):
    r = api_client.post("/api/v1/ingest/metrics", json=_batch())
    assert r.status_code == 401


def test_ingest_rejects_unknown_key(api_client):
    with patch("api.routes.ingestion.find_source_by_api_key", return_value=None):
        r = api_client.post("/api/v1/ingest/metrics", json=_batch(), headers={"X-API-KEY": "nope"})
    assert r.status_code == 403


def test_ingest_inserts_and_returns_count(api_client):
    src = {"id": "1", "tenant_id": "default", "name": "Ext"}
    with patch("api.routes.ingestion.find_source_by_api_key", return_value=src), \
         patch("api.routes.ingestion.insert_metrics", return_value=1) as ins:
        r = api_client.post("/api/v1/ingest/metrics", json=_batch(), headers={"X-API-KEY": "good"})
    assert r.status_code == 200
    assert r.json() == {"ingested": 1}
    ins.assert_called_once()
    # the source name + tenant from the matched source are passed through
    _, name, tenant = ins.call_args[0]
    assert name == "Ext" and tenant == "default"


def test_ingest_validates_empty_batch(api_client):
    src = {"id": "1", "tenant_id": "default", "name": "Ext"}
    with patch("api.routes.ingestion.find_source_by_api_key", return_value=src):
        r = api_client.post("/api/v1/ingest/metrics", json={"metrics": []}, headers={"X-API-KEY": "good"})
    assert r.status_code == 422
