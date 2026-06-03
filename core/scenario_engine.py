# core/scenario_engine.py
"""DSS M6 — Model & Scenario Management / what-if (Model subsystem).

A scenario applies assumptions ("indicator X → target / delta") and projects each
assumed indicator against its corridor (M2). The POTENTIAL is the impact avoided
(severity × downstream influence, reusing M4's weighting) when an assumption removes
a breach — letting a decision-maker compare "what if we act on X".

apply_assumption / evaluate_scenario are pure and unit-tested. run_scenario wires in
the live indicator values and dependency graph.
"""
import json
from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlalchemy import text

from core.database import get_engine
from core.deviation_engine import classify_breach, breach_severity

_SEV_WEIGHT = {"critical": 2.0, "warning": 1.0}


def apply_assumption(baseline: Optional[float], mode: str, value: float) -> Optional[float]:
    """Projected indicator value after the assumption. None baseline stays None
    (can't project without a current value), except for an absolute 'target'."""
    if mode == "target":
        return value
    if baseline is None:
        return None
    if mode == "delta":
        return baseline + value
    if mode == "delta_pct":
        return baseline * (1.0 + value / 100.0)
    return baseline


def evaluate_scenario(indicators: List[Dict[str, Any]], assumptions: Dict[Any, Dict[str, Any]]) -> Dict[str, Any]:
    """Pure what-if evaluation.

    indicators: [{id, value(baseline|None), low, high, direction, downstream_weight}].
    assumptions: {indicator_id: {'mode', 'value'}}.
    Returns per-indicator results + potential_value (avoided impact) + breaches_avoided."""
    results: List[Dict[str, Any]] = []
    potential = 0.0
    avoided = 0
    for ind in indicators:
        baseline = ind["value"]
        a = assumptions.get(ind["id"])
        projected = apply_assumption(baseline, a["mode"], a["value"]) if a else baseline

        b_breach = classify_breach(baseline, ind["low"], ind["high"], ind["direction"]) if baseline is not None else None
        p_breach = classify_breach(projected, ind["low"], ind["high"], ind["direction"]) if projected is not None else None
        improved = b_breach is not None and p_breach is None
        worsened = b_breach is None and p_breach is not None

        if improved:
            sev = breach_severity(baseline, ind["low"], ind["high"], b_breach)
            potential += _SEV_WEIGHT.get(sev, 1.0) * (1.0 + float(ind.get("downstream_weight", 0.0)))
            avoided += 1

        results.append({
            "indicator_id": ind["id"], "indicator_name": ind.get("name"),
            "baseline": baseline, "projected": projected,
            "baseline_breach": b_breach, "projected_breach": p_breach,
            "improved": improved, "worsened": worsened,
        })
    return {"results": results, "potential_value": round(potential, 4), "breaches_avoided": avoided}


class ScenarioEngine:
    def run_scenario(self, scenario_id, tenant_id: str) -> Optional[dict]:
        """Evaluate a stored scenario against live indicator values; persist a result."""
        engine = get_engine()
        with engine.connect() as conn:
            sc = conn.execute(
                text("SELECT assumptions FROM scenarios WHERE id = :id AND tenant_id = :tid"),
                {"id": scenario_id, "tid": tenant_id},
            ).mappings().first()
        if not sc:
            return None

        assumptions_list = sc["assumptions"] or []
        if isinstance(assumptions_list, str):
            assumptions_list = json.loads(assumptions_list)
        # Keys as UUID so they match the indicator rows loaded from the DB (and so the
        # = ANY(:ids) lookup compares uuid = uuid, not uuid = text).
        assumptions = {UUID(str(a["indicator_id"])): {"mode": a.get("mode", "target"), "value": a["value"]}
                       for a in assumptions_list}

        indicators = self._load_indicator_states(tenant_id, list(assumptions.keys()))
        evaluated = evaluate_scenario(indicators, assumptions)

        engine = get_engine()
        with engine.begin() as conn:
            row = conn.execute(
                text("INSERT INTO scenario_results (tenant_id, scenario_id, results, "
                     "potential_value, breaches_avoided) "
                     "VALUES (:tid, :sid, CAST(:res AS jsonb), :pot, :avoided) "
                     "RETURNING id, computed_at"),
                {"tid": tenant_id, "sid": scenario_id,
                 "res": json.dumps(_jsonable(evaluated["results"])),
                 "pot": evaluated["potential_value"], "avoided": evaluated["breaches_avoided"]},
            ).mappings().first()

        return {
            "id": row["id"], "scenario_id": scenario_id, "computed_at": row["computed_at"],
            "results": evaluated["results"], "potential_value": evaluated["potential_value"],
            "breaches_avoided": evaluated["breaches_avoided"],
        }

    def _load_indicator_states(self, tenant_id: str, indicator_ids: list) -> List[Dict[str, Any]]:
        if not indicator_ids:
            return []
        from core.deviation_engine import indicator_evaluator, WINDOW_MINUTES
        engine = get_engine()
        states: List[Dict[str, Any]] = []
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, name, target_low, target_high, direction FROM indicators "
                     "WHERE tenant_id = :tid AND id = ANY(:ids)"),
                {"tid": tenant_id, "ids": indicator_ids},
            ).mappings().all()
            # Downstream influence per indicator (Σ outgoing edge weights) — M4 graph.
            weights = {}
            for w in conn.execute(
                text("SELECT src_indicator_id, SUM(weight) AS w FROM indicator_dependencies "
                     "WHERE tenant_id = :tid GROUP BY src_indicator_id"),
                {"tid": tenant_id},
            ).mappings().all():
                weights[w["src_indicator_id"]] = float(w["w"])

        for r in rows:
            value = indicator_evaluator._indicator_value(r["id"], tenant_id, WINDOW_MINUTES)
            states.append({
                "id": r["id"], "name": r["name"], "value": value,
                "low": float(r["target_low"]) if r["target_low"] is not None else None,
                "high": float(r["target_high"]) if r["target_high"] is not None else None,
                "direction": r["direction"], "downstream_weight": weights.get(r["id"], 0.0),
            })
        return states


def _jsonable(results):
    # UUIDs in indicator_id → str for jsonb storage.
    out = []
    for r in results:
        d = dict(r)
        d["indicator_id"] = str(d["indicator_id"])
        out.append(d)
    return out


scenario_engine = ScenarioEngine()
