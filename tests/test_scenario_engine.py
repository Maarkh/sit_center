# tests/test_scenario_engine.py
"""Unit tests for DSS M6 what-if logic (pure — no DB) + route gates."""
import pytest
from pydantic import ValidationError

from core.scenario_engine import apply_assumption, evaluate_scenario
from api.schemas_dss import ScenarioCreate


class TestApplyAssumption:
    def test_target_replaces(self):
        assert apply_assumption(150.0, "target", 50.0) == 50.0

    def test_target_works_without_baseline(self):
        assert apply_assumption(None, "target", 50.0) == 50.0

    def test_delta_adds(self):
        assert apply_assumption(100.0, "delta", -30.0) == 70.0

    def test_delta_pct(self):
        assert apply_assumption(200.0, "delta_pct", -25.0) == 150.0

    def test_delta_without_baseline_is_none(self):
        assert apply_assumption(None, "delta", 10.0) is None


def _ind(id_, value, low, high, direction="above", dw=0.0):
    return {"id": id_, "value": value, "low": low, "high": high, "direction": direction,
            "downstream_weight": dw, "name": f"ind-{id_}"}


class TestEvaluateScenario:
    def test_breach_removed_counts_potential(self):
        # baseline 150 breaches high=100; target 50 fixes it
        out = evaluate_scenario([_ind("a", 150.0, 0.0, 100.0)], {"a": {"mode": "target", "value": 50.0}})
        r = out["results"][0]
        assert r["baseline_breach"] == "above"
        assert r["projected_breach"] is None
        assert r["improved"] is True
        assert out["breaches_avoided"] == 1
        assert out["potential_value"] > 0

    def test_downstream_weight_raises_potential(self):
        low_pot = evaluate_scenario([_ind("a", 150.0, 0.0, 100.0, dw=0.0)],
                                    {"a": {"mode": "target", "value": 50.0}})["potential_value"]
        high_pot = evaluate_scenario([_ind("a", 150.0, 0.0, 100.0, dw=3.0)],
                                     {"a": {"mode": "target", "value": 50.0}})["potential_value"]
        assert high_pot > low_pot

    def test_no_change_no_potential(self):
        # already inside corridor → no improvement
        out = evaluate_scenario([_ind("a", 50.0, 0.0, 100.0)], {"a": {"mode": "target", "value": 60.0}})
        assert out["results"][0]["improved"] is False
        assert out["potential_value"] == 0
        assert out["breaches_avoided"] == 0

    def test_worsened_flag(self):
        # baseline ok, assumption pushes it out of corridor
        out = evaluate_scenario([_ind("a", 50.0, 0.0, 100.0)], {"a": {"mode": "target", "value": 150.0}})
        r = out["results"][0]
        assert r["worsened"] is True
        assert out["breaches_avoided"] == 0  # worsening is not a potential gain

    def test_indicator_without_assumption_unchanged(self):
        out = evaluate_scenario([_ind("a", 150.0, 0.0, 100.0)], {})
        r = out["results"][0]
        assert r["baseline"] == r["projected"] == 150.0
        assert r["improved"] is False

    def test_no_baseline_data_skips(self):
        out = evaluate_scenario([_ind("a", None, 0.0, 100.0)], {"a": {"mode": "delta", "value": -50.0}})
        r = out["results"][0]
        assert r["baseline"] is None and r["projected"] is None
        assert r["improved"] is False


class TestScenarioSchema:
    def test_requires_an_assumption(self):
        with pytest.raises(ValidationError):
            ScenarioCreate(name="empty", assumptions=[])

    def test_valid(self):
        s = ScenarioCreate(name="reduce loss", assumptions=[
            {"indicator_id": "00000000-0000-0000-0000-000000000001", "mode": "delta_pct", "value": -30}])
        assert s.assumptions[0].mode == "delta_pct"


class TestScenarioRBAC:
    def test_list_requires_auth(self, api_client):
        assert api_client.get("/api/v1/scenarios/").status_code in (401, 403)

    def test_viewer_cannot_create(self, api_client, viewer_auth_headers):
        resp = api_client.post("/api/v1/scenarios/", json={
            "name": "x", "assumptions": [{"indicator_id": "00000000-0000-0000-0000-000000000001", "value": 1}]},
            headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_admin_empty_assumptions_422(self, api_client, auth_headers):
        resp = api_client.post("/api/v1/scenarios/", json={"name": "x", "assumptions": []},
                               headers=auth_headers)
        assert resp.status_code == 422
