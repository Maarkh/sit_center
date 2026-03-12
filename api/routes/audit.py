# api/routes/audit.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import text
from core.database import get_engine
from core.rbac import require_permission
from api.auth import TokenData
from config import mask_secrets

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogEntry(BaseModel):
    id: int
    username: str
    tenant_id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    changes: Dict[str, Any]
    ip_address: Optional[str]
    timestamp: datetime


@router.get("/logs", response_model=List[AuditLogEntry])
def get_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_permission("read:audit")),
):
    engine = get_engine()
    where_parts = ["tenant_id = :tenant_id"]
    params: Dict[str, Any] = {
        "tenant_id": current_user.tenant_id,
        "limit": limit,
        "offset": offset,
    }

    if action:
        where_parts.append("action = :action")
        params["action"] = action
    if resource_type:
        where_parts.append("resource_type = :resource_type")
        params["resource_type"] = resource_type
    if username:
        where_parts.append("username = :username")
        params["username"] = username

    where_clause = " AND ".join(where_parts)
    query = text(f"""
        SELECT id, username, tenant_id, action, resource_type, resource_id, changes, ip_address, timestamp
        FROM audit_log
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(query, params).mappings().all()
            return [AuditLogEntry(**row) for row in rows]
    except Exception as e:
        raise HTTPException(500, mask_secrets(str(e)))
