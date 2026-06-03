# core/recommendation_engine.py
"""DSS M7 — Knowledge Base & Recommendation (Design + Choice / Next-Best-Action).

Given a deviation (M3) or incident, find matching playbooks, score them as ranked
alternatives, and persist them as recommendations. Accepting one instantiates its
process (M8) bound to the same situation and records the decision (proto-M10).

Scoring (score_playbook) and confidence (match_confidence) are pure and unit-tested.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import text

from core.database import get_engine

# Map incident priority → the severity vocabulary playbooks match on.
_PRIORITY_TO_SEVERITY = {"critical": "critical", "high": "critical",
                         "medium": "warning", "low": "warning"}


def score_playbook(
    effect_score: float,
    severity: str,
    periods: int,
    *,
    indicator_scoped: bool,
    winrate_factor: float = 1.0,
) -> float:
    """Rank score. Higher effect, critical severity, longer-running (chronicle) and
    indicator-specific playbooks rank above generic, low-effect ones. `winrate_factor`
    (default 1.0 = neutral) folds in the playbook's learned track record (M10)."""
    severity_factor = 1.5 if severity == "critical" else 1.0
    # Persistence: a breach that has lasted many cycles is more urgent to act on.
    persistence_factor = 1.0 + 0.1 * min(max(periods - 1, 0), 10)
    specificity_bonus = 0.5 if indicator_scoped else 0.0
    base = effect_score * severity_factor * persistence_factor + specificity_bonus
    return round(base * winrate_factor, 4)


def match_confidence(
    *,
    severity_match: bool,
    direction_match: bool,
    indicator_scoped: bool,
) -> float:
    """How well the playbook's trigger rules pin this specific situation (0..1).
    A generic any/any/all-indicators playbook is a weak match; an exact
    severity+direction+indicator playbook is a strong one."""
    c = 0.4
    if severity_match:
        c += 0.25
    if direction_match:
        c += 0.2
    if indicator_scoped:
        c += 0.15
    return round(min(c, 1.0), 4)


