# core/situation_engine.py
"""DSS M4 — Situation & Correlation (Orient / L2 Comprehension).

Correlates active deviations (M3) into Situations: two deviations join the same
situation when their indicators sit in the same connected component of the dependency
graph (or are the same indicator) AND they occurred within a time window. Each
situation gets an impact score (downstream influence) and a root-cause hypothesis
(the upstream-most breaching indicator).

The correlation math (correlate / compute_impact / root_cause) is pure and unit-tested.
"""
import os
from typing import List, Dict, Any, Optional, Iterable, Tuple
from sqlalchemy import text

from core.database import get_engine
from config import logger, mask_secrets

_SEV_WEIGHT = {"critical": 2.0, "warning": 1.0}

# correlate() is O(n²) in the open-deviation count (pairwise window/component test).
# Union-find keeps it cycle-safe, but a tenant storming thousands of simultaneous
# deviations would still make a single correlation tick quadratically expensive.
# Bound it to the most-recent N (the freshest deviations are the ones worth
# clustering now); anything beyond is logged, not silently dropped. Configurable.
MAX_CORRELATE_DEVIATIONS = int(os.environ.get("MAX_CORRELATE_DEVIATIONS", "2000"))


def correlate(deviations: List[Dict[str, Any]], edges: Iterable[Tuple], window_seconds: int) -> List[List[Dict[str, Any]]]:
    """Partition deviations into correlated clusters (incl. singletons).

    deviations: [{'id', 'indicator_id', 'detected_at'(datetime)}], edges: directed
    (src, dst) indicator pairs used undirected for connectivity. Two deviations join
    when their indicators share a dependency-graph component (or are equal) and they
    are within window_seconds of each other (transitively, via union-find)."""
    # Indicator connectivity (undirected components).
    iparent: Dict[Any, Any] = {}

    def ifind(x):
        iparent.setdefault(x, x)
        root = x
        while iparent[root] != root:
            root = iparent[root]
        while iparent[x] != root:
            iparent[x], x = root, iparent[x]
        return root

    def iunion(a, b):
        ra, rb = ifind(a), ifind(b)
        if ra != rb:
            iparent[ra] = rb

    for s, d in edges:
        iunion(s, d)

    def same_component(i1, i2) -> bool:
        if i1 == i2:
            return True
        if i1 in iparent and i2 in iparent:
            return ifind(i1) == ifind(i2)
        return False

    # Union-find over deviations.
    n = len(deviations)
    dparent = list(range(n))

    def dfind(x):
        while dparent[x] != x:
            dparent[x] = dparent[dparent[x]]
            x = dparent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            di, dj = deviations[i], deviations[j]
            if not same_component(di["indicator_id"], dj["indicator_id"]):
                continue
            if abs((di["detected_at"] - dj["detected_at"]).total_seconds()) <= window_seconds:
                ri, rj = dfind(i), dfind(j)
                if ri != rj:
                    dparent[ri] = rj

    clusters: Dict[int, List[Dict[str, Any]]] = {}
    for i in range(n):
        clusters.setdefault(dfind(i), []).append(deviations[i])
    return list(clusters.values())


def compute_impact(items: List[Tuple[Any, str]], out_weight: Dict[Any, float]) -> float:
    """Impact = Σ severity_weight × (1 + downstream influence of the indicator).
    items: [(indicator_id, severity)]; out_weight: indicator → Σ outgoing edge weight."""
    total = 0.0
    for indicator_id, severity in items:
        total += _SEV_WEIGHT.get(severity, 1.0) * (1.0 + out_weight.get(indicator_id, 0.0))
    return round(total, 4)


def root_cause(indicators: Iterable[Any], directed_edges: Iterable[Tuple],
               earliest_by_indicator: Dict[Any, Any]) -> Optional[Any]:
    """The likely root cause: the upstream-most breaching indicator in the cluster
    (a dependency source with no breaching upstream), tie-broken by earliest detection.
    Falls back to the earliest-detected indicator when the cluster has no internal edges."""
    ind_set = set(indicators)
    if not ind_set:
        return None
    internal = [(s, d) for (s, d) in directed_edges if s in ind_set and d in ind_set]
    has_incoming = {d for (_, d) in internal}
    sources = [i for i in ind_set if i not in has_incoming and any(s == i for (s, _) in internal)]
    candidates = sources if sources else list(ind_set)
    return min(candidates, key=lambda i: earliest_by_indicator.get(i))


