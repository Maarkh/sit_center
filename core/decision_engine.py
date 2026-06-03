# core/decision_engine.py
"""DSS M10 — Decision Log & Learning Loop (Learn).

A decision is an accepted recommendation (M7). M10 records its OUTCOME (did it
resolve the situation, with what effect) and aggregates per-playbook win-rates that
feed back into recommendation ranking (Learn → Decide). Outcomes can be recorded by
an operator or auto-derived: a launched process (M8) that completed while the
originating deviation resolved counts as a win; a cancelled process or a still-open
deviation counts as a loss.

The win-rate math (compute_winrate / winrate_factor) is pure and unit-tested.
"""
from typing import Optional, Dict, List, Any
from sqlalchemy import text

from core.database import get_engine
from core.audit import log_audit
from config import logger, mask_secrets

# Below this many decided outcomes a playbook's win-rate is treated as unknown
# (neutral) so a thin history can't unfairly bury or boost it.
MIN_SAMPLES = 3


def compute_winrate(rows: List[Dict[str, Any]]) -> Dict[Any, Dict[str, Any]]:
    """rows: [{'playbook_id', 'decided', 'resolved'}] → per-playbook stats with win_rate."""
    out: Dict[Any, Dict[str, Any]] = {}
    for r in rows:
        decided = int(r["decided"])
        resolved = int(r["resolved"])
        out[r["playbook_id"]] = {
            "decided": decided,
            "resolved": resolved,
            "win_rate": round(resolved / decided, 4) if decided else None,
        }
    return out


def winrate_factor(win_rate: Optional[float], n_decided: int, min_samples: int = MIN_SAMPLES) -> float:
    """Score multiplier from a playbook's track record. Neutral (1.0) until there is
    enough history; then in [0.5, 1.5] — proven playbooks rank up, failing ones down."""
    if win_rate is None or n_decided < min_samples:
        return 1.0
    return round(0.5 + max(0.0, min(1.0, win_rate)), 4)


