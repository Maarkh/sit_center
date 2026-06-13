# core/responsibility.py
"""Resolve WHO owns an indicator and WHICH escalation chain applies, so work spawned
from a deviation (auto-incident, auto-process) is assigned and escalated automatically.

Resolution (most specific wins), per the "responsibility map on the indicator, fall back
to the goal" model:
  owner_role : indicators.owner_role → goals.owner_role
  owner_user : indicators.owner_user            (no goal-level person)
  chain      : indicators.escalation_chain_id → goals.escalation_chain_id → default active
"""
from sqlalchemy import text


def resolve_responsibility(conn, indicator_id, tenant_id: str):
    """Returns (owner_user, owner_role, chain_id) — any of which may be None. `conn` is an
    open SQLAlchemy connection (caller's transaction)."""
    row = conn.execute(
        text(
            "SELECT i.owner_role, i.owner_user, i.escalation_chain_id, "
            "g.owner_role AS goal_role, g.escalation_chain_id AS goal_chain "
            "FROM indicators i LEFT JOIN goals g ON g.id = i.goal_id "
            "WHERE i.id = :iid AND i.tenant_id = :tid"
        ),
        {"iid": indicator_id, "tid": tenant_id},
    ).mappings().first()

    owner_user = owner_role = chain = None
    if row:
        owner_user = row["owner_user"]
        owner_role = row["owner_role"] or row["goal_role"]
        chain = row["escalation_chain_id"] or row["goal_chain"]
    if not chain:
        chain = conn.execute(
            text("SELECT id FROM escalation_chains WHERE tenant_id = :tid AND is_active = true "
                 "ORDER BY created_at LIMIT 1"),
            {"tid": tenant_id},
        ).scalar()
    return owner_user, owner_role, chain


def resolve_assignee(conn, indicator_id, tenant_id: str):
    """The single person/role string to put in incidents.assigned_to: the owning user if
    named, else the owning role. None if neither is set anywhere."""
    owner_user, owner_role, _ = resolve_responsibility(conn, indicator_id, tenant_id)
    return owner_user or owner_role
