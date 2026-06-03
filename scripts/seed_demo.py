#!/usr/bin/env python
"""Seed a full DSS demo scenario so every cockpit tab has data.

Prereqs: the API must be running (default http://localhost:8000) and this process
must see the same DATABASE_URL / REDIS_* env as the API (it calls the evaluation
engines directly for deviations & forecasts).

Usage:
    # with the project's env exported (DATABASE_URL, REDIS_*, SECRET_KEY, ADMIN_*):
    PYTHONPATH=. python scripts/seed_demo.py
    # optional override:
    SEED_API_BASE=http://localhost:8000 PYTHONPATH=. python scripts/seed_demo.py

Seeds: a goal with 3 indicators (2 dependency-linked + breaching, 1 healthy), a
process template + 2 playbooks, drives the indicators to chronic deviations (which
auto-generate recommendations), correlates them into a situation, accepts the top
recommendation (launching a process), raises a predictive alert with a forecast, and
creates + runs a what-if scenario.
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

BASE = os.environ.get("SEED_API_BASE", "http://localhost:8000")
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.environ.get("DEMO_ADMIN_PASSWORD", "admin")


def _login() -> str:
    body = f"username={ADMIN_USER}&password={ADMIN_PASS}".encode()
    req = urllib.request.Request(BASE + "/token", data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as r:
        return json.load(r)["access_token"]


TOKEN = _login()


def api(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, (json.load(r) if r.length != 0 else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def main():
    _, goal = api("POST", "/api/v1/indicators/goals", {"name": "Доступность ЦОД", "owner_role": "ops-lead"})
    gid = goal["id"]

    _, up = api("POST", "/api/v1/indicators/", {
        "name": "Сеть ядра ЦОД", "unit": "%", "goal_id": gid, "target_low": 0.0, "target_high": 100.0,
        "direction": "above", "chronicle_threshold": 2,
        "factors": [{"name": "потери пакетов", "metrics": ["core_packet_loss"]}]})
    up_id = up["id"]
    _, dn = api("POST", "/api/v1/indicators/", {
        "name": "Портал услуг", "unit": "%", "goal_id": gid, "target_low": 0.0, "target_high": 100.0,
        "direction": "above", "chronicle_threshold": 2,
        "factors": [{"name": "ошибки 5xx", "metrics": ["portal_error_rate"]}]})
    dn_id = dn["id"]
    api("POST", "/api/v1/indicators/", {
        "name": "Электропитание", "unit": "%", "goal_id": gid, "target_low": 0.0, "target_high": 100.0,
        "direction": "above", "factors": [{"name": "нагрузка", "metrics": ["power_load"]}]})

    api("POST", "/api/v1/situations/dependencies",
        {"src_indicator_id": up_id, "dst_indicator_id": dn_id, "weight": 2.0})

    _, tmpl = api("POST", "/api/v1/processes/templates", {
        "name": "Локализация сетевого сбоя", "steps": [
            {"name": "Диагностика ядра", "step_order": 0, "assignee_role": "L1",
             "checklist": ["проверить линки", "проверить BGP"], "due_after_minutes": 15},
            {"name": "Переключение на резерв", "step_order": 1, "assignee_role": "L2"}]})
    tmpl_id = tmpl["id"]
    _, pb = api("POST", "/api/v1/playbooks", {
        "name": "Сетевой сбой → переключение на резерв", "trigger_severity": "critical",
        "trigger_direction": "above", "effect_score": 3.0, "process_template_id": tmpl_id,
        "indicator_ids": [up_id], "actions": [{"action": "переключить на резерв", "checklist": ["уведомить дежурного"]}]})
    pb_id = pb["id"]
    api("POST", "/api/v1/playbooks", {"name": "Общая эскалация на L2", "effect_score": 1.0})

    # Deviations (engine writes them; chronic crossing auto-generates recommendations).
    from sqlalchemy import text
    from core.database import get_engine
    eng = get_engine()
    with eng.begin() as c:
        for metric, val in [("core_packet_loss", 150.0), ("portal_error_rate", 140.0), ("power_load", 60.0)]:
            for _ in range(3):
                c.execute(text(
                    "INSERT INTO canonical_metrics (metric_name, value, timestamp, dimensions, tags, source, tenant_id) "
                    "VALUES (:m, :v, NOW(), '{}'::jsonb, '{}'::jsonb, 'demo', 'default')"), {"m": metric, "v": val})

    from core.deviation_engine import indicator_evaluator
    indicator_evaluator.evaluate_tenant("default")
    indicator_evaluator.evaluate_tenant("default")

    api("POST", "/api/v1/situations/correlate", {"window_minutes": 30})

    # Accept the auto-generated targeted recommendation → launches a process + a decision.
    _, devs = api("GET", f"/api/v1/deviations/?indicator_id={up_id}&active_only=true")
    if devs:
        _, recos = api("GET", f"/api/v1/recommendations?deviation_id={devs[0]['id']}")
        targeted = next((r for r in (recos or []) if r["playbook_id"] == pb_id and r["status"] == "proposed"), None)
        if targeted:
            api("POST", f"/api/v1/recommendations/{targeted['id']}/accept", {})

    # Predictive alert + forecast snapshot.
    from core.predictive_engine import predictive_engine
    now = datetime.now(timezone.utc)
    pts = [{"ts": now + timedelta(hours=h), "yhat": y, "yhat_low": y - 10, "yhat_high": y + 10}
           for h, y in [(1, 80), (2, 95), (3, 130)]]
    predictive_engine.evaluate_indicator(up_id, "default", pts, 24, "core_packet_loss",
                                         low=0.0, high=100.0, direction="above")

    # What-if scenario.
    _, scn = api("POST", "/api/v1/scenarios/", {
        "name": "Снизить потери ядра до 50",
        "assumptions": [{"indicator_id": up_id, "mode": "target", "value": 50.0}]})
    api("POST", f"/api/v1/scenarios/{scn['id']}/run", {})

    _, sits = api("GET", "/api/v1/situations/?active_only=true")
    _, insts = api("GET", "/api/v1/processes/instances")
    _, decisions = api("GET", "/api/v1/recommendations/decisions")
    _, palerts = api("GET", "/api/v1/predictions/?active_only=true")
    _, scens = api("GET", "/api/v1/scenarios/")
    print(f"✅ DSS demo seeded: situations={len(sits)} processes={len(insts)} "
          f"decisions={len(decisions)} predictive={len(palerts)} scenarios={len(scens)}")


if __name__ == "__main__":
    main()
