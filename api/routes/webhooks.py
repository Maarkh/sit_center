# api/routes/webhooks.py
"""
Webhook endpoints for external systems:
- /webhook/grafana → receive Grafana alerts → Telegram
- /webhook/idoit    → receive structured alerts → Telegram + i-doit incident
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import hmac
import requests
from config import settings, logger, mask_secrets
from core.notifications import notify
from api.limiter import limiter

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# === Схемы ===

class GrafanaAlert(BaseModel):
    title: str = Field(..., min_length=1)
    message: str = ""
    status: str = "firing"  # firing / resolved


class IdoitAlertData(BaseModel):
    title: str = Field(..., min_length=1, description="Краткое название алерта")
    message: str = Field(..., description="Детали")
    priority: str = Field("warning", pattern="^(info|warning|critical)$")
    region: Optional[str] = Field("N/A", description="Регион РФ, e.g. RU-MOW")
    metric: str = Field(..., description="Имя метрики, e.g. api_latency_p99")
    value: Optional[str] = Field("N/A", description="Текущее значение")

    @validator("region")
    def validate_region(cls, v):
        if v and len(v) > 20:
            raise ValueError("region too long")
        return v


# === Вспомогательные функции ===

def verify_webhook_key(request: Request) -> bool:
    key_header = request.headers.get("X-API-KEY")
    if not settings.WEBHOOK_API_KEY:
        logger.error("WEBHOOK_API_KEY not configured — rejecting all webhook requests")
        return False
    if not key_header:
        return False
    return hmac.compare_digest(key_header, settings.WEBHOOK_API_KEY)


def create_idoit_incident(alert_data: IdoitAlertData) -> Dict[str, Any]:
    if not (settings.I_DOIT_API_URL and settings.I_DOIT_API_KEY):
        logger.info("i-doit integration disabled (no URL or API key)")
        return {"success": False, "error": "i-doit disabled"}

    payload = {
        "jsonrpc": "2.0",
        "method": "cmdb.object.create",
        "params": {
            "apikey": settings.I_DOIT_API_KEY,
            "objTypeID": 10,  # Инцидент
            "title": f"[ALERT] {alert_data.title}",
            "properties": {
                "description": (
                    f"{alert_data.message}\n"
                    f"Регион: {alert_data.region}\n"
                    f"Метрика: {alert_data.metric}\n"
                    f"Значение: {alert_data.value}"
                ),
                "status": "2",           # Open
                "priority": "3",          # High
                "assigned": "admin"
            }
        },
        "id": 1
    }

    try:
        resp = requests.post(
            settings.I_DOIT_API_URL,
            json=payload,
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("error"):
            err_msg = result["error"].get("message", "unknown")
            logger.error(f"i-doit API error: {err_msg}")
            return {"success": False, "error": err_msg}

        obj_id = result.get("result", {}).get("objectID")
        if not obj_id:
            logger.error("i-doit: no objectID in response")
            return {"success": False, "error": "no objectID"}

        logger.info(f"✅ i-doit incident created: {obj_id}")
        return {"success": True, "id": obj_id}

    except requests.RequestException as e:
        logger.exception("i-doit request failed")
        return {"success": False, "error": f"connection error: {mask_secrets(str(e))}"}
    except Exception as e:
        logger.exception("i-doit processing error")
        return {"success": False, "error": mask_secrets(str(e))}


# === Роуты ===

@router.post("/grafana", status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def grafana_webhook(
    request: Request,
    payload: GrafanaAlert
):
    # Rate-limiting через глобальный limiter (уже настроен в main.py)
    priority = "critical" if payload.status == "firing" else "info"
    message = f"🚨 {payload.title}\n{payload.message}"
    notify(message, priority)
    return {"status": "ok", "sent": True}


@router.post("/idoit", status_code=status.HTTP_200_OK)
@limiter.limit("100/minute")
async def idoit_webhook(
    request: Request,
    payload: IdoitAlertData
):
    # 🔐 Аутентификация
    if not verify_webhook_key(request):
        logger.warning(f"Invalid X-API-KEY from {request.client.host if request.client else 'unknown'}")
        raise HTTPException(status_code=403, detail="Invalid API key")

    # ✅ Уведомление в Telegram
    telegram_msg = f"🚨 i-doit: {payload.title}\n{payload.message}"
    notify(telegram_msg, payload.priority)

    # 🛠️ Создание инцидента в i-doit (если настроено)
    result = create_idoit_incident(payload)
    if not result["success"]:
        # Не фейлим запрос — логируем, но продолжаем
        logger.warning(f"i-doit incident creation failed: {result['error']}")

    return {
        "success": True,
        "telegram_sent": True,
        "idoit": result
    }