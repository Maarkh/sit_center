# tests/test_indicators.py
"""Unit tests for DSS M2 (Indicator & Goal Model).

Schema validation and RBAC/auth gates are tested here (no DB needed — permission
checks run before the route body). The full CRUD lifecycle against a real DB lives
in tests/integration/test_dss.py.
"""
import pytest
from pydantic import ValidationError

from api.schemas_dss import (
    IndicatorCreate, FactorCreate, SubscriptionCreate,
)


class TestIndicatorSchema:
    def test_valid_static_corridor(self):
        ind = IndicatorCreate(name="Доступность сервиса", unit="%", target_low=99.0, target_high=100.0)
        assert ind.corridor_type == "static"
        assert ind.direction == "both"

    def test_corridor_low_above_high_rejected(self):
        with pytest.raises(ValidationError):
            IndicatorCreate(name="bad", target_low=100.0, target_high=1.0)

    def test_static_corridor_needs_a_bound(self):
        with pytest.raises(ValidationError):
            IndicatorCreate(name="no bounds", corridor_type="static")

    def test_baseline_corridor_allows_open_bounds(self):
        ind = IndicatorCreate(name="seasonal", corridor_type="baseline", baseline_model_ref="prophet:v1")
        assert ind.target_low is None and ind.target_high is None

    def test_one_sided_corridor_ok(self):
        ind = IndicatorCreate(name="latency", target_high=200.0, direction="above")
        assert ind.target_low is None
        assert ind.target_high == 200.0

    def test_chronicle_threshold_bounds(self):
        with pytest.raises(ValidationError):
            IndicatorCreate(name="x", target_low=1.0, chronicle_threshold=0)

    def test_nested_factors(self):
        ind = IndicatorCreate(
            name="SLA", target_low=99.0,
            factors=[FactorCreate(name="latency", weight=2.0, metrics=["api_latency_p99"])],
        )
        assert ind.factors[0].metrics == ["api_latency_p99"]


class TestFactorSchema:
    def test_invalid_metric_name_rejected(self):
        with pytest.raises(ValidationError):
            FactorCreate(name="f", metrics=["bad name with spaces"])

    def test_metric_dedup(self):
        f = FactorCreate(name="f", metrics=["cpu", "cpu", "mem"])
        assert f.metrics == ["cpu", "mem"]

    def test_weight_must_be_positive(self):
        with pytest.raises(ValidationError):
            FactorCreate(name="f", weight=0)


class TestSubscriptionSchema:
    def test_requires_a_target(self):
        with pytest.raises(ValidationError):
            SubscriptionCreate(channel="telegram")

    def test_role_target_ok(self):
        s = SubscriptionCreate(subscriber_role="duty-officer", channel="telegram")
        assert s.subscriber_role == "duty-officer"


class TestIndicatorRBAC:
    def test_create_goal_requires_auth(self, api_client):
        resp = api_client.post("/api/v1/indicators/goals", json={"name": "g"})
        assert resp.status_code in (401, 403)

    def test_viewer_cannot_write(self, api_client, viewer_auth_headers):
        # viewer has no write:indicators and is not admin → 403 before any DB access
        resp = api_client.post(
            "/api/v1/indicators/goals", json={"name": "g"}, headers=viewer_auth_headers
        )
        assert resp.status_code == 403

    def test_viewer_cannot_read_indicators_without_permission(self, api_client, viewer_auth_headers):
        # viewer fixture grants only read:metrics/rules/alerts — not read:indicators
        resp = api_client.get("/api/v1/indicators/", headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_create_indicator_validation_error(self, api_client, auth_headers):
        # admin passes RBAC; bad corridor fails schema validation (422) before DB
        resp = api_client.post(
            "/api/v1/indicators/",
            json={"name": "bad", "corridor_type": "static"},  # no bounds
            headers=auth_headers,
        )
        assert resp.status_code == 422
