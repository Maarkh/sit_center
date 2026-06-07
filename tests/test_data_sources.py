"""Data-source registry helpers (M1) — pure logic, no DB/network."""
import pytest

from core.data_sources import (
    _dig, collect_host_agent, probe, HOST_METRICS, kafka_topics_from_sources,
    build_metric_rows, find_source_by_api_key, SOURCE_TYPES,
)
from api.routes.data_sources import _mask, _merge_secrets, MASK, SourceCreate


# ── json-path walking (http_pull extraction) ────────────────────────────────
def test_dig_nested_dict():
    assert _dig({"data": {"cpu": 42}}, "data.cpu") == 42


def test_dig_list_index():
    assert _dig({"items": [{"v": 1}, {"v": 2}]}, "items.1.v") == 2


def test_dig_missing_raises():
    with pytest.raises(Exception):
        _dig({"a": 1}, "a.b.c")


# ── host_agent collection ───────────────────────────────────────────────────
def test_collect_host_agent_known_metrics():
    rows = collect_host_agent({"metrics": ["cpu_usage", "mem_usage"]})
    names = {n for n, _ in rows}
    assert names == {"cpu_usage", "mem_usage"}
    assert all(isinstance(v, float) for _, v in rows)


def test_collect_host_agent_skips_unknown():
    rows = collect_host_agent({"metrics": ["mem_usage", "does_not_exist"]})
    assert {n for n, _ in rows} == {"mem_usage"}


def test_collect_host_agent_defaults_when_empty():
    rows = collect_host_agent({})
    assert {n for n, _ in rows} == {"cpu_usage", "mem_usage"}


def test_host_metrics_registry_callables():
    for name, fn in HOST_METRICS.items():
        assert callable(fn), name


# ── probe ───────────────────────────────────────────────────────────────────
def test_probe_host_agent_ok():
    res = probe("host_agent", {"metrics": ["mem_usage"]})
    assert res["ok"] is True
    assert "mem_usage" in res["sample"]


def test_probe_kafka_requires_topic():
    assert probe("kafka", {})["ok"] is False
    assert probe("kafka", {"topic": "sit_center.metrics"})["ok"] is True


def test_probe_unknown_type():
    assert probe("nope", {})["ok"] is False


# ── secret masking contract (mirrors notification channels) ─────────────────
def test_mask_hides_secrets():
    masked = _mask({"url": "http://x", "token": "s3cret"})
    assert masked["url"] == "http://x"
    assert masked["token"] == MASK


def test_merge_secrets_preserves_on_mask_sentinel():
    merged = _merge_secrets({"token": MASK, "url": "http://y"}, {"token": "real", "url": "http://x"})
    assert merged["token"] == "real"
    assert merged["url"] == "http://y"


def test_merge_secrets_overwrites_when_new_value():
    merged = _merge_secrets({"token": "new"}, {"token": "old"})
    assert merged["token"] == "new"


# ── pydantic type validation ────────────────────────────────────────────────
def test_source_create_rejects_bad_type():
    with pytest.raises(Exception):
        SourceCreate(name="x", type="ftp", config={})


def test_source_create_accepts_known_types():
    for t in ("host_agent", "http_pull", "kafka", "http_push"):
        s = SourceCreate(name="x", type=t, config={})
        assert s.type == t


# ── http_push ───────────────────────────────────────────────────────────────
def test_http_push_in_source_types():
    assert "http_push" in SOURCE_TYPES


def test_probe_http_push_reports_readiness():
    res = probe("http_push", {"api_key": "k"})
    assert res["ok"] is True
    assert res["sample"]["api_key_set"] is True
    assert res["sample"]["endpoint"].endswith("/ingest/metrics")
    assert probe("http_push", {})["sample"]["api_key_set"] is False


def test_find_source_by_api_key_empty_returns_none():
    assert find_source_by_api_key("") is None
    assert find_source_by_api_key(None) is None


def test_mask_hides_api_key():
    assert _mask({"api_key": "secret", "url": "u"})["api_key"] == MASK


def test_build_metric_rows_shapes_points():
    pts = [{"metric_name": "m1", "value": 1, "dimensions": {"r": "x"}},
           {"metric_name": "m2", "value": 2.5}]
    rows = build_metric_rows(pts, "Ext", "default")
    assert len(rows) == 2
    assert rows[0]["metric_name"] == "m1" and rows[0]["value"] == 1.0
    assert rows[0]["source"] == "Ext" and rows[0]["tenant_id"] == "default"
    assert rows[0]["dimensions"] == '{"r": "x"}'   # json-encoded
    assert rows[1]["tags"] == "{}"                   # default empty


# ── kafka topic resolution ──────────────────────────────────────────────────
def test_kafka_topics_union_with_default():
    sources = [{"config": {"topic": "a"}}, {"config": {"topic": "b"}}]
    assert kafka_topics_from_sources(sources, "sit_center.metrics") == ["a", "b", "sit_center.metrics"]


def test_kafka_topics_dedup_preserves_order():
    sources = [{"config": {"topic": "a"}}, {"config": {"topic": "a"}}]
    assert kafka_topics_from_sources(sources, "a") == ["a"]


def test_kafka_topics_skips_blank():
    sources = [{"config": {}}, {"config": {"topic": ""}}, {"config": {"topic": "x"}}]
    assert kafka_topics_from_sources(sources, None) == ["x"]


def test_kafka_topics_default_only():
    assert kafka_topics_from_sources([], "default.topic") == ["default.topic"]
