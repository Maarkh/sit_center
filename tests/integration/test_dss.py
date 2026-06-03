# tests/integration/test_dss.py
"""End-to-end integration tests for the DSS modules (M2/M3/M8/M7/M5/M4).

Run against a REAL migrated TimescaleDB (migrations 010-015 must be applied).
These exercise the full lifecycles the unit tests can't: nested factor creation,
corridor evaluation writing real deviations/chronicles, the process wave engine,
the deviation→recommendation→process chain, predictive alerts, and correlation of
deviations into situations with impact + root-cause.
"""
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import text


def _tables_present(db_engine, *tables) -> bool:
    try:
        with db_engine.connect() as conn:
            for t in tables:
                conn.execute(text(f"SELECT 1 FROM {t} LIMIT 1"))
        return True
    except Exception:
        return False


# ======================================================================
# M2 — Indicator & Goal Model
# ======================================================================
class TestIndicatorModel:
    def test_goal_indicator_factor_tree(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "goals", "indicators", "factors"):
            pytest.skip("M2 tables not found — migration 010 not applied")

        # Goal
        resp = integration_client.post(
            "/api/v1/indicators/goals",
            json={"name": "Доступность услуг", "owner_role": "ops-lead"},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        goal_id = resp.json()["id"]

        # Indicator with nested factors
        resp = integration_client.post(
            "/api/v1/indicators/",
            json={
                "name": "SLA портала", "unit": "%", "goal_id": goal_id,
                "target_low": 99.0, "target_high": 100.0, "direction": "below",
                "factors": [
                    {"name": "успешные ответы", "weight": 2.0, "metrics": ["http_success_ratio"]},
                ],
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        ind = resp.json()
        ind_id = ind["id"]
        assert ind["factors"][0]["metrics"] == ["http_success_ratio"]

        # Subscription
        resp = integration_client.post(
            f"/api/v1/indicators/{ind_id}/subscriptions",
            json={"subscriber_role": "duty-officer", "channel": "telegram"},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text

        # Tree contains the goal with its indicator
        resp = integration_client.get("/api/v1/indicators/tree", headers=admin_headers)
        assert resp.status_code == 200
        tree = resp.json()
        goal_node = next((g for g in tree["goals"] if g["id"] == goal_id), None)
        assert goal_node is not None
        assert any(i["id"] == ind_id for i in goal_node["indicators"])

        # Cleanup (cascades factors + subscriptions)
        assert integration_client.delete(f"/api/v1/indicators/{ind_id}", headers=admin_headers).status_code == 204
        assert integration_client.delete(f"/api/v1/indicators/goals/{goal_id}", headers=admin_headers).status_code == 204

    def test_tenant_isolation(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "indicators"):
            pytest.skip("M2 tables not found")
        other_id = uuid.uuid4()
        with db_engine.begin() as conn:
            conn.execute(
                text("INSERT INTO indicators (id, tenant_id, name, target_high, corridor_type) "
                     "VALUES (:id, 'tenant-b', 'leaked', 100, 'static')"),
                {"id": other_id},
            )
        try:
            resp = integration_client.get("/api/v1/indicators/?active_only=false", headers=admin_headers)
            assert resp.status_code == 200
            assert all(i["id"] != str(other_id) for i in resp.json()), "tenant-b indicator leaked!"
        finally:
            with db_engine.begin() as conn:
                conn.execute(text("DELETE FROM indicators WHERE id = :id"), {"id": other_id})


# ======================================================================
# M3 — Deviation Detection & Chronicle
# ======================================================================
class TestDeviationEvaluation:
    def test_corridor_breach_chronicle_and_resolve(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "indicators", "deviations", "chronicles", "canonical_metrics"):
            pytest.skip("M2/M3 tables not found — migrations 010-011 not applied")

        from core.deviation_engine import indicator_evaluator

        metric = f"itest_dss_metric_{uuid.uuid4().hex[:8]}"
        # Indicator: corridor [0, 100], above is a breach, chronicle threshold 2.
        resp = integration_client.post(
            "/api/v1/indicators/",
            json={
                "name": "DSS test indicator", "target_low": 0.0, "target_high": 100.0,
                "direction": "above", "chronicle_threshold": 2,
                "factors": [{"name": "f", "weight": 1.0, "metrics": [metric]}],
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        ind_id = resp.json()["id"]

        def seed(value):
            with db_engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO canonical_metrics "
                         "(metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
                         "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'itest', 'default')"),
                    {"m": metric, "v": value},
                )

        def clear_metric():
            with db_engine.begin() as conn:
                conn.execute(text("DELETE FROM canonical_metrics WHERE metric_name = :m"), {"m": metric})

        try:
            # Phase A — value 150 is above 100 → deviation opens.
            seed(150.0)
            s1 = indicator_evaluator.evaluate_tenant("default")
            assert s1["opened"] >= 1

            resp = integration_client.get(
                f"/api/v1/deviations/?indicator_id={ind_id}&active_only=true", headers=admin_headers)
            assert resp.status_code == 200
            devs = resp.json()
            assert len(devs) == 1
            assert devs[0]["direction"] == "above"
            assert devs[0]["periods"] == 1

            # Phase A2 — still breaching → periods 2 == threshold → chronic + critical.
            s2 = indicator_evaluator.evaluate_tenant("default")
            assert s2["chronic"] >= 1
            resp = integration_client.get(
                f"/api/v1/deviations/?indicator_id={ind_id}&active_only=true", headers=admin_headers)
            dev = resp.json()[0]
            assert dev["periods"] == 2
            assert dev["severity"] == "critical"

            # Chronicle aggregate recorded.
            resp = integration_client.get(
                f"/api/v1/deviations/chronicles/list?indicator_id={ind_id}", headers=admin_headers)
            assert resp.status_code == 200
            chron = resp.json()
            assert len(chron) == 1
            assert chron[0]["episodes"] == 1
            assert chron[0]["max_periods"] == 2

            # Phase B — back inside corridor → deviation resolves.
            clear_metric()
            seed(50.0)
            s3 = indicator_evaluator.evaluate_tenant("default")
            assert s3["resolved"] >= 1
            resp = integration_client.get(
                f"/api/v1/deviations/?indicator_id={ind_id}&active_only=true", headers=admin_headers)
            assert resp.json() == []
        finally:
            clear_metric()
            integration_client.delete(f"/api/v1/indicators/{ind_id}", headers=admin_headers)

    def test_acknowledge_and_resolve_via_api(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "indicators", "deviations", "canonical_metrics"):
            pytest.skip("M2/M3 tables not found")

        from core.deviation_engine import indicator_evaluator
        metric = f"itest_dss_ack_{uuid.uuid4().hex[:8]}"
        resp = integration_client.post(
            "/api/v1/indicators/",
            json={"name": "ack test", "target_high": 10.0, "direction": "above",
                  "factors": [{"name": "f", "metrics": [metric]}]},
            headers=admin_headers,
        )
        ind_id = resp.json()["id"]
        try:
            with db_engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO canonical_metrics "
                         "(metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
                         "VALUES (:m, 99, NOW(), '{}'::jsonb, '{}'::jsonb, 'itest', 'default')"),
                    {"m": metric},
                )
            indicator_evaluator.evaluate_tenant("default")
            dev_id = integration_client.get(
                f"/api/v1/deviations/?indicator_id={ind_id}&active_only=true",
                headers=admin_headers).json()[0]["id"]

            r = integration_client.post(f"/api/v1/deviations/{dev_id}/acknowledge",
                                        json={"note": "смотрю"}, headers=admin_headers)
            assert r.status_code == 200
            assert r.json()["status"] == "acknowledged"
            assert r.json()["acknowledged_by"] == "admin"

            r = integration_client.post(f"/api/v1/deviations/{dev_id}/resolve",
                                        json={}, headers=admin_headers)
            assert r.status_code == 200
            assert r.json()["status"] == "resolved"
        finally:
            with db_engine.begin() as conn:
                conn.execute(text("DELETE FROM canonical_metrics WHERE metric_name = :m"), {"m": metric})
            integration_client.delete(f"/api/v1/indicators/{ind_id}", headers=admin_headers)


# ======================================================================
# M8 — Process / Workflow Engine
# ======================================================================
class TestProcessEngine:
    def test_full_workflow_sequential_and_parallel(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "process_templates", "process_steps",
                               "process_instances", "step_assignments"):
            pytest.skip("M8 tables not found — migration 012 not applied")

        # Template: wave 0 = two parallel steps (A,B), wave 1 = one step (C).
        resp = integration_client.post(
            "/api/v1/processes/templates",
            json={
                "name": "Реакция на инцидент",
                "steps": [
                    {"name": "Диагностика", "step_order": 0, "step_type": "parallel",
                     "assignee_role": "L1", "checklist": ["логи", "метрики"]},
                    {"name": "Оповещение", "step_order": 0, "step_type": "parallel",
                     "assignee_role": "duty"},
                    {"name": "Устранение", "step_order": 1, "step_type": "sequential",
                     "assignee_role": "L2"},
                ],
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        tmpl_id = resp.json()["id"]
        assert len(resp.json()["steps"]) == 3

        # Instantiate
        resp = integration_client.post(
            "/api/v1/processes/instances",
            json={"template_id": tmpl_id, "title": "Инцидент #1"},
            headers=admin_headers,
        )
        assert resp.status_code == 201, resp.text
        inst = resp.json()
        inst_id = inst["id"]
        assert inst["status"] == "running"

        by_name = {a["name"]: a for a in inst["assignments"]}
        # Wave 0 steps active, wave 1 step pending.
        assert by_name["Диагностика"]["status"] == "active"
        assert by_name["Оповещение"]["status"] == "active"
        assert by_name["Устранение"]["status"] == "pending"

        # Cannot complete the wave-1 step before its wave is reached.
        r = integration_client.post(
            f"/api/v1/processes/assignments/{by_name['Устранение']['id']}/complete",
            json={"force": True}, headers=admin_headers)
        assert r.status_code == 409

        # Work step A (checklist must be done before completing without force).
        a_id = by_name["Диагностика"]["id"]
        r = integration_client.post(f"/api/v1/processes/assignments/{a_id}/start",
                                    json={"assignee": "operator-1"}, headers=admin_headers)
        assert r.status_code == 200 and r.json()["status"] == "in_progress"

        # Completing with unchecked checklist is rejected.
        r = integration_client.post(f"/api/v1/processes/assignments/{a_id}/complete",
                                    json={}, headers=admin_headers)
        assert r.status_code == 409

        # Check off the checklist, then complete.
        r = integration_client.patch(
            f"/api/v1/processes/assignments/{a_id}/checklist",
            json={"checklist_state": [{"item": "логи", "done": True}, {"item": "метрики", "done": True}]},
            headers=admin_headers)
        assert r.status_code == 200
        r = integration_client.post(f"/api/v1/processes/assignments/{a_id}/complete",
                                    json={"report": "всё проверено"}, headers=admin_headers)
        assert r.status_code == 200 and r.json()["status"] == "done"

        # Instance still running — step B not done; wave 1 not yet active.
        inst = integration_client.get(f"/api/v1/processes/instances/{inst_id}", headers=admin_headers).json()
        assert inst["status"] == "running"
        cur = {a["name"]: a["status"] for a in inst["assignments"]}
        assert cur["Устранение"] == "pending"

        # Complete B with force (no checklist) → wave advances, C activates.
        r = integration_client.post(
            f"/api/v1/processes/assignments/{by_name['Оповещение']['id']}/complete",
            json={"force": True}, headers=admin_headers)
        assert r.status_code == 200
        inst = integration_client.get(f"/api/v1/processes/instances/{inst_id}", headers=admin_headers).json()
        c = next(a for a in inst["assignments"] if a["name"] == "Устранение")
        assert c["status"] == "active"

        # Complete C → instance completes.
        r = integration_client.post(f"/api/v1/processes/assignments/{c['id']}/complete",
                                    json={"force": True}, headers=admin_headers)
        assert r.status_code == 200
        inst = integration_client.get(f"/api/v1/processes/instances/{inst_id}", headers=admin_headers).json()
        assert inst["status"] == "completed"
        assert inst["completed_at"] is not None

        # Cleanup
        integration_client.delete(f"/api/v1/processes/templates/{tmpl_id}", headers=admin_headers)

    def test_step_sla_escalation(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "process_templates", "step_assignments"):
            pytest.skip("M8 tables not found")
        from core.process_engine import process_engine

        resp = integration_client.post(
            "/api/v1/processes/templates",
            json={"name": "SLA test", "steps": [
                {"name": "Шаг с дедлайном", "step_order": 0, "due_after_minutes": 30}]},
            headers=admin_headers,
        )
        tmpl_id = resp.json()["id"]
        inst_id = integration_client.post(
            "/api/v1/processes/instances", json={"template_id": tmpl_id},
            headers=admin_headers).json()["id"]
        try:
            # Backdate the active step's due_at into the past.
            with db_engine.begin() as conn:
                conn.execute(
                    text("UPDATE step_assignments SET due_at = NOW() - INTERVAL '1 hour' "
                         "WHERE instance_id = :id AND status = 'active'"),
                    {"id": inst_id},
                )
            escalated = process_engine.escalate_overdue_steps("default")
            assert escalated >= 1

            inst = integration_client.get(f"/api/v1/processes/instances/{inst_id}", headers=admin_headers).json()
            assert any(a["escalated"] for a in inst["assignments"])

            # Idempotent: a second pass does not re-escalate the same step.
            assert process_engine.escalate_overdue_steps("default") == 0
        finally:
            integration_client.delete(f"/api/v1/processes/templates/{tmpl_id}", headers=admin_headers)


# ======================================================================
# M7 — Knowledge Base & Recommendation (Orient → Decide → Act chain)
# ======================================================================
class TestRecommendation:
    def test_deviation_to_recommendation_to_process(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "playbooks", "recommendations", "deviations",
                               "process_templates"):
            pytest.skip("M7 tables not found — migration 013 not applied")

        from core.deviation_engine import indicator_evaluator

        metric = f"itest_reco_{uuid.uuid4().hex[:8]}"
        # Indicator: corridor high=100, above is a breach, chronicle threshold 2.
        ind_id = integration_client.post(
            "/api/v1/indicators/",
            json={"name": "reco indicator", "target_high": 100.0, "direction": "above",
                  "chronicle_threshold": 2, "factors": [{"name": "f", "metrics": [metric]}]},
            headers=admin_headers,
        ).json()["id"]

        # A process template the winning playbook will launch.
        tmpl_id = integration_client.post(
            "/api/v1/processes/templates",
            json={"name": "Регламент устранения", "steps": [
                {"name": "Локализовать", "step_order": 0, "assignee_role": "L1"}]},
            headers=admin_headers,
        ).json()["id"]

        # Specific playbook: scoped to this indicator, exact severity+direction, has a process.
        specific_pb = integration_client.post(
            "/api/v1/playbooks",
            json={"name": "Целевой playbook", "trigger_severity": "critical",
                  "trigger_direction": "above", "effect_score": 2.0,
                  "process_template_id": tmpl_id, "indicator_ids": [ind_id],
                  "actions": [{"action": "перезапустить узел", "checklist": ["проверить healthcheck"]}]},
            headers=admin_headers,
        )
        assert specific_pb.status_code == 201, specific_pb.text
        specific_pb_id = specific_pb.json()["id"]

        # Generic playbook: any/any, no scope, lower effect.
        integration_client.post(
            "/api/v1/playbooks",
            json={"name": "Общий playbook", "effect_score": 1.0},
            headers=admin_headers,
        )

        def seed(value):
            with db_engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO canonical_metrics "
                         "(metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
                         "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'itest', 'default')"),
                    {"m": metric, "v": value},
                )

        try:
            # Drive the indicator to a critical, chronic breach.
            seed(150.0)
            indicator_evaluator.evaluate_tenant("default")
            indicator_evaluator.evaluate_tenant("default")  # periods 2 → critical
            dev = integration_client.get(
                f"/api/v1/deviations/?indicator_id={ind_id}&active_only=true",
                headers=admin_headers).json()[0]
            assert dev["severity"] == "critical"
            dev_id = dev["id"]

            # Generate ranked recommendations.
            resp = integration_client.post(
                "/api/v1/recommendations/generate",
                json={"deviation_id": dev_id}, headers=admin_headers)
            assert resp.status_code == 200, resp.text
            recos = resp.json()
            assert len(recos) == 2
            # The specific, scoped, exact-match playbook must rank first.
            assert recos[0]["rank"] == 1
            assert recos[0]["playbook_id"] == specific_pb_id
            assert recos[0]["score"] > recos[1]["score"]
            assert recos[0]["confidence"] > recos[1]["confidence"]
            top_id = recos[0]["id"]

            # Accept the top recommendation → its process is instantiated, sibling dismissed.
            resp = integration_client.post(
                f"/api/v1/recommendations/{top_id}/accept", json={}, headers=admin_headers)
            assert resp.status_code == 200, resp.text
            accepted = resp.json()
            assert accepted["status"] == "accepted"
            assert accepted["process_instance_id"] is not None
            assert accepted["decided_by"] == "admin"

            # The launched process is bound to the originating deviation.
            inst = integration_client.get(
                f"/api/v1/processes/instances/{accepted['process_instance_id']}",
                headers=admin_headers).json()
            assert inst["deviation_id"] == dev_id
            assert inst["status"] == "running"

            # The sibling recommendation was auto-dismissed by the choice.
            all_recos = integration_client.get(
                f"/api/v1/recommendations?deviation_id={dev_id}", headers=admin_headers).json()
            statuses = {r["id"]: r["status"] for r in all_recos}
            assert statuses[top_id] == "accepted"
            assert all(s == "dismissed" for rid, s in statuses.items() if rid != top_id)

            # Double-accept is rejected.
            assert integration_client.post(
                f"/api/v1/recommendations/{top_id}/accept", json={},
                headers=admin_headers).status_code == 409
        finally:
            with db_engine.begin() as conn:
                conn.execute(text("DELETE FROM canonical_metrics WHERE metric_name = :m"), {"m": metric})
            integration_client.delete(f"/api/v1/indicators/{ind_id}", headers=admin_headers)
            # playbooks + template cleanup (recommendations cascade from the deviation)
            for pb in integration_client.get("/api/v1/playbooks", headers=admin_headers).json():
                if pb["name"] in ("Целевой playbook", "Общий playbook"):
                    integration_client.delete(f"/api/v1/playbooks/{pb['id']}", headers=admin_headers)
            integration_client.delete(f"/api/v1/processes/templates/{tmpl_id}", headers=admin_headers)


# ======================================================================
# M5 — Forecasting & Predictive Alerts (Project)
# ======================================================================
class TestPredictiveAlerts:
    def test_projected_breach_raises_and_resolves(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "indicators", "predictive_alerts", "forecasts"):
            pytest.skip("M5 tables not found — migration 014 not applied")

        from core.predictive_engine import predictive_engine

        metric = f"itest_pred_{uuid.uuid4().hex[:8]}"
        ind_id = integration_client.post(
            "/api/v1/indicators/",
            json={"name": "pred indicator", "target_high": 100.0, "direction": "above",
                  "factors": [{"name": "f", "metrics": [metric]}]},
            headers=admin_headers,
        ).json()["id"]

        now = datetime.now(timezone.utc)
        # Synthetic forecast (bypasses Prophet via the engine seam): central value
        # crosses 100 in the 3rd hour.
        # First two stay fully inside the corridor (band included); the 3rd is the
        # first point to breach, with the central forecast crossing → high confidence.
        breach_points = [
            {"ts": now + timedelta(hours=1), "yhat": 80, "yhat_low": 70, "yhat_high": 90},
            {"ts": now + timedelta(hours=2), "yhat": 95, "yhat_low": 88, "yhat_high": 99},
            {"ts": now + timedelta(hours=3), "yhat": 130, "yhat_low": 120, "yhat_high": 140},
        ]
        try:
            res = predictive_engine.evaluate_indicator(
                ind_id, "default", breach_points, 24, metric,
                low=None, high=100.0, direction="above")
            assert res["status"] == "evaluated" and res["raised"] == 1

            alerts = integration_client.get(
                f"/api/v1/predictions/?indicator_id={ind_id}&active_only=true",
                headers=admin_headers).json()
            assert len(alerts) == 1
            alert = alerts[0]
            assert alert["direction"] == "above"
            assert alert["confidence"] == "high"          # central yhat=130 breaches
            assert alert["breach_eta"] is not None
            alert_id = alert["id"]

            # Forecast snapshot was stored for the cockpit.
            snap = integration_client.get(
                f"/api/v1/predictions/forecasts/{ind_id}/latest", headers=admin_headers)
            assert snap.status_code == 200
            assert len(snap.json()["points"]) == 3

            # Acknowledge.
            r = integration_client.post(f"/api/v1/predictions/{alert_id}/acknowledge",
                                        json={}, headers=admin_headers)
            assert r.status_code == 200 and r.json()["status"] == "acknowledged"

            # A later forecast that stays inside the corridor resolves the alert.
            safe_points = [{"ts": now + timedelta(hours=h), "yhat": 50, "yhat_low": 40, "yhat_high": 60}
                           for h in (1, 2, 3)]
            res2 = predictive_engine.evaluate_indicator(
                ind_id, "default", safe_points, 24, metric,
                low=None, high=100.0, direction="above")
            assert res2["resolved"] == 1
            assert integration_client.get(
                f"/api/v1/predictions/?indicator_id={ind_id}&active_only=true",
                headers=admin_headers).json() == []
        finally:
            integration_client.delete(f"/api/v1/indicators/{ind_id}", headers=admin_headers)


# ======================================================================
# M4 — Situation & Correlation (Orient / L2)
# ======================================================================
class TestSituationCorrelation:
    def test_dependency_correlates_deviations_into_situation(self, integration_client, admin_headers, db_engine):
        if not _tables_present(db_engine, "situations", "situation_deviations",
                               "indicator_dependencies", "deviations"):
            pytest.skip("M4 tables not found — migration 015 not applied")

        from core.deviation_engine import indicator_evaluator

        m1 = f"itest_sit_up_{uuid.uuid4().hex[:8]}"
        m2 = f"itest_sit_dn_{uuid.uuid4().hex[:8]}"

        def mk_indicator(name, metric):
            return integration_client.post(
                "/api/v1/indicators/",
                json={"name": name, "target_high": 100.0, "direction": "above",
                      "factors": [{"name": "f", "metrics": [metric]}]},
                headers=admin_headers,
            ).json()["id"]

        up_id = mk_indicator("upstream indicator", m1)
        dn_id = mk_indicator("downstream indicator", m2)

        # Dependency: upstream → downstream.
        dep = integration_client.post(
            "/api/v1/situations/dependencies",
            json={"src_indicator_id": up_id, "dst_indicator_id": dn_id, "weight": 2.0},
            headers=admin_headers)
        assert dep.status_code == 201, dep.text

        def seed(metric, value):
            with db_engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO canonical_metrics "
                         "(metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
                         "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'itest', 'default')"),
                    {"m": metric, "v": value},
                )

        sit_id = None
        try:
            # Both indicators breach in the same evaluation cycle → two open deviations.
            seed(m1, 150.0)
            seed(m2, 150.0)
            indicator_evaluator.evaluate_tenant("default")

            # Correlate via the API.
            summary = integration_client.post(
                "/api/v1/situations/correlate", json={"window_minutes": 30},
                headers=admin_headers).json()
            assert summary["clusters"] >= 1 and summary["created"] >= 1

            sits = integration_client.get(
                "/api/v1/situations/?active_only=true", headers=admin_headers).json()
            # Find the situation rooted at our upstream indicator.
            mine = [s for s in sits if s["root_cause_indicator_id"] == up_id]
            assert len(mine) == 1, f"expected one situation rooted at upstream, got {mine}"
            sit = mine[0]
            sit_id = sit["id"]
            assert sit["deviation_count"] == 2
            assert sit["impact_score"] > 0

            # Detail view carries both deviations + the root-cause hypothesis.
            detail = integration_client.get(
                f"/api/v1/situations/{sit_id}", headers=admin_headers).json()
            assert len(detail["deviations"]) == 2
            assert detail["root_cause_indicator_id"] == up_id
            assert "первопричина" in (detail["root_cause_hypothesis"] or "").lower()

            # Triage: move to investigating.
            r = integration_client.patch(
                f"/api/v1/situations/{sit_id}/status",
                json={"status": "investigating"}, headers=admin_headers)
            assert r.status_code == 200 and r.json()["status"] == "investigating"

            # Both deviations clear → correlation auto-resolves the situation.
            for m in (m1, m2):
                with db_engine.begin() as conn:
                    conn.execute(text("DELETE FROM canonical_metrics WHERE metric_name = :m"), {"m": m})
                seed(m, 50.0)
            indicator_evaluator.evaluate_tenant("default")
            res = integration_client.post(
                "/api/v1/situations/correlate", json={"window_minutes": 30},
                headers=admin_headers).json()
            assert res["resolved"] >= 1
            after = integration_client.get(
                f"/api/v1/situations/{sit_id}", headers=admin_headers).json()
            assert after["status"] == "resolved"
        finally:
            with db_engine.begin() as conn:
                for m in (m1, m2):
                    conn.execute(text("DELETE FROM canonical_metrics WHERE metric_name = :m"), {"m": m})
                if sit_id:
                    conn.execute(text("DELETE FROM situations WHERE id = :id"), {"id": sit_id})
            integration_client.delete(f"/api/v1/indicators/{up_id}", headers=admin_headers)
            integration_client.delete(f"/api/v1/indicators/{dn_id}", headers=admin_headers)
