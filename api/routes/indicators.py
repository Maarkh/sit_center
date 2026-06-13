# api/routes/indicators.py
"""DSS M2 — Indicator & Goal Model.

CRUD for the Goal → Indicator → Factor → Metric hierarchy plus subscriptions and a
tree view for the decision cockpit. Direct-DB access (mirrors api/routes/incidents.py);
every query is scoped by tenant_id.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text

from core.database import get_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import mask_secrets, logger
from api.schemas_dss import (
    GoalCreate, GoalUpdate, GoalRead,
    IndicatorCreate, IndicatorUpdate, IndicatorRead,
    FactorCreate, FactorRead,
    SubscriptionCreate, SubscriptionRead,
    IndicatorTreeResponse, GoalTreeNode, IndicatorTreeNode,
)

router = APIRouter(prefix="/indicators", tags=["DSS: Indicators"])

_IND_COLS = """
    id, goal_id, name, description, unit, target_low, target_high, corridor_type,
    baseline_model_ref, direction, chronicle_threshold, is_active,
    owner_role, owner_user, escalation_chain_id, created_at, updated_at
"""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _load_factors(conn, indicator_id) -> List[FactorRead]:
    rows = conn.execute(
        text("SELECT id, name, weight FROM factors WHERE indicator_id = :iid ORDER BY created_at"),
        {"iid": indicator_id},
    ).mappings().all()
    factors: List[FactorRead] = []
    for r in rows:
        metrics = conn.execute(
            text("SELECT metric_name FROM factor_metrics WHERE factor_id = :fid ORDER BY metric_name"),
            {"fid": r["id"]},
        ).scalars().all()
        factors.append(FactorRead(id=r["id"], name=r["name"], weight=float(r["weight"]), metrics=list(metrics)))
    return factors


def _row_to_indicator(conn, row) -> IndicatorRead:
    return IndicatorRead(
        id=row["id"],
        goal_id=row["goal_id"],
        name=row["name"],
        description=row["description"],
        unit=row["unit"] or "",
        target_low=float(row["target_low"]) if row["target_low"] is not None else None,
        target_high=float(row["target_high"]) if row["target_high"] is not None else None,
        corridor_type=row["corridor_type"],
        baseline_model_ref=row["baseline_model_ref"],
        direction=row["direction"],
        chronicle_threshold=row["chronicle_threshold"],
        is_active=row["is_active"],
        owner_role=row["owner_role"],
        owner_user=row["owner_user"],
        escalation_chain_id=row["escalation_chain_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        factors=_load_factors(conn, row["id"]),
    )


def _insert_factor(conn, indicator_id, tenant_id: str, factor: FactorCreate):
    fid = conn.execute(
        text(
            "INSERT INTO factors (tenant_id, indicator_id, name, weight) "
            "VALUES (:tid, :iid, :name, :weight) RETURNING id"
        ),
        {"tid": tenant_id, "iid": indicator_id, "name": factor.name, "weight": factor.weight},
    ).scalar()
    for metric_name in factor.metrics:
        conn.execute(
            text(
                "INSERT INTO factor_metrics (factor_id, metric_name) VALUES (:fid, :m) "
                "ON CONFLICT DO NOTHING"
            ),
            {"fid": fid, "m": metric_name},
        )
    return fid


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------
@router.post("/goals", response_model=GoalRead, status_code=status.HTTP_201_CREATED, summary="Create goal")
@limiter.limit("30/minute")
def create_goal(
    request: Request,
    data: GoalCreate,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "INSERT INTO goals (tenant_id, name, description, owner_role, escalation_chain_id, is_active) "
                    "VALUES (:tid, :name, :desc, :owner, :chain, :active) "
                    "RETURNING id, name, description, owner_role, escalation_chain_id, is_active, created_at, updated_at"
                ),
                {"tid": current_user.tenant_id, "name": data.name, "desc": data.description,
                 "owner": data.owner_role, "chain": data.escalation_chain_id, "active": data.is_active},
            ).mappings().first()
        log_audit(current_user.username, current_user.tenant_id, "create", "goal", resource_id=str(row["id"]))
        return GoalRead(**row)
    except Exception as e:
        logger.error("create goal failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not create goal")


@router.get("/goals", response_model=List[GoalRead], summary="List goals")
def list_goals(
    active_only: bool = Query(True),
    current_user: TokenData = Depends(require_permission("read:indicators")),
):
    where = "tenant_id = :tid" + ("" if not active_only else " AND is_active = true")
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"SELECT id, name, description, owner_role, escalation_chain_id, is_active, created_at, updated_at "
                f"FROM goals WHERE {where} ORDER BY name"
            ),
            {"tid": current_user.tenant_id},
        ).mappings().all()
    return [GoalRead(**r) for r in rows]


@router.get("/goals/{goal_id}", response_model=GoalRead, summary="Get goal")
def get_goal(
    goal_id: UUID,
    current_user: TokenData = Depends(require_permission("read:indicators")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, name, description, owner_role, escalation_chain_id, is_active, created_at, updated_at "
                "FROM goals WHERE id = :id AND tenant_id = :tid"
            ),
            {"id": goal_id, "tid": current_user.tenant_id},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalRead(**row)


@router.put("/goals/{goal_id}", response_model=GoalRead, summary="Update goal")
@limiter.limit("30/minute")
def update_goal(
    request: Request,
    goal_id: UUID,
    data: GoalUpdate,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "UPDATE goals SET name = :name, description = :desc, owner_role = :owner, "
                "escalation_chain_id = :chain, is_active = :active WHERE id = :id AND tenant_id = :tid "
                "RETURNING id, name, description, owner_role, escalation_chain_id, is_active, created_at, updated_at"
            ),
            {"id": goal_id, "tid": current_user.tenant_id, "name": data.name,
             "desc": data.description, "owner": data.owner_role, "chain": data.escalation_chain_id,
             "active": data.is_active},
        ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Goal not found")
    log_audit(current_user.username, current_user.tenant_id, "update", "goal", resource_id=str(goal_id))
    return GoalRead(**row)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete goal")
@limiter.limit("10/minute")
def delete_goal(
    request: Request,
    goal_id: UUID,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM goals WHERE id = :id AND tenant_id = :tid"),
            {"id": goal_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "goal", resource_id=str(goal_id))
    return


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------
@router.post("/", response_model=IndicatorRead, status_code=status.HTTP_201_CREATED, summary="Create indicator")
@limiter.limit("30/minute")
def create_indicator(
    request: Request,
    data: IndicatorCreate,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            # If a goal is referenced, it must belong to this tenant.
            if data.goal_id is not None:
                owns = conn.execute(
                    text("SELECT 1 FROM goals WHERE id = :id AND tenant_id = :tid"),
                    {"id": data.goal_id, "tid": current_user.tenant_id},
                ).first()
                if not owns:
                    raise HTTPException(status_code=400, detail="goal_id not found for this tenant")

            ind_id = conn.execute(
                text(
                    "INSERT INTO indicators (tenant_id, goal_id, name, description, unit, "
                    "target_low, target_high, corridor_type, baseline_model_ref, direction, "
                    "chronicle_threshold, is_active, owner_role, owner_user, escalation_chain_id) "
                    "VALUES (:tid, :goal, :name, :desc, :unit, "
                    ":low, :high, :ctype, :bref, :dir, :chron, :active, :orole, :ouser, :chain) RETURNING id"
                ),
                {"tid": current_user.tenant_id, "goal": data.goal_id, "name": data.name,
                 "desc": data.description, "unit": data.unit, "low": data.target_low,
                 "high": data.target_high, "ctype": data.corridor_type, "bref": data.baseline_model_ref,
                 "dir": data.direction, "chron": data.chronicle_threshold, "active": data.is_active,
                 "orole": data.owner_role, "ouser": data.owner_user, "chain": data.escalation_chain_id},
            ).scalar()

            for factor in data.factors:
                _insert_factor(conn, ind_id, current_user.tenant_id, factor)

            row = conn.execute(
                text(f"SELECT {_IND_COLS} FROM indicators WHERE id = :id"), {"id": ind_id}
            ).mappings().first()
            result = _row_to_indicator(conn, row)
        log_audit(current_user.username, current_user.tenant_id, "create", "indicator", resource_id=str(ind_id))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create indicator failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not create indicator")


@router.get("/", response_model=List[IndicatorRead], summary="List indicators")
def list_indicators(
    goal_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    current_user: TokenData = Depends(require_permission("read:indicators")),
):
    where = ["tenant_id = :tid"]
    params = {"tid": current_user.tenant_id}
    if active_only:
        where.append("is_active = true")
    if goal_id is not None:
        where.append("goal_id = :goal")
        params["goal"] = goal_id
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT {_IND_COLS} FROM indicators WHERE {' AND '.join(where)} ORDER BY name"),
            params,
        ).mappings().all()
        return [_row_to_indicator(conn, r) for r in rows]


@router.get("/tree", response_model=IndicatorTreeResponse, summary="Indicator tree (cockpit)")
def indicator_tree(
    current_user: TokenData = Depends(require_permission("read:indicators")),
):
    """Goal → Indicator → Factor → Metric tree for the decision cockpit."""
    engine = get_engine()
    with engine.connect() as conn:
        goals = conn.execute(
            text(
                "SELECT id, name, owner_role, is_active FROM goals "
                "WHERE tenant_id = :tid ORDER BY name"
            ),
            {"tid": current_user.tenant_id},
        ).mappings().all()
        indicators = conn.execute(
            text(f"SELECT {_IND_COLS} FROM indicators WHERE tenant_id = :tid ORDER BY name"),
            {"tid": current_user.tenant_id},
        ).mappings().all()

        by_goal: dict = {}
        unassigned: List[IndicatorTreeNode] = []
        for ind in indicators:
            node = IndicatorTreeNode(
                id=ind["id"], name=ind["name"], unit=ind["unit"] or "",
                target_low=float(ind["target_low"]) if ind["target_low"] is not None else None,
                target_high=float(ind["target_high"]) if ind["target_high"] is not None else None,
                direction=ind["direction"], is_active=ind["is_active"],
                factors=_load_factors(conn, ind["id"]),
            )
            if ind["goal_id"] is None:
                unassigned.append(node)
            else:
                by_goal.setdefault(ind["goal_id"], []).append(node)

        goal_nodes = [
            GoalTreeNode(
                id=g["id"], name=g["name"], owner_role=g["owner_role"], is_active=g["is_active"],
                indicators=by_goal.get(g["id"], []),
            )
            for g in goals
        ]
    return IndicatorTreeResponse(goals=goal_nodes, unassigned=unassigned)


@router.get("/{indicator_id}", response_model=IndicatorRead, summary="Get indicator")
def get_indicator(
    indicator_id: UUID,
    current_user: TokenData = Depends(require_permission("read:indicators")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(f"SELECT {_IND_COLS} FROM indicators WHERE id = :id AND tenant_id = :tid"),
            {"id": indicator_id, "tid": current_user.tenant_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Indicator not found")
        return _row_to_indicator(conn, row)


@router.put("/{indicator_id}", response_model=IndicatorRead, summary="Update indicator")
@limiter.limit("30/minute")
def update_indicator(
    request: Request,
    indicator_id: UUID,
    data: IndicatorUpdate,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            if data.goal_id is not None:
                owns = conn.execute(
                    text("SELECT 1 FROM goals WHERE id = :id AND tenant_id = :tid"),
                    {"id": data.goal_id, "tid": current_user.tenant_id},
                ).first()
                if not owns:
                    raise HTTPException(status_code=400, detail="goal_id not found for this tenant")

            row = conn.execute(
                text(
                    "UPDATE indicators SET goal_id = :goal, name = :name, description = :desc, "
                    "unit = :unit, target_low = :low, target_high = :high, corridor_type = :ctype, "
                    "baseline_model_ref = :bref, direction = :dir, chronicle_threshold = :chron, "
                    "is_active = :active, owner_role = :orole, owner_user = :ouser, "
                    "escalation_chain_id = :chain WHERE id = :id AND tenant_id = :tid RETURNING id"
                ),
                {"id": indicator_id, "tid": current_user.tenant_id, "goal": data.goal_id,
                 "name": data.name, "desc": data.description, "unit": data.unit,
                 "low": data.target_low, "high": data.target_high, "ctype": data.corridor_type,
                 "bref": data.baseline_model_ref, "dir": data.direction,
                 "chron": data.chronicle_threshold, "active": data.is_active,
                 "orole": data.owner_role, "ouser": data.owner_user, "chain": data.escalation_chain_id},
            ).first()
            if not row:
                raise HTTPException(status_code=404, detail="Indicator not found")
            full = conn.execute(
                text(f"SELECT {_IND_COLS} FROM indicators WHERE id = :id"), {"id": indicator_id}
            ).mappings().first()
            result = _row_to_indicator(conn, full)
        log_audit(current_user.username, current_user.tenant_id, "update", "indicator", resource_id=str(indicator_id))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update indicator failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not update indicator")


@router.delete("/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete indicator")
@limiter.limit("10/minute")
def delete_indicator(
    request: Request,
    indicator_id: UUID,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM indicators WHERE id = :id AND tenant_id = :tid"),
            {"id": indicator_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Indicator not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "indicator", resource_id=str(indicator_id))
    return


# ---------------------------------------------------------------------------
# Factors (sub-resource of an indicator)
# ---------------------------------------------------------------------------
@router.post("/{indicator_id}/factors", response_model=FactorRead,
             status_code=status.HTTP_201_CREATED, summary="Add factor to indicator")
@limiter.limit("30/minute")
def add_factor(
    request: Request,
    indicator_id: UUID,
    data: FactorCreate,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        owns = conn.execute(
            text("SELECT 1 FROM indicators WHERE id = :id AND tenant_id = :tid"),
            {"id": indicator_id, "tid": current_user.tenant_id},
        ).first()
        if not owns:
            raise HTTPException(status_code=404, detail="Indicator not found")
        fid = _insert_factor(conn, indicator_id, current_user.tenant_id, data)
        metrics = conn.execute(
            text("SELECT metric_name FROM factor_metrics WHERE factor_id = :fid ORDER BY metric_name"),
            {"fid": fid},
        ).scalars().all()
    log_audit(current_user.username, current_user.tenant_id, "create", "factor", resource_id=str(fid))
    return FactorRead(id=fid, name=data.name, weight=data.weight, metrics=list(metrics))


@router.delete("/factors/{factor_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete factor")
@limiter.limit("20/minute")
def delete_factor(
    request: Request,
    factor_id: UUID,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM factors WHERE id = :id AND tenant_id = :tid"),
            {"id": factor_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Factor not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "factor", resource_id=str(factor_id))
    return


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------
@router.post("/{indicator_id}/subscriptions", response_model=SubscriptionRead,
             status_code=status.HTTP_201_CREATED, summary="Subscribe to indicator")
@limiter.limit("30/minute")
def add_subscription(
    request: Request,
    indicator_id: UUID,
    data: SubscriptionCreate,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        owns = conn.execute(
            text("SELECT 1 FROM indicators WHERE id = :id AND tenant_id = :tid"),
            {"id": indicator_id, "tid": current_user.tenant_id},
        ).first()
        if not owns:
            raise HTTPException(status_code=404, detail="Indicator not found")
        row = conn.execute(
            text(
                "INSERT INTO indicator_subscriptions (tenant_id, indicator_id, subscriber_role, "
                "subscriber_user, channel) VALUES (:tid, :iid, :role, :usr, :chan) "
                "RETURNING id, indicator_id, subscriber_role, subscriber_user, channel, created_at"
            ),
            {"tid": current_user.tenant_id, "iid": indicator_id, "role": data.subscriber_role,
             "usr": data.subscriber_user, "chan": data.channel},
        ).mappings().first()
    log_audit(current_user.username, current_user.tenant_id, "create", "subscription", resource_id=str(row["id"]))
    return SubscriptionRead(**row)


@router.get("/{indicator_id}/subscriptions", response_model=List[SubscriptionRead],
            summary="List indicator subscriptions")
def list_subscriptions(
    indicator_id: UUID,
    current_user: TokenData = Depends(require_permission("read:indicators")),
):
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, indicator_id, subscriber_role, subscriber_user, channel, created_at "
                "FROM indicator_subscriptions WHERE indicator_id = :iid AND tenant_id = :tid "
                "ORDER BY created_at"
            ),
            {"iid": indicator_id, "tid": current_user.tenant_id},
        ).mappings().all()
    return [SubscriptionRead(**r) for r in rows]


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Unsubscribe")
@limiter.limit("20/minute")
def delete_subscription(
    request: Request,
    subscription_id: UUID,
    current_user: TokenData = Depends(require_permission("write:indicators")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM indicator_subscriptions WHERE id = :id AND tenant_id = :tid"),
            {"id": subscription_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subscription not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "subscription", resource_id=str(subscription_id))
    return
