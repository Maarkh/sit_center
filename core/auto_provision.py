# core/auto_provision.py
"""B (zero-touch): auto-provision baseline indicators.

A metric flowing into canonical_metrics is just a number until an *indicator* watches
it against a corridor. Creating indicators by hand doesn't scale. This module, when a
metric has been flowing long enough to learn a "normal" band but has no indicator yet,
creates one with a self-tuning ``corridor_type='baseline'`` corridor (mean ± K·σ over
history, computed live by core/deviation_engine) plus the factor/factor_metrics wiring —
so deviations start without any manual setup.

Opt-in: a deploy must set AUTO_PROVISION_INDICATORS=true. Off by default so it never
surprises an operator by inventing indicators.
"""
import os

from sqlalchemy import text

from core.database import get_engine
from config import logger

AUTO_PROVISION_ENABLED = os.environ.get("AUTO_PROVISION_INDICATORS", "false").lower() in ("1", "true", "yes")
# A metric needs enough recent points before a baseline (mean±K·σ) is trustworthy.
MIN_POINTS = int(os.environ.get("AUTO_PROVISION_MIN_POINTS", "30"))
# History window the points are counted over (defaults to the baseline window: 7 days).
HISTORY_WINDOW_MIN = int(os.environ.get("AUTO_PROVISION_WINDOW_MIN", str(7 * 24 * 60)))
# The metric must still be LIVE (data within this window) — don't provision dead history.
ACTIVE_WINDOW_MIN = int(os.environ.get("AUTO_PROVISION_ACTIVE_MIN", str(24 * 60)))
# Safety cap per run so a fresh deploy with hundreds of metrics ramps up gradually.
MAX_PER_RUN = int(os.environ.get("AUTO_PROVISION_MAX_PER_RUN", "50"))
CHRONICLE_THRESHOLD = int(os.environ.get("AUTO_PROVISION_CHRONICLE", "3"))

_AUTO_DESC = "Авто-создан (zero-touch): самонастраивающийся коридор «норма ± K·σ» по истории метрики."


def _select_to_provision(candidates, covered, cap=MAX_PER_RUN):
    """Pure selection: from metric names that already meet the history/active thresholds
    (enforced in SQL), drop those already watched by an indicator and cap the batch.
    Deterministic order so reruns are stable."""
    out = [m for m in sorted(candidates) if m and m not in covered]
    return out[:cap]


def _covered_metrics(conn, tenant_id):
    """Metric names already watched by some active indicator (via factor_metrics)."""
    rows = conn.execute(
        text(
            "SELECT DISTINCT fm.metric_name FROM factor_metrics fm "
            "JOIN factors f ON f.id = fm.factor_id "
            "JOIN indicators i ON i.id = f.indicator_id "
            "WHERE i.tenant_id = :tid AND i.is_active = true"
        ),
        {"tid": tenant_id},
    ).scalars().all()
    return set(rows)


def _ready_metrics(conn, tenant_id):
    """Metric names with enough history AND still live (recent data)."""
    rows = conn.execute(
        text(
            "SELECT metric_name FROM canonical_metrics "
            "WHERE tenant_id = :tid AND timestamp >= NOW() - make_interval(mins => :win) "
            "GROUP BY metric_name "
            "HAVING COUNT(*) >= :minp AND MAX(timestamp) >= NOW() - make_interval(mins => :amin)"
        ),
        {"tid": tenant_id, "win": HISTORY_WINDOW_MIN, "minp": MIN_POINTS, "amin": ACTIVE_WINDOW_MIN},
    ).scalars().all()
    return list(rows)


def _catalog_meta(conn, tenant_id, names):
    """display_name + unit per metric from the catalog, for nicer indicator naming."""
    if not names:
        return {}
    rows = conn.execute(
        text(
            "SELECT metric_name, display_name, unit FROM metadata_metrics "
            "WHERE tenant_id = :tid AND metric_name = ANY(:names)"
        ),
        {"tid": tenant_id, "names": list(names)},
    ).mappings().all()
    return {r["metric_name"]: (r["display_name"], r["unit"]) for r in rows}


def provision_tenant(tenant_id: str = "default") -> dict:
    """Create baseline indicators for ready, uncovered metrics of one tenant.
    Returns {candidates, created, names}. Each new indicator gets one factor linking
    the single metric; the corridor is dynamic ('baseline'), so target_low/high stay NULL
    and are learned at evaluation time."""
    engine = get_engine()
    created = []
    with engine.begin() as conn:
        ready = _ready_metrics(conn, tenant_id)
        covered = _covered_metrics(conn, tenant_id)
        to_make = _select_to_provision(ready, covered)
        if not to_make:
            return {"candidates": 0, "created": 0, "names": []}
        meta = _catalog_meta(conn, tenant_id, to_make)
        for metric_name in to_make:
            disp, unit = meta.get(metric_name, (metric_name, ""))
            ind_id = conn.execute(
                text(
                    "INSERT INTO indicators (tenant_id, name, description, unit, corridor_type, "
                    "direction, chronicle_threshold, is_active) "
                    "VALUES (:tid, :name, :desc, :unit, 'baseline', 'both', :chron, true) RETURNING id"
                ),
                {"tid": tenant_id, "name": disp or metric_name, "desc": _AUTO_DESC,
                 "unit": unit or "", "chron": CHRONICLE_THRESHOLD},
            ).scalar()
            fid = conn.execute(
                text(
                    "INSERT INTO factors (tenant_id, indicator_id, name, weight) "
                    "VALUES (:tid, :iid, :name, 1.0) RETURNING id"
                ),
                {"tid": tenant_id, "iid": ind_id, "name": metric_name},
            ).scalar()
            conn.execute(
                text("INSERT INTO factor_metrics (factor_id, metric_name) VALUES (:fid, :m) "
                     "ON CONFLICT DO NOTHING"),
                {"fid": fid, "m": metric_name},
            )
            created.append(metric_name)
    if created:
        logger.info("Auto-provisioned %d baseline indicator(s) for tenant=%s: %s",
                    len(created), tenant_id, ", ".join(created))
    return {"candidates": len(to_make), "created": len(created), "names": created}
