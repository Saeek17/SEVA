import asyncio
import json
import logging
from typing import Dict, Any

from app.config import settings
from app.models.push import PushSubscription

logger = logging.getLogger(__name__)

def push_enabled() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)

async def send_push(sub: PushSubscription, title: str, body: str, url: str = "/kisan") -> Dict[str, Any]:
    """
    Deliver one Web Push notification. Returns {"status": "SENT" | "GONE" | "FAILED" | "SKIPPED"}.
    GONE means the browser revoked the subscription (HTTP 404/410) and it should be deactivated.
    """
    if not push_enabled():
        return {"status": "SKIPPED", "error": "VAPID keys not configured"}

    if settings.DRY_RUN:
        logger.info(f"[DRY RUN PUSH] {title} | {body}")
        return {"status": "SENT", "error": None}

    from pywebpush import webpush, WebPushException

    payload = json.dumps({"title": title, "body": body, "url": url}, ensure_ascii=False)

    def _send():
        webpush(
            subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
            ttl=6 * 3600,
        )

    try:
        await asyncio.to_thread(_send)
        return {"status": "SENT", "error": None}
    except WebPushException as e:
        code = getattr(e.response, "status_code", None)
        if code in (404, 410):
            return {"status": "GONE", "error": str(e)}
        logger.error(f"Web Push failed: {e}")
        return {"status": "FAILED", "error": str(e)}
    except Exception as e:
        logger.error(f"Web Push failed: {e}")
        return {"status": "FAILED", "error": str(e)}
