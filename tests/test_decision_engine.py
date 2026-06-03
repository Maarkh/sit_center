# tests/test_decision_engine.py
"""Unit tests for DSS M10 win-rate logic (pure — no DB) + its effect on M7 scoring."""
import pytest
from pydantic import ValidationError

from core.decision_engine import compute_winrate, winrate_factor, MIN_SAMPLES
from core.recommendation_engine import score_playbook
from api.schemas_dss import OutcomeCreate


class TestComputeWinrate:
    def test_basic_rate(self):
        out = compute_winrate([{"playbook_id": "p1", "decided": 4, "resolved": 3}])
        assert out["p1"]["win_rate"] == 0.75
        assert out["p1"]["decided"] == 4

    def test_zero_decided_is_none(self):
        out = compute_winrate([{"playbook_id": "p1", "decided": 0, "resolved": 0}])
        assert out["p1"]["win_rate"] is None

    def test_perfect_and_zero(self):
        out = compute_winrate([
            {"playbook_id": "a", "decided": 5, "resolved": 5},
            {"playbook_id": "b", "decided": 5, "resolved": 0},
        ])
        assert out["a"]["win_rate"] == 1.0
        assert out["b"]["win_rate"] == 0.0


class TestWinrateFactor:
    def test_neutral_without_enough_samples(self):
        assert winrate_factor(1.0, MIN_SAMPLES - 1) == 1.0
        assert winrate_factor(None, 100) == 1.0

    def test_proven_playbook_boosts(self):
        assert winrate_factor(1.0, 10) == 1.5

    def test_failing_playbook_penalises(self):
        assert winrate_factor(0.0, 10) == 0.5

    def test_midrange(self):
        assert winrate_factor(0.5, 10) == 1.0

    def test_clamped(self):
        assert winrate_factor(2.0, 10) == 1.5   # win_rate clamped to 1.0
        assert winrate_factor(-1.0, 10) == 0.5


class TestWinrateAffectsScoring:
    def test_winrate_factor_scales_score(self):
        base = score_playbook(2.0, "warning", 1, indicator_scoped=False)
        boosted = score_playbook(2.0, "warning", 1, indicator_scoped=False, winrate_factor=1.5)
        penalised = score_playbook(2.0, "warning", 1, indicator_scoped=False, winrate_factor=0.5)
        assert boosted > base > penalised
        assert boosted == round(base * 1.5, 4)

    def test_default_is_neutral(self):
        # default winrate_factor=1.0 keeps the original score (back-compat)
        assert score_playbook(1.0, "critical", 1, indicator_scoped=False) == 1.5


class TestOutcomeSchema:
    def test_requires_resolved(self):
        with pytest.raises(ValidationError):
            OutcomeCreate(effect_value=10.0)

    def test_valid(self):
        o = OutcomeCreate(resolved=True, effect_value=42.0, note="устранено")
        assert o.resolved is True


class TestDecisionRBAC:
    def test_decision_log_requires_auth(self, api_client):
        assert api_client.get("/api/v1/recommendations/decisions").status_code in (401, 403)

    def test_viewer_cannot_record_outcome(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/api/v1/recommendations/00000000-0000-0000-0000-000000000000/outcome",
            json={"resolved": True}, headers=viewer_auth_headers)
        assert resp.status_code == 403