class RecommendationEngine:
    def generate(self, tenant_id: str, *, deviation_id=None, incident_id: Optional[int] = None) -> List[dict]:
        """(Re)generate ranked recommendations for a deviation or incident. Replaces
        prior *proposed* rows (accepted/dismissed decisions are preserved)."""
        ctx = self._situation_context(tenant_id, deviation_id, incident_id)
        if ctx is None:
            from core.process_engine import ProcessError
            raise ProcessError("deviation/incident not found")

        candidates = self._candidate_playbooks(tenant_id, ctx)
        # Learned track record per playbook (M10 Learn → Decide feedback).
        from core.decision_engine import decision_engine, winrate_factor
        winrates = decision_engine.playbook_winrates(tenant_id)
        scored = []
        for pb in candidates:
            indicator_scoped = pb["_scoped"]
            severity_match = pb["trigger_severity"] is not None and pb["trigger_severity"] == ctx["severity"]
            direction_match = (
                pb["trigger_direction"] is not None
                and ctx["direction"] is not None
                and pb["trigger_direction"] == ctx["direction"]
            )
            wr = winrates.get(pb["id"])
            wf = winrate_factor(wr["win_rate"], wr["decided"]) if wr else 1.0
            score = score_playbook(float(pb["effect_score"]), ctx["severity"], ctx["periods"],
                                   indicator_scoped=indicator_scoped, winrate_factor=wf)
            confidence = match_confidence(severity_match=severity_match,
                                          direction_match=direction_match,
                                          indicator_scoped=indicator_scoped)
            scored.append({
                "playbook_id": pb["id"], "playbook_name": pb["name"],
                "score": score, "confidence": confidence,
                "rationale": self._rationale(pb, ctx, indicator_scoped, severity_match, direction_match),
                "has_process": pb["process_template_id"] is not None,
            })

        scored.sort(key=lambda r: (-r["score"], -r["confidence"], r["playbook_name"]))

        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM recommendations WHERE tenant_id = :tid AND status = 'proposed' "
                     "AND deviation_id IS NOT DISTINCT FROM :dev AND incident_id IS NOT DISTINCT FROM :inc"),
                {"tid": tenant_id, "dev": deviation_id, "inc": incident_id},
            )
            out = []
            for rank, r in enumerate(scored, start=1):
                row = conn.execute(
                    text(
                        "INSERT INTO recommendations (tenant_id, deviation_id, incident_id, playbook_id, "
                        "rank, score, confidence, rationale, status) "
                        "VALUES (:tid, :dev, :inc, :pb, :rank, :score, :conf, :rat, 'proposed') "
                        "RETURNING id, created_at"
                    ),
                    {"tid": tenant_id, "dev": deviation_id, "inc": incident_id, "pb": r["playbook_id"],
                     "rank": rank, "score": r["score"], "conf": r["confidence"], "rat": r["rationale"]},
                ).mappings().first()
                out.append({**r, "id": row["id"], "rank": rank, "created_at": row["created_at"],
                            "status": "proposed", "deviation_id": deviation_id, "incident_id": incident_id})
        return out

    def accept(self, recommendation_id, tenant_id: str, *, user: str) -> dict:
        """Accept a recommendation: instantiate its playbook's process (if any) bound
        to the same situation, mark accepted, and dismiss the sibling proposals."""
        from core.process_engine import process_engine, ProcessError

        engine = get_engine()
        with engine.connect() as conn:
            rec = conn.execute(
                text("SELECT r.id, r.status, r.deviation_id, r.incident_id, r.playbook_id, "
                     "p.process_template_id, p.name AS playbook_name "
                     "FROM recommendations r LEFT JOIN playbooks p ON p.id = r.playbook_id "
                     "WHERE r.id = :id AND r.tenant_id = :tid"),
                {"id": recommendation_id, "tid": tenant_id},
            ).mappings().first()
        if not rec:
            raise ProcessError("recommendation not found")
        if rec["status"] != "proposed":
            raise ProcessError(f"recommendation already {rec['status']}")

        # Instantiate the process first (own transaction); roll it back by cancelling
        # if we then lose the accept race.
        instance_id = None
        if rec["process_template_id"]:
            instance_id = process_engine.instantiate(
                rec["process_template_id"], tenant_id, started_by=user,
                title=f"NBA: {rec['playbook_name']}",
                incident_id=rec["incident_id"], deviation_id=rec["deviation_id"],
            )

        with engine.begin() as conn:
            updated = conn.execute(
                text("UPDATE recommendations SET status = 'accepted', process_instance_id = :pi, "
                     "decided_by = :user, decided_at = NOW() "
                     "WHERE id = :id AND tenant_id = :tid AND status = 'proposed' RETURNING id"),
                {"id": recommendation_id, "tid": tenant_id, "pi": instance_id, "user": user},
            ).first()
            if not updated:
                # Lost the race — undo the orphan process instance.
                if instance_id:
                    try:
                        process_engine.cancel_instance(instance_id, tenant_id, user=user)
                    except Exception:
                        pass
                raise ProcessError("recommendation already decided")
            # Sibling proposals for the same situation are now moot.
            conn.execute(
                text("UPDATE recommendations SET status = 'dismissed', decided_by = :user, "
                     "decided_at = NOW() WHERE tenant_id = :tid AND status = 'proposed' AND id <> :id "
                     "AND deviation_id IS NOT DISTINCT FROM :dev AND incident_id IS NOT DISTINCT FROM :inc"),
                {"tid": tenant_id, "id": recommendation_id, "user": user,
                 "dev": rec["deviation_id"], "inc": rec["incident_id"]},
            )
        return {"process_instance_id": instance_id}

    # -- helpers -----------------------------------------------------------
    def _situation_context(self, tenant_id, deviation_id, incident_id) -> Optional[Dict[str, Any]]:
        engine = get_engine()
        with engine.connect() as conn:
            if deviation_id is not None:
                d = conn.execute(
                    text("SELECT indicator_id, severity, direction, periods FROM deviations "
                         "WHERE id = :id AND tenant_id = :tid"),
                    {"id": deviation_id, "tid": tenant_id},
                ).mappings().first()
                if not d:
                    return None
                return {"indicator_id": d["indicator_id"], "severity": d["severity"],
                        "direction": d["direction"], "periods": d["periods"]}
            inc = conn.execute(
                text("SELECT priority FROM incidents WHERE id = :id AND tenant_id = :tid"),
                {"id": incident_id, "tid": tenant_id},
            ).mappings().first()
            if not inc:
                return None
            return {"indicator_id": None,
                    "severity": _PRIORITY_TO_SEVERITY.get(inc["priority"], "warning"),
                    "direction": None, "periods": 1}

    def _candidate_playbooks(self, tenant_id, ctx) -> List[dict]:
        engine = get_engine()
        indicator_id = ctx["indicator_id"]
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT p.id, p.name, p.trigger_severity, p.trigger_direction, p.effect_score, "
                    "p.process_template_id, "
                    "EXISTS (SELECT 1 FROM playbook_indicators pi WHERE pi.playbook_id = p.id) AS has_scope, "
                    "EXISTS (SELECT 1 FROM playbook_indicators pi WHERE pi.playbook_id = p.id "
                    "        AND pi.indicator_id = :iid) AS matches_indicator "
                    "FROM playbooks p WHERE p.tenant_id = :tid AND p.is_active = true "
                    "AND (p.trigger_severity IS NULL OR p.trigger_severity = :sev) "
                    "AND (p.trigger_direction IS NULL OR p.trigger_direction = :dir)"
                ),
                {"tid": tenant_id, "iid": indicator_id, "sev": ctx["severity"], "dir": ctx["direction"]},
            ).mappings().all()

        candidates = []
        for r in rows:
            has_scope = r["has_scope"]
            matches_indicator = r["matches_indicator"]
            # Scoped playbook only applies if this situation's indicator is in scope.
            if has_scope and not matches_indicator:
                continue
            d = dict(r)
            d["_scoped"] = bool(has_scope and matches_indicator)
            candidates.append(d)
        return candidates

    def _rationale(self, pb, ctx, indicator_scoped, severity_match, direction_match) -> str:
        bits = []
        if indicator_scoped:
            bits.append("привязан к показателю")
        if severity_match:
            bits.append(f"severity={ctx['severity']}")
        if direction_match:
            bits.append(f"direction={ctx['direction']}")
        if ctx["periods"] > 1:
            bits.append(f"длится {ctx['periods']} периодов")
        scope = ", ".join(bits) if bits else "общий playbook"
        proc = " → запускает регламент" if pb["process_template_id"] else ""
        return f"Подходит: {scope}{proc}"


recommendation_engine = RecommendationEngine()
