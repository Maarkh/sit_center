# api/routes/scenarios.py
"""DSS M6 — Model & Scenario Management / what-if.

Define a scenario (assumptions about indicator values), run it to project the effect
against the corridors and estimate the avoided-impact potential, and review results.
Tenant-scoped.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional
from uuid import UUID
import json
from sqlalchemy import text

from core.database import get_engine
from core.scenario_engine import scenario_engine
from api.auth import TokenData
from core.rbac import require_permission
from core.audit import log_audit
from api.limiter import limiter
from config import mask_secrets, logger
from api.schemas_dss import (
    ScenarioCreate, ScenarioRead, ScenarioListItem,
    ScenarioResultRead, ScenarioResultItem, Assumption,
)

router = APIRouter(prefix="/scenarios", tags=["DSS: Scenarios (what-if)"])


def _result_read(row) -> Optional[ScenarioResultRead]:
    if not row:
        return None
    results = row["results"] or []
    if isinstance(results, str):
        results = json.loads(results)
    return ScenarioResultRead(
        id=row["id"], scenario_id=row["scenario_id"],
        results=[ScenarioResultItem(**r) for r in results],
        potential_value=float(row["potential_value"]),
        breaches_avoided=row["breaches_avoided"], computed_at=row["computed_at"],
    )


def _assumptions(row_assumptions) -> List[Assumption]:
    data = row_assumptions or []
    if isinstance(data, str):
        data = json.loads(data)
    return [Assumption(**a) for a in data]


def _latest_result(conn, scenario_id):
    return conn.execute(
        text("SELECT id, scenario_id, results, potential_value, breaches_avoided, computed_at "
             "FROM scenario_results WHERE scenario_id = :sid ORDER BY computed_at DESC LIMIT 1"),
        {"sid": scenario_id},
    ).mappings().first()


@router.post("/", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED, summary="Create scenario")
@limiter.limit("30/minute")
def create_scenario(
    request: Request,
    data: ScenarioCreate,
    current_user: TokenData = Depends(require_permission("write:scenarios")),
):
    engine = get_engine()
    try:
        with engine.begin() as conn:
            if data.situation_id is not None:
                owns = conn.execute(
                    text("SELECT 1 FROM situations WHERE id = :id AND tenant_id = :tid"),
                    {"id": data.situation_id, "tid": current_user.tenant_id},
                ).first()
                if not owns:
                    raise HTTPException(status_code=400, detail="situation_id not found for this tenant")
            assumptions_json = json.dumps([{"indicator_id": str(a.indicator_id), "mode": a.mode,
                                            "value": a.value} for a in data.assumptions])
            row = conn.execute(
                text("INSERT INTO scenarios (tenant_id, name, description, situation_id, assumptions, "
                     "created_by) VALUES (:tid, :name, :desc, :sit, CAST(:asm AS jsonb), :by) "
                     "RETURNING id, name, description, situation_id, assumptions, created_by, "
                     "created_at, updated_at"),
                {"tid": current_user.tenant_id, "name": data.name, "desc": data.description,
                 "sit": data.situation_id, "asm": assumptions_json, "by": current_user.username},
            ).mappings().first()
        log_audit(current_user.username, current_user.tenant_id, "create", "scenario", resource_id=str(row["id"]))
        return ScenarioRead(
            id=row["id"], name=row["name"], description=row["description"],
            situation_id=row["situation_id"], assumptions=_assumptions(row["assumptions"]),
            created_by=row["created_by"], created_at=row["created_at"], updated_at=row["updated_at"],
            latest_result=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create scenario failed: %s", mask_secrets(str(e)))
        raise HTTPException(status_code=400, detail="Could not create scenario")


@router.get("/", response_model=List[ScenarioListItem], summary="List scenarios")
def list_scenarios(
    situation_id: Optional[UUID] = Query(None),
    current_user: TokenData = Depends(require_permission("read:scenarios")),
):
    where = ["s.tenant_id = :tid"]
    params = {"tid": current_user.tenant_id}
    if situation_id is not None:
        where.append("s.situation_id = :sit")
        params["sit"] = situation_id
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT s.id, s.name, s.situation_id, s.created_at, "
                 "r.potential_value, r.breaches_avoided FROM scenarios s "
                 "LEFT JOIN LATERAL (SELECT potential_value, breaches_avoided FROM scenario_results "
                 "  WHERE scenario_id = s.id ORDER BY computed_at DESC LIMIT 1) r ON true "
                 f"WHERE {' AND '.join(where)} ORDER BY s.created_at DESC"),
            params,
        ).mappings().all()
    return [ScenarioListItem(
        id=r["id"], name=r["name"], situation_id=r["situation_id"], created_at=r["created_at"],
        potential_value=float(r["potential_value"]) if r["potential_value"] is not None else None,
        breaches_avoided=r["breaches_avoided"],
    ) for r in rows]


@router.get("/{scenario_id}", response_model=ScenarioRead, summary="Get scenario (with latest result)")
def get_scenario(
    scenario_id: UUID,
    current_user: TokenData = Depends(require_permission("read:scenarios")),
):
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, description, situation_id, assumptions, created_by, created_at, "
                 "updated_at FROM scenarios WHERE id = :id AND tenant_id = :tid"),
            {"id": scenario_id, "tid": current_user.tenant_id},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Scenario not found")
        latest = _result_read(_latest_result(conn, scenario_id))
    return ScenarioRead(
        id=row["id"], name=row["name"], description=row["description"],
        situation_id=row["situation_id"], assumptions=_assumptions(row["assumptions"]),
        created_by=row["created_by"], created_at=row["created_at"], updated_at=row["updated_at"],
        latest_result=latest,
    )


@router.post("/{scenario_id}/run", response_model=ScenarioResultRead, summary="Run what-if scenario")
@limiter.limit("30/minute")
def run_scenario(
    request: Request,
    scenario_id: UUID,
    current_user: TokenData = Depends(require_permission("write:scenarios")),
):
    result = scenario_engine.run_scenario(scenario_id, current_user.tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    log_audit(current_user.username, current_user.tenant_id, "run", "scenario", resource_id=str(scenario_id))
    return ScenarioResultRead(
        id=result["id"], scenario_id=result["scenario_id"],
        results=[ScenarioResultItem(**r) for r in result["results"]],
        potential_value=result["potential_value"], breaches_avoided=result["breaches_avoided"],
        computed_at=result["computed_at"],
    )


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete scenario")
@limiter.limit("20/minute")
def delete_scenario(
    request: Request,
    scenario_id: UUID,
    current_user: TokenData = Depends(require_permission("write:scenarios")),
):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM scenarios WHERE id = :id AND tenant_id = :tid"),
            {"id": scenario_id, "tid": current_user.tenant_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Scenario not found")
    log_audit(current_user.username, current_user.tenant_id, "delete", "scenario", resource_id=str(scenario_id))
    return
