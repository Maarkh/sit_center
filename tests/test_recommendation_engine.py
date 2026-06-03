# tests/test_recommendation_engine.py
"""Unit tests for DSS M7 scoring (pure functions — no DB) + route gates."""
import pytest
from pydantic import ValidationError

from core.recommendation_engine import score_playbook, match_confidence
from api.schemas_dss import PlaybookCreate, RecommendationGenerateRequest


class TestScorePlaybook:
    def test_critical_outranks_warning(self):
        crit = score_playbook(1.0, "critical", 1, indicator_scoped=False)
        warn = score_playbook(1.0, "warning", 1, indicator_scoped=False)
        assert crit > warn

    def test_persistence_raises_score(self):
        fresh = score_playbook(1.0, "warning", 1, indicator_scoped=False)
        chronic = score_playbook(1.0, "warning", 5, indicator_scoped=False)
        assert chronic > fresh

    def test_persistence_caps(self):
        # streak beyond 11 should not keep increasing the factor unbounded
        a = score_playbook(1.0, "warning", 11, indicator_scoped=False)
        b = score_playbook(1.0, "warning", 50, indicator_scoped=False)
        assert a == b

    def test_indicator_scope_bonus(self):
        scoped = score_playbook(1.0, "warning", 1, indicator_scoped=True)
        generic = score_playbook(1.0, "warning", 1, indicator_scoped=False)
        assert scoped > generic

    def test_higher_effect_outranks(self):
        assert score_playbook(5.0, "warning", 1, indicator_scoped=False) > \
               score_playbook(1.0, "warning", 1, indicator_scoped=False)


class TestMatchConfidence:
    def test_generic_is_low(self):
        assert match_confidence(severity_match=False, direction_match=False, indicator_scoped=False) == 0.4

    def test_exact_match_is_high(self):
        c = match_confidence(severity_match=True, direction_match=True, indicator_scoped=True)
        assert c == 1.0

    def test_partial_match_between(self):
        c = match_confidence(severity_match=True, direction_match=False, indicator_scoped=False)
        assert 0.4 < c < 1.0

    def test_never_exceeds_one(self):
        c = match_confidence(severity_match=True, direction_match=True, indicator_scoped=True)
        assert c <= 1.0


class TestPlaybookSchema:
    def test_trigger_direction_both_rejected(self):
        with pytest.raises(ValidationError):
            PlaybookCreate(name="x", trigger_direction="both")

    def test_valid_playbook(self):
        pb = PlaybookCreate(name="Перезапуск сервиса", trigger_severity="critical",
                            trigger_direction="above", effect_score=3.0)
        assert pb.trigger_severity == "critical"

    def test_negative_effect_rejected(self):
        with pytest.raises(ValidationError):
            PlaybookCreate(name="x", effect_score=-1.0)


class TestGenerateRequest:
    def test_requires_exactly_one_target(self):
        with pytest.raises(ValidationError):
            RecommendationGenerateRequest()  # neither
        with pytest.raises(ValidationError):
            RecommendationGenerateRequest(deviation_id="00000000-0000-0000-0000-000000000000",
                                          incident_id=1)  # both

    def test_deviation_only_ok(self):
        r = RecommendationGenerateRequest(deviation_id="00000000-0000-0000-0000-000000000000")
        assert r.incident_id is None


class TestRecommendationRBAC:
    def test_list_playbooks_requires_auth(self, api_client):
        assert api_client.get("/api/v1/playbooks").status_code in (401, 403)

    def test_viewer_cannot_manage_playbooks(self, api_client, viewer_auth_headers):
        resp = api_client.post("/api/v1/playbooks", json={"name": "x"}, headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_viewer_cannot_generate(self, api_client, viewer_auth_headers):
        resp = api_client.post("/api/v1/recommendations/generate",
                               json={"incident_id": 1}, headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_admin_generate_validation(self, api_client, auth_headers):
        # admin passes RBAC; neither target → 422
        resp = api_client.post("/api/v1/recommendations/generate", json={}, headers=auth_headers)
        assert resp.status_code == 422
