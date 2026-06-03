# tests/test_process_engine.py
"""Unit tests for DSS M8 wave logic (pure functions — no DB) + route gates."""
import pytest
from pydantic import ValidationError

from core.process_engine import current_wave_order, is_instance_complete
from api.schemas_dss import ProcessTemplateCreate, ProcessStepCreate


def _a(order, status):
    return {"step_order": order, "status": status}


class TestWaveOrder:
    def test_first_wave_is_lowest_order(self):
        assignments = [_a(0, "pending"), _a(1, "pending"), _a(2, "pending")]
        assert current_wave_order(assignments) == 0

    def test_wave_stays_until_all_in_wave_terminal(self):
        # order 0 has one done, one still in_progress → wave is still 0
        assignments = [_a(0, "done"), _a(0, "in_progress"), _a(1, "pending")]
        assert current_wave_order(assignments) == 1 - 1  # == 0

    def test_advances_when_wave_complete(self):
        assignments = [_a(0, "done"), _a(0, "skipped"), _a(1, "pending")]
        assert current_wave_order(assignments) == 1

    def test_parallel_steps_share_a_wave(self):
        # three parallel steps at order 0; none terminal → wave 0, all activate together
        assignments = [_a(0, "active"), _a(0, "active"), _a(0, "pending")]
        assert current_wave_order(assignments) == 0

    def test_complete_when_all_terminal(self):
        assignments = [_a(0, "done"), _a(1, "done"), _a(2, "skipped")]
        assert current_wave_order(assignments) is None
        assert is_instance_complete(assignments) is True

    def test_not_complete_with_any_nonterminal(self):
        assignments = [_a(0, "done"), _a(1, "in_progress")]
        assert is_instance_complete(assignments) is False

    def test_empty_is_complete(self):
        assert current_wave_order([]) is None
        assert is_instance_complete([]) is True


class TestTemplateSchema:
    def test_template_requires_a_step(self):
        with pytest.raises(ValidationError):
            ProcessTemplateCreate(name="empty", steps=[])

    def test_valid_template(self):
        t = ProcessTemplateCreate(
            name="Реакция на отказ",
            steps=[
                ProcessStepCreate(name="Диагностика", step_order=0, assignee_role="L1",
                                  checklist=["проверить логи", "проверить метрики"], due_after_minutes=15),
                ProcessStepCreate(name="Устранение", step_order=1, step_type="sequential",
                                  assignee_role="L2"),
            ],
        )
        assert len(t.steps) == 2
        assert t.steps[0].checklist == ["проверить логи", "проверить метрики"]

    def test_parallel_steps_same_order(self):
        t = ProcessTemplateCreate(
            name="parallel",
            steps=[
                ProcessStepCreate(name="A", step_order=0, step_type="parallel"),
                ProcessStepCreate(name="B", step_order=0, step_type="parallel"),
            ],
        )
        assert {s.step_order for s in t.steps} == {0}


class TestProcessRBAC:
    def test_create_template_requires_auth(self, api_client):
        resp = api_client.post("/api/v1/processes/templates", json={"name": "x", "steps": []})
        assert resp.status_code in (401, 403)

    def test_viewer_cannot_write(self, api_client, viewer_auth_headers):
        resp = api_client.post(
            "/api/v1/processes/templates",
            json={"name": "x", "steps": [{"name": "s", "step_order": 0}]},
            headers=viewer_auth_headers,
        )
        assert resp.status_code == 403

    def test_viewer_cannot_read_processes(self, api_client, viewer_auth_headers):
        resp = api_client.get("/api/v1/processes/templates", headers=viewer_auth_headers)
        assert resp.status_code == 403

    def test_admin_empty_template_validation(self, api_client, auth_headers):
        # admin passes RBAC; empty steps fails schema validation (422)
        resp = api_client.post(
            "/api/v1/processes/templates",
            json={"name": "x", "steps": []},
            headers=auth_headers,
        )
        assert resp.status_code == 422
