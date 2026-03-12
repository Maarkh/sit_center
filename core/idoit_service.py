# core/idoit_service.py
"""
Bidirectional i-doit integration service.

i-doit is the primary ITSM/CMDB system for incident resolution.
This service handles:
- Push: create/update incidents in i-doit when they change locally
- Pull: sync status changes from i-doit back to local incidents
- Mapping: priority/status translation between systems
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from config import settings, logger, mask_secrets
from core.database import get_engine
from sqlalchemy import text


# === Status/Priority mapping ===

# Sit Center -> i-doit status mapping
STATUS_TO_IDOIT = {
    "new": "1",          # New
    "in_progress": "2",  # In Progress / Open
    "escalated": "2",    # In Progress (escalated is still open in i-doit)
    "resolved": "3",     # Resolved
    "closed": "4",       # Closed
}

# i-doit -> Sit Center status mapping
STATUS_FROM_IDOIT = {
    "1": "new",
    "2": "in_progress",
    "3": "resolved",
    "4": "closed",
}

# Sit Center -> i-doit priority mapping
PRIORITY_TO_IDOIT = {
    "critical": "1",  # Very High
    "high": "2",       # High
    "medium": "3",     # Normal
    "low": "4",        # Low
}

PRIORITY_FROM_IDOIT = {
    "1": "critical",
    "2": "high",
    "3": "medium",
    "4": "low",
}


def is_enabled() -> bool:
    return bool(getattr(settings, "I_DOIT_API_URL", None) and getattr(settings, "I_DOIT_API_KEY", None))


def _call_idoit(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a JSON-RPC call to i-doit API."""
    params["apikey"] = settings.I_DOIT_API_KEY

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }

    resp = requests.post(settings.I_DOIT_API_URL, json=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    if result.get("error"):
        err_msg = result["error"].get("message", "unknown")
        raise RuntimeError(f"i-doit API error: {err_msg}")

    return result.get("result", {})


def _log_sync(incident_id: int, direction: str, action: str,
              payload: Any = None, response: Any = None,
              success: bool = False, error: str = None):
    """Write to idoit_sync_log for audit trail."""
    import json
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO idoit_sync_log (incident_id, direction, action, payload, response, success, error)
                    VALUES (:iid, :direction, :action, :payload, :response, :success, :error)
                """),
                {
                    "iid": incident_id,
                    "direction": direction,
                    "action": action,
                    "payload": json.dumps(payload, default=str) if payload else None,
                    "response": json.dumps(response, default=str) if response else None,
                    "success": success,
                    "error": error,
                },
            )
    except Exception as e:
        logger.error(f"Failed to write sync log: {e}")


# === Push operations (Sit Center -> i-doit) ===

def push_incident_create(incident_id: int) -> Optional[str]:
    """Create an incident in i-doit and store the external_id back."""
    if not is_enabled():
        return None

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT id, alert_message, description, metric, region, value,
                       priority, assigned_to, status
                FROM incidents WHERE id = :id
            """),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return None

    description = (
        f"{row['alert_message']}\n\n"
        f"Metric: {row['metric']}\n"
        f"Region: {row['region']}\n"
        f"Value: {row['value'] or 'N/A'}\n"
    )
    if row["description"]:
        description += f"\nDetails: {row['description']}"

    try:
        result = _call_idoit("cmdb.object.create", {
            "type": "C__OBJTYPE__INCIDENT",
            "title": f"[SIT-{incident_id}] {row['alert_message'][:200]}",
            "description": description,
            "status": STATUS_TO_IDOIT.get(row["status"], "1"),
            "priority": PRIORITY_TO_IDOIT.get(row["priority"], "3"),
        })

        obj_id = str(result.get("id") or result.get("objectID", ""))
        if not obj_id:
            _log_sync(incident_id, "push", "create", response=result, error="no objectID")
            return None

        external_url = f"{settings.I_DOIT_API_URL.rsplit('/api', 1)[0]}/?objID={obj_id}" if settings.I_DOIT_API_URL else None

        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE incidents SET
                        external_id = :eid, external_system = 'idoit',
                        external_url = :url, last_synced_at = :now
                    WHERE id = :id
                """),
                {"id": incident_id, "eid": obj_id, "url": external_url, "now": datetime.now(timezone.utc)},
            )

        _log_sync(incident_id, "push", "create", response=result, success=True)
        logger.info(f"i-doit incident created: SIT-{incident_id} -> idoit#{obj_id}")
        return obj_id

    except Exception as e:
        _log_sync(incident_id, "push", "create", error=mask_secrets(str(e)))
        logger.error(f"i-doit push_create failed for incident #{incident_id}: {mask_secrets(str(e))}")
        return None


def push_status_update(incident_id: int, new_status: str):
    """Sync a status change to i-doit."""
    if not is_enabled():
        return

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT external_id FROM incidents WHERE id = :id AND external_id IS NOT NULL"),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return

    idoit_status = STATUS_TO_IDOIT.get(new_status)
    if not idoit_status:
        return

    try:
        result = _call_idoit("cmdb.object.update", {
            "id": int(row["external_id"]),
            "title": None,  # don't change title
            "status": idoit_status,
        })

        with engine.begin() as conn:
            conn.execute(
                text("UPDATE incidents SET last_synced_at = :now WHERE id = :id"),
                {"id": incident_id, "now": datetime.now(timezone.utc)},
            )

        _log_sync(incident_id, "push", "status_update",
                   payload={"status": new_status, "idoit_status": idoit_status},
                   response=result, success=True)

    except Exception as e:
        _log_sync(incident_id, "push", "status_update", error=mask_secrets(str(e)))
        logger.warning(f"i-doit status sync failed for #{incident_id}: {mask_secrets(str(e))}")


def push_assignment(incident_id: int, assigned_to: str):
    """Sync an assignment change to i-doit."""
    if not is_enabled():
        return

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT external_id FROM incidents WHERE id = :id AND external_id IS NOT NULL"),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return

    try:
        result = _call_idoit("cmdb.object.update", {
            "id": int(row["external_id"]),
            "assigned": assigned_to,
        })
        _log_sync(incident_id, "push", "assign",
                   payload={"assigned_to": assigned_to}, response=result, success=True)
    except Exception as e:
        _log_sync(incident_id, "push", "assign", error=mask_secrets(str(e)))
        logger.warning(f"i-doit assign sync failed for #{incident_id}: {mask_secrets(str(e))}")


def push_comment(incident_id: int, author: str, content: str):
    """Push a comment to i-doit as a logbook entry."""
    if not is_enabled():
        return

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT external_id FROM incidents WHERE id = :id AND external_id IS NOT NULL"),
            {"id": incident_id},
        ).mappings().first()

    if not row:
        return

    try:
        result = _call_idoit("cmdb.logbook.create", {
            "object_id": int(row["external_id"]),
            "message": f"[{author}] {content}",
            "description": content,
        })
        _log_sync(incident_id, "push", "comment",
                   payload={"author": author}, response=result, success=True)
    except Exception as e:
        _log_sync(incident_id, "push", "comment", error=mask_secrets(str(e)))
        logger.warning(f"i-doit comment sync failed for #{incident_id}: {mask_secrets(str(e))}")


# === Pull operations (i-doit -> Sit Center) ===

def pull_status_update(incident_id: int, idoit_status: str, idoit_assigned: str = None):
    """
    Apply a status change from i-doit to the local incident.
    Called from the inbound webhook handler.
    """
    local_status = STATUS_FROM_IDOIT.get(str(idoit_status))
    if not local_status:
        logger.warning(f"Unknown i-doit status '{idoit_status}' for incident #{incident_id}")
        return

    engine = get_engine()
    now = datetime.now(timezone.utc)

    updates = ["status = :status", "last_synced_at = :now"]
    params: Dict[str, Any] = {"id": incident_id, "status": local_status, "now": now}

    if local_status == "in_progress":
        updates.append("started_at = COALESCE(started_at, :now)")
    elif local_status == "resolved":
        updates.append("resolved_at = COALESCE(resolved_at, :now)")
    elif local_status == "closed":
        updates.append("closed_at = COALESCE(closed_at, :now)")

    if idoit_assigned:
        updates.append("assigned_to = :assigned")
        params["assigned"] = idoit_assigned

    with engine.begin() as conn:
        conn.execute(
            text(f"UPDATE incidents SET {', '.join(updates)} WHERE id = :id"),
            params,
        )

    _log_sync(incident_id, "pull", "status_update",
              payload={"idoit_status": idoit_status, "local_status": local_status},
              success=True)
    logger.info(f"i-doit pull: incident #{incident_id} -> {local_status}")
