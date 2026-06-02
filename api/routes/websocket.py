# api/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import List, Dict
import json
from api.auth import verify_token
from core.pubsub import subscribe_alerts

router = APIRouter()


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


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        token_data = verify_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, tenant_id=token_data.tenant_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
