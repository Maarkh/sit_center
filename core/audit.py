# core/audit.py
import json
from typing import Optional, Dict, Any
from sqlalchemy import text
from config import logger, mask_secrets
from core.database import get_engine


def log_audit(
    username: str,
    tenant_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Write an audit log entry to the database."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO audit_log (username, tenant_id, action, resource_type, resource_id, changes, ip_address, user_agent)
                    VALUES (:username, :tenant_id, :action, :resource_type, :resource_id, :changes, :ip_address, :user_agent)
                """),
                {
                    "username": username,
                    "tenant_id": tenant_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "changes": json.dumps(changes or {}, ensure_ascii=False, default=str),
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                },
            )
    except Exception as e:
        logger.error("Failed to write audit log: %s", mask_secrets(str(e)))