class SituationEngine:
    def correlate_tenant(self, tenant_id: str = "default", window_minutes: int = 30) -> dict:
        engine = get_engine()
        summary = {"clusters": 0, "created": 0, "updated": 0, "resolved": 0}
        with engine.connect() as conn:
            devs = conn.execute(
                text("SELECT id, indicator_id, severity, detected_at FROM deviations "
                     "WHERE tenant_id = :tid AND status <> 'resolved' "
                     "ORDER BY detected_at DESC LIMIT :lim"),
                {"tid": tenant_id, "lim": MAX_CORRELATE_DEVIATIONS},
            ).mappings().all()
            if len(devs) >= MAX_CORRELATE_DEVIATIONS:
                logger.warning(
                    "tenant %s has ≥%d open deviations; correlating only the %d most recent "
                    "this tick (raise MAX_CORRELATE_DEVIATIONS to widen)",
                    tenant_id, MAX_CORRELATE_DEVIATIONS, MAX_CORRELATE_DEVIATIONS,
                )
            edges = conn.execute(
                text("SELECT src_indicator_id, dst_indicator_id, weight FROM indicator_dependencies "
                     "WHERE tenant_id = :tid"),
                {"tid": tenant_id},
            ).mappings().all()

        deviations = [{"id": d["id"], "indicator_id": d["indicator_id"],
                       "severity": d["severity"], "detected_at": d["detected_at"]} for d in devs]
        directed = [(e["src_indicator_id"], e["dst_indicator_id"]) for e in edges]
        out_weight: Dict[Any, float] = {}
        for e in edges:
            out_weight[e["src_indicator_id"]] = out_weight.get(e["src_indicator_id"], 0.0) + float(e["weight"])

        clusters = [c for c in correlate(deviations, directed, window_minutes * 60) if len(c) >= 2]
        summary["clusters"] = len(clusters)

        for cluster in clusters:
            try:
                created = self._upsert_situation(tenant_id, cluster, directed, out_weight)
                summary["created" if created else "updated"] += 1
            except Exception as e:
                logger.error("situation upsert failed: %s", mask_secrets(str(e)))

        summary["resolved"] = self._auto_resolve(tenant_id)
        return summary

    def _upsert_situation(self, tenant_id, cluster, directed, out_weight) -> bool:
        dev_ids = [d["id"] for d in cluster]
        indicators = {d["indicator_id"] for d in cluster}
        earliest = {}
        for d in cluster:
            cur = earliest.get(d["indicator_id"])
            if cur is None or d["detected_at"] < cur:
                earliest[d["indicator_id"]] = d["detected_at"]

        impact = compute_impact([(d["indicator_id"], d["severity"]) for d in cluster], out_weight)
        rc_indicator = root_cause(indicators, directed, earliest)

        engine = get_engine()
        with engine.begin() as conn:
            rc_name = conn.execute(
                text("SELECT name FROM indicators WHERE id = :id"), {"id": rc_indicator},
            ).scalar() if rc_indicator else None
            title = f"Ситуация: {rc_name or 'коррелированные отклонения'} (+{len(indicators) - 1})"
            hypothesis = (
                f"Вероятная первопричина — показатель '{rc_name}' (выше по графу зависимостей); "
                f"затронуто {len(indicators)} связанных показателей, {len(dev_ids)} отклонений."
                if rc_name else
                f"Коррелированы {len(dev_ids)} отклонений по {len(indicators)} показателям (по времени)."
            )

            # Reuse an existing active situation that already links any of these deviations.
            existing = conn.execute(
                text("SELECT DISTINCT s.id FROM situations s "
                     "JOIN situation_deviations sd ON sd.situation_id = s.id "
                     "WHERE s.tenant_id = :tid AND s.status IN ('open', 'investigating') "
                     "AND sd.deviation_id = ANY(:devs) ORDER BY s.id LIMIT 1"),
                {"tid": tenant_id, "devs": dev_ids},
            ).scalar()

            created = existing is None
            if created:
                sit_id = conn.execute(
                    text("INSERT INTO situations (tenant_id, title, root_cause_indicator_id, "
                         "root_cause_hypothesis, impact_score, status, deviation_count) "
                         "VALUES (:tid, :title, :rc, :hyp, :impact, 'open', :cnt) RETURNING id"),
                    {"tid": tenant_id, "title": title, "rc": rc_indicator, "hyp": hypothesis,
                     "impact": impact, "cnt": len(dev_ids)},
                ).scalar()
            else:
                sit_id = existing
                conn.execute(
                    text("UPDATE situations SET title = :title, root_cause_indicator_id = :rc, "
                         "root_cause_hypothesis = :hyp, impact_score = :impact WHERE id = :id"),
                    {"title": title, "rc": rc_indicator, "hyp": hypothesis, "impact": impact, "id": sit_id},
                )

            for dev_id in dev_ids:
                conn.execute(
                    text("INSERT INTO situation_deviations (situation_id, deviation_id) "
                         "VALUES (:sid, :did) ON CONFLICT DO NOTHING"),
                    {"sid": sit_id, "did": dev_id},
                )
            # Keep the linked-deviation count in sync.
            conn.execute(
                text("UPDATE situations SET deviation_count = "
                     "(SELECT count(*) FROM situation_deviations WHERE situation_id = :id) WHERE id = :id"),
                {"id": sit_id},
            )
            if created:
                self._notify(conn, title, impact, hypothesis)
        return created

    def _auto_resolve(self, tenant_id) -> int:
        """Resolve active situations all of whose linked deviations are resolved."""
        engine = get_engine()
        with engine.begin() as conn:
            ids = conn.execute(
                text("SELECT s.id FROM situations s WHERE s.tenant_id = :tid "
                     "AND s.status IN ('open', 'investigating') AND NOT EXISTS ("
                     "  SELECT 1 FROM situation_deviations sd JOIN deviations d ON d.id = sd.deviation_id "
                     "  WHERE sd.situation_id = s.id AND d.status <> 'resolved')"),
                {"tid": tenant_id},
            ).scalars().all()
            for sit_id in ids:
                conn.execute(
                    text("UPDATE situations SET status = 'resolved', closed_at = NOW() WHERE id = :id"),
                    {"id": sit_id},
                )
        return len(ids)

    def _notify(self, conn, title, impact, hypothesis):
        priority = "critical" if impact >= 4.0 else "warning"
        try:
            from core.notifications import notify
            notify(f"{title} — impact {impact}. {hypothesis}", priority, event_type="situation")
        except Exception as e:
            logger.error("situation notify failed: %s", mask_secrets(str(e)))


situation_engine = SituationEngine()