class DecisionEngine:
    def record_outcome(self, recommendation_id, tenant_id: str, *, resolved: bool,
                       effect_value: Optional[float] = None, note: Optional[str] = None,
                       user: Optional[str] = None, auto: bool = False) -> Optional[dict]:
        """Record (or correct) the outcome of an accepted recommendation. Returns None
        if the recommendation isn't an accepted decision. Auto mode never overwrites an
        existing (operator) outcome."""
        engine = get_engine()
        with engine.begin() as conn:
            rec = conn.execute(
                text("SELECT status FROM recommendations WHERE id = :id AND tenant_id = :tid"),
                {"id": recommendation_id, "tid": tenant_id},
            ).scalar()
            if rec != "accepted":
                return None
            if auto:
                conn.execute(
                    text("INSERT INTO decision_outcomes (tenant_id, recommendation_id, resolved, "
                         "effect_value, note, auto, evaluated_by) "
                         "VALUES (:tid, :rid, :res, :eff, :note, true, :by) "
                         "ON CONFLICT (recommendation_id) DO NOTHING"),
                    {"tid": tenant_id, "rid": recommendation_id, "res": resolved,
                     "eff": effect_value, "note": note, "by": user or "system"},
                )
            else:
                conn.execute(
                    text("INSERT INTO decision_outcomes (tenant_id, recommendation_id, resolved, "
                         "effect_value, note, auto, evaluated_by) "
                         "VALUES (:tid, :rid, :res, :eff, :note, false, :by) "
                         "ON CONFLICT (recommendation_id) DO UPDATE SET resolved = :res, "
                         "effect_value = :eff, note = :note, auto = false, evaluated_by = :by, "
                         "evaluated_at = NOW()"),
                    {"tid": tenant_id, "rid": recommendation_id, "res": resolved,
                     "eff": effect_value, "note": note, "by": user},
                )
            row = conn.execute(
                text("SELECT id, recommendation_id, resolved, effect_value, note, auto, "
                     "evaluated_by, evaluated_at FROM decision_outcomes WHERE recommendation_id = :rid"),
                {"rid": recommendation_id},
            ).mappings().first()
        if not auto:
            log_audit(user or "system", tenant_id, "outcome", "recommendation",
                      resource_id=str(recommendation_id))
        return dict(row) if row else None

    def auto_evaluate(self, tenant_id: str = "default") -> dict:
        """Derive outcomes for accepted decisions whose process has finished and which
        have no outcome yet. completed process + resolved deviation = win; else loss."""
        engine = get_engine()
        with engine.connect() as conn:
            pending = conn.execute(
                text("SELECT r.id, pi.status AS proc_status, d.status AS dev_status "
                     "FROM recommendations r "
                     "JOIN process_instances pi ON pi.id = r.process_instance_id "
                     "LEFT JOIN deviations d ON d.id = r.deviation_id "
                     "WHERE r.tenant_id = :tid AND r.status = 'accepted' "
                     "AND pi.status IN ('completed', 'cancelled') "
                     "AND NOT EXISTS (SELECT 1 FROM decision_outcomes o WHERE o.recommendation_id = r.id)"),
                {"tid": tenant_id},
            ).mappings().all()

        evaluated = 0
        for p in pending:
            resolved = p["proc_status"] == "completed" and (p["dev_status"] in (None, "resolved"))
            try:
                self.record_outcome(p["id"], tenant_id, resolved=resolved, auto=True,
                                    note="auto: process %s, deviation %s" % (p["proc_status"], p["dev_status"]))
                evaluated += 1
            except Exception as e:
                logger.error("auto outcome failed: %s", mask_secrets(str(e)))
        return {"evaluated": evaluated}

    def playbook_winrates(self, tenant_id: str) -> Dict[Any, Dict[str, Any]]:
        """Per-playbook {decided, resolved, win_rate} from recorded outcomes."""
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT r.playbook_id, COUNT(*) AS decided, "
                     "COUNT(*) FILTER (WHERE o.resolved) AS resolved "
                     "FROM recommendations r JOIN decision_outcomes o ON o.recommendation_id = r.id "
                     "WHERE r.tenant_id = :tid AND r.playbook_id IS NOT NULL "
                     "GROUP BY r.playbook_id"),
                {"tid": tenant_id},
            ).mappings().all()
        return compute_winrate([dict(r) for r in rows])

    def playbook_stats(self, playbook_id, tenant_id: str) -> dict:
        engine = get_engine()
        with engine.connect() as conn:
            accepted = conn.execute(
                text("SELECT COUNT(*) FROM recommendations WHERE tenant_id = :tid "
                     "AND playbook_id = :pid AND status = 'accepted'"),
                {"tid": tenant_id, "pid": playbook_id},
            ).scalar() or 0
            row = conn.execute(
                text("SELECT COUNT(*) AS decided, COUNT(*) FILTER (WHERE o.resolved) AS resolved "
                     "FROM recommendations r JOIN decision_outcomes o ON o.recommendation_id = r.id "
                     "WHERE r.tenant_id = :tid AND r.playbook_id = :pid"),
                {"tid": tenant_id, "pid": playbook_id},
            ).mappings().first()
        decided = int(row["decided"]) if row else 0
        resolved = int(row["resolved"]) if row else 0
        return {
            "playbook_id": playbook_id, "accepted": int(accepted), "decided": decided,
            "resolved": resolved,
            "win_rate": round(resolved / decided, 4) if decided else None,
        }

    def decision_log(self, tenant_id: str, limit: int = 100) -> List[dict]:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT r.id AS recommendation_id, r.playbook_id, p.name AS playbook_name, "
                     "r.deviation_id, r.incident_id, r.process_instance_id, r.score, r.confidence, "
                     "r.decided_by, r.decided_at, o.resolved, o.effect_value, o.auto AS outcome_auto, "
                     "o.evaluated_at FROM recommendations r "
                     "LEFT JOIN playbooks p ON p.id = r.playbook_id "
                     "LEFT JOIN decision_outcomes o ON o.recommendation_id = r.id "
                     "WHERE r.tenant_id = :tid AND r.status = 'accepted' "
                     "ORDER BY r.decided_at DESC NULLS LAST LIMIT :limit"),
                {"tid": tenant_id, "limit": limit},
            ).mappings().all()
        return [dict(r) for r in rows]


decision_engine = DecisionEngine()
