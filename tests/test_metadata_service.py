# tests/test_metadata_service.py
import pytest
from unittest.mock import patch, MagicMock
from core.metadata_service import MetadataService, MetricDTO


@pytest.fixture
def service(fake_redis_instance):
    with patch("core.metadata_service.get_cache", return_value=fake_redis_instance), \
         patch("core.metadata_service.get_database_url", return_value="postgresql://test:test@localhost/test"):
        svc = MetadataService()
        svc._cache = fake_redis_instance
        yield svc


def test_make_fingerprint():
    fp = MetadataService.make_fingerprint("cpu", {"region": "Moscow"})
    assert isinstance(fp, str)
    assert len(fp) == 32  # md5 hex digest


def test_make_fingerprint_deterministic():
    fp1 = MetadataService.make_fingerprint("cpu", {"a": "1", "b": "2"})
    fp2 = MetadataService.make_fingerprint("cpu", {"b": "2", "a": "1"})
    assert fp1 == fp2


def test_list_metrics_cached(service, fake_redis_instance):
    import json
    cached = [{"metric_name": "m1", "display_name": "M1", "is_active": True, "unit": "", "description": None, "default_threshold": None, "default_critical_threshold": None}]
    fake_redis_instance.set("metadata:metrics:active", json.dumps(cached))

    result = service.list_metrics(active_only=True)
    assert len(result) == 1
    assert result[0].metric_name == "m1"


def test_serialize_deserialize(service):
    data = {"key": "value", "list": [1, 2, 3]}
    serialized = service._serialize_json(data)
    deserialized = service._deserialize_json(serialized)
    assert deserialized == data


def test_deserialize_none(service):
    assert service._deserialize_json(None) is None
