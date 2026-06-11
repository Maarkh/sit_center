# core/sla_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from sqlalchemy import text
from core.database import get_engine
from config import logger


def get_sla_policy(tenant_id: str, priority: str) -> Optional[Dict]:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, response_time_minutes, resolution_time_minutes, escalation_after_minutes
                FROM sla_policies
                WHERE tenant_id = :tenant_id AND priority = :priority AND is_active = true
            """),
            {"tenant_id": tenant_id, "priority": priority},
        ).mappings().first()
        return dict(row) if row else None


def apply_sla_to_incident(incident_id: int, tenant_id: str, priority: str, detected_at: datetime):
    policy = get_sla_policy(tenant_id, priority)
    if not policy:
        return

    response_deadline = detected_at + timedelta(minutes=policy["response_time_minutes"])
    resolution_deadline = detected_at + timedelta(minutes=policy["resolution_time_minutes"])

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE incidents SET
                    sla_policy_id = :policy_id,
                    response_deadline = :response_deadline,
                    resolution_deadline = :resolution_deadline
                WHERE id = :id
            """),
            {
                "id": incident_id,
                "policy_id": policy["id"],
                "response_deadline": response_deadline,
                "resolution_deadline": resolution_deadline,
            },
        )


def check_sla_breaches():
    """Check all open incidents for SLA breaches. Called periodically by Celery."""
    now = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.begin() as conn:
        # Response breach: never acknowledged past the response deadline. Key on
        # started_at IS NULL (no operator picked it up) rather than status='new' —
        # auto-escalation flips an unanswered incident to 'escalated' before this sweep,
        # which would otherwise let it escape the response-breach check entirely.
        breached_response = conn.execute(
            text("""
                UPDATE incidents SET response_breached = true
                WHERE started_at IS NULL
                  AND status NOT IN ('resolved', 'closed')
                  AND response_deadline IS NOT NULL
                  AND response_deadline < :now
                  AND response_breached = false
                RETURNING id, metric, region, priority
            """),
            {"now": now},
        ).mappings().all()

        for row in breached_response:
            logger.warning(f"SLA response breach: incident #{row['id']} ({row['priority']}) {row['metric']}/{row['region']}")

        # Resolution breach: incident not resolved/closed past resolution deadline
        breached_resolution = conn.execute(
            text("""
                UPDATE incidents SET resolution_breached = true
                WHERE status NOT IN ('resolved', 'closed')
                  AND resolution_deadline IS NOT NULL
                  AND resolution_deadline < :now
                  AND resolution_breached = false
                RETURNING id, metric, region, priority
            """),
            {"now": now},
        ).mappings().all()

        for row in breached_resolution:
            logger.warning(f"SLA resolution breach: incident #{row['id']} ({row['priority']}) {row['metric']}/{row['region']}")

    return {
        "response_breaches": len(breached_response),
        "resolution_breaches": len(breached_resolution),
    }


def check_auto_escalation():
    """Auto-escalate incidents that exceeded their escalation timeout. Called by Celery."""
    now = datetime.now(timezone.utc)
    engine = get_engine()

    with engine.connect() as conn:
        # Find open incidents with escalation chains that need escalation
        rows = conn.execute(
            text("""
                SELECT i.id, i.escalation_level, i.escalation_chain_id,
                       i.last_escalated_at, i.detected_at, i.tenant_id,
                       i.metric, i.region, i.priority
                FROM incidents i
                WHERE i.status NOT IN ('resolved', 'closed')
                  AND i.escalation_chain_id IS NOT NULL
            """),
        ).mappings().all()

    for row in rows:
        current_level = row["escalation_level"]
        reference_time = row["last_escalated_at"] or row["detected_at"]

        with engine.connect() as conn:
            next_level = conn.execute(
                text("""
                    SELECT level, notify_role, notify_users, escalate_after_minutes
                    FROM escalation_levels
                    WHERE chain_id = :chain_id AND level = :next_level
                """),
                {"chain_id": row["escalation_chain_id"], "next_level": current_level + 1},
            ).mappings().first()

        if not next_level:
            continue

        elapsed = (now - reference_time).total_seconds() / 60
        if elapsed >= next_level["escalate_after_minutes"]:
            # Compare-and-swap on the observed level so a concurrent manual escalation
            # (incidents.escalate_incident, which locks) or an overlapping run can't be
            # clobbered / double-escalated: the UPDATE only fires if the incident is
            # still at current_level and not already resolved.
            with engine.begin() as conn:
                res = conn.execute(
                    text("""
                        UPDATE incidents SET
                            escalation_level = :level,
                            status = 'escalated',
                            last_escalated_at = :now
                        WHERE id = :id AND escalation_level = :observed
                          AND status NOT IN ('resolved', 'closed')
                    """),
                    {"id": row["id"], "level": next_level["level"], "now": now,
                     "observed": current_level},
                )
            if res.rowcount == 0:
                continue  # raced — another escalation/resolve won; don't notify

            logger.warning(
                f"Auto-escalated incident #{row['id']} to L{next_level['level']} "
                f"({next_level['notify_role']}): {row['metric']}/{row['region']}"
            )

            try:
                from core.notifications import notify
                users = next_level["notify_users"] or []
                target = next_level["notify_role"] + (f" ({', '.join(users)})" if users else "")
                notify(
                    f"Эскалация L{next_level['level']} → {target}: инцидент #{row['id']} "
                    f"{row['metric']}/{row['region']} ({row['priority']})",
                    "critical" if next_level["level"] >= 3 else "warning",
                    event_type="escalation", tenant_id=row["tenant_id"],
                )
            except Exception as e:
                logger.error(f"Failed to send escalation notification: {e}")
