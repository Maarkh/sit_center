"""Notification routing: deliver a (message, priority, event_type) to every enabled
channel configured for the tenant whose event_types + min_priority match.

Transports: telegram, email (SMTP), webhook (generic POST), whatsapp_twilio.
If no channel matches, fall back to the legacy Telegram env config (so existing
deployments keep working); if that isn't configured either, the event is silent.
"""
import smtplib
from email.mime.text import MIMEText

import requests
from sqlalchemy import text

from core.database import get_engine
from config import logger, mask_secrets

# Event categories a channel can subscribe to ('all' = every category).
EVENT_TYPES = ["alert", "incident", "escalation", "predictive", "situation", "system"]
CHANNEL_TYPES = ["telegram", "email", "webhook", "whatsapp_twilio"]
PRIORITIES = ["info", "warning", "critical"]
_PRIORITY_RANK = {"info": 0, "warning": 1, "critical": 2}
# config keys never returned in the clear by the API and preserved on update.
SECRET_KEYS = {"bot_token", "password", "auth_token", "api_key", "token", "secret"}


def channel_matches(channel: dict, event_type: str, priority: str) -> bool:
    """Pure predicate: does this channel want this event? (unit-tested)."""
    if not channel.get("enabled", True):
        return False
    ets = channel.get("event_types") or []
    if event_type not in ets and "all" not in ets:
        return False
    return _PRIORITY_RANK.get(priority, 0) >= _PRIORITY_RANK.get(channel.get("min_priority", "info"), 0)


def dispatch(message: str, priority: str = "info", event_type: str = "system",
             tenant_id: str = "default") -> dict:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""SELECT type, config, event_types, min_priority, enabled
                    FROM notification_channels WHERE tenant_id = :tid AND enabled = true"""),
            {"tid": tenant_id},
        ).mappings().all()
    channels = [dict(r) for r in rows if channel_matches(dict(r), event_type, priority)]

    if not channels:
        return _legacy_fallback(message, priority)

    sent = 0
    for ch in channels:
        try:
            send_to_channel(ch["type"], ch["config"] or {}, message, priority, event_type)
            sent += 1
        except Exception as e:
            logger.error("notify channel '%s' failed: %s", ch["type"], mask_secrets(str(e)))
    return {"channels": len(channels), "sent": sent}


def _legacy_fallback(message: str, priority: str) -> dict:
    try:
        from config import settings
        if settings.TELEGRAM_BOT_TOKEN:
            from telegram_bot import send_alert_sync
            ok = send_alert_sync(message, priority)
            return {"channels": 0, "sent": int(bool(ok)), "fallback": "telegram_env"}
    except Exception as e:
        logger.error("legacy telegram fallback failed: %s", mask_secrets(str(e)))
    return {"channels": 0, "sent": 0, "silent": True}


def send_to_channel(ctype: str, cfg: dict, message: str, priority: str, event_type: str) -> None:
    if ctype == "telegram":
        _send_telegram(cfg, message, priority)
    elif ctype == "email":
        _send_email(cfg, message, priority, event_type)
    elif ctype == "webhook":
        _send_webhook(cfg, message, priority, event_type)
    elif ctype == "whatsapp_twilio":
        _send_whatsapp(cfg, message)
    else:
        raise ValueError(f"unknown channel type: {ctype}")


def _send_telegram(cfg: dict, message: str, priority: str) -> None:
    token, chat_id = cfg.get("bot_token"), cfg.get("chat_id")
    if not token or not chat_id:
        raise ValueError("telegram channel missing bot_token/chat_id")
    emoji = {"critical": "🔴", "warning": "🟠"}.get(priority, "ℹ️")
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": f"{emoji} {message}", "parse_mode": "HTML",
              "disable_notification": priority == "info"},
        timeout=(5, 10),
    )
    resp.raise_for_status()


def _send_email(cfg: dict, message: str, priority: str, event_type: str) -> None:
    host, to = cfg.get("host"), cfg.get("to")
    frm = cfg.get("from") or cfg.get("username")
    if not host or not to or not frm:
        raise ValueError("email channel missing host/to/from")
    msg = MIMEText(message)
    msg["Subject"] = f"[{priority.upper()}] {event_type} — Ситуационный центр"
    msg["From"], msg["To"] = frm, to
    with smtplib.SMTP(host, int(cfg.get("port", 587)), timeout=15) as s:
        if cfg.get("use_tls", True):
            s.starttls()
        if cfg.get("username"):
            s.login(cfg["username"], cfg.get("password", ""))
        s.sendmail(frm, [a.strip() for a in to.split(",")], msg.as_string())


def _send_webhook(cfg: dict, message: str, priority: str, event_type: str) -> None:
    from core.ssrf import guarded_request

    url = cfg.get("url")
    if not url:
        raise ValueError("webhook channel missing url")
    # SSRF guard: validate the URL (and every redirect hop) resolves to a public host.
    resp = guarded_request(
        requests.request, "POST", url,
        json={"message": message, "priority": priority, "event_type": event_type},
        headers=cfg.get("headers") or {},
        timeout=(5, 10),
    )
    resp.raise_for_status()


def _send_whatsapp(cfg: dict, message: str) -> None:
    sid, tok = cfg.get("account_sid"), cfg.get("auth_token")
    frm, to = cfg.get("from"), cfg.get("to")
    if not all([sid, tok, frm, to]):
        raise ValueError("whatsapp channel missing account_sid/auth_token/from/to")
    resp = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data={"From": f"whatsapp:{frm}", "To": f"whatsapp:{to}", "Body": message},
        auth=(sid, tok), timeout=(5, 15),
    )
    resp.raise_for_status()
