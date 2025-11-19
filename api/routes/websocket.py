# api/routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect,WebSocketException, status
from typing import List
import asyncio
import json
from core.database import get_engine
from sqlalchemy import text
from config import logger, mask_secrets
from api.auth import verify_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Фоновая задача: push новых алертов
async def alert_stream_task():
    last_ts = None
    while True:
        try:
            engine = get_engine()
            with engine.connect() as conn:
                if last_ts is None:
                    # Только последние 10 при первом запуске
                    result = conn.execute(
                        text("""
                            SELECT * FROM alert_events 
                            ORDER BY event_time DESC 
                            LIMIT 10
                        """)
                    ).mappings().all()
                else:
                    result = conn.execute(
                        text("""
                            SELECT * FROM alert_events 
                            WHERE event_time > :last_ts 
                            ORDER BY event_time ASC
                            LIMIT 50
                        """),
                        {"last_ts": last_ts}
                    ).mappings().all()
                
                if result:
                    for row in result:
                        await manager.broadcast({
                            "type": "alert",
                            "id": str(row["id"]),
                            "metric": row["metric_name"],
                            "dimensions": row["dimensions"],
                            "value": float(row["value"]),
                            "status": row["status"],
                            "event_time": row["event_time"].isoformat()
                        })
                        last_ts = row["event_time"]
                        
        except Exception as e:
            logger.error(f"WS stream error: {mask_secrets(str(e))}")
        
        await asyncio.sleep(5)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    # Получаем токен из query или headers
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)