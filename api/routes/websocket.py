# api/routes/websocket.py
import json
import secrets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from typing import List, Dict
from api.auth import get_current_user, TokenData
from core.pubsub import subscribe_alerts
from config import get_cache, logger, mask_secrets

router = APIRouter()

# Short-lived, single-use ticket TTL. Long enough for the SPA to open the socket
# right after fetching the ticket, short enough that a leaked ticket is useless.
WS_TICKET_TTL = 30


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # id(websocket) -> tenant_id, so a broadcast only reaches its own tenant.
        self.connection_tenants: Dict[int, str] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_tenants[id(websocket)] = tenant_id

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.connection_tenants.pop(id(websocket), None)

    async def broadcast(self, message: dict):
        # Only deliver to connections belonging to the alert's tenant. A message
        # without a tenant_id is treated as "default" so it can never fan out
        # to every tenant by accident.
        message_tenant = message.get("tenant_id", "default")
        disconnected = []
        for connection in self.active_connections:
            if self.connection_tenants.get(id(connection)) != message_tenant:
                continue
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


async def alert_stream_task():
    """Subscribe to Redis Pub/Sub and broadcast alerts to WebSocket clients."""
    await subscribe_alerts(manager.broadcast)


@router.post("/ws/ticket", tags=["System"], summary="Issue a single-use WebSocket ticket")
def issue_ws_ticket(current_user: TokenData = Depends(get_current_user)):
    """Exchange the Bearer JWT for a short-lived, single-use ticket.

    Browsers can't set Authorization headers on a WebSocket, so the SPA fetches a
    ticket here (over normal authenticated HTTP) and connects with `?ticket=...`.
    This keeps the long-lived JWT out of the WS URL, where it would otherwise land
    in proxy/access logs and browser history.
    """
    ticket = secrets.token_urlsafe(32)
    get_cache().setex(f"ws_ticket:{ticket}", WS_TICKET_TTL, current_user.tenant_id)
    return {"ticket": ticket, "expires_in": WS_TICKET_TTL}


def _resolve_ws_tenant(websocket: WebSocket):
    """Resolve the tenant for a WS connection from a single-use ticket (preferred)
    or, for backwards compatibility, a full JWT in the query string."""
    ticket = websocket.query_params.get("ticket")
    if ticket:
        try:
            cache = get_cache()
            key = f"ws_ticket:{ticket}"
            tenant_id = cache.get(key)
            if tenant_id is not None:
                cache.delete(key)  # single use
                if isinstance(tenant_id, bytes):
                    tenant_id = tenant_id.decode()
                return tenant_id
        except Exception as e:
            logger.warning("WS ticket lookup failed: %s", mask_secrets(str(e)))
        return None

    # The full-JWT-in-?token= fallback was removed: it leaked the token into proxy
    # logs / history. Clients must use the single-use ticket (POST /ws/ticket).
    return None


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    tenant_id = _resolve_ws_tenant(websocket)
    if not tenant_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, tenant_id=tenant_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
