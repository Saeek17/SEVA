import uuid
import logging
from typing import Dict, Any
from app.config import settings
from app.services.delivery.base import BaseDeliveryProvider

logger = logging.getLogger(__name__)

def absolute_url(url: str) -> str:
    """Twilio fetches audio over the public internet, so relative API paths need PUBLIC_BASE_URL."""
    if url.startswith(("http://", "https://")) or not settings.PUBLIC_BASE_URL:
        return url
    return settings.PUBLIC_BASE_URL.rstrip("/") + "/" + url.lstrip("/")

class TwilioDeliveryProvider(BaseDeliveryProvider):
    """
    Twilio SMS and Outbound Voice Call delivery provider.
    Automatically enters dry-run mock mode when DRY_RUN=True or Twilio credentials are blank.
    """
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_FROM_PHONE
        self.whatsapp_from = settings.TWILIO_WHATSAPP_FROM
        self._client = None

        if self.account_sid and self.auth_token and not settings.DRY_RUN:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
                logger.info("Initialized Twilio production client.")
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio client: {e}. Falling back to mock delivery.")

    async def send_sms(self, to_phone: str, message: str, advisory_id: str) -> Dict[str, Any]:
        if self._client and not settings.DRY_RUN:
            try:
                msg = self._client.messages.create(
                    body=message,
                    from_=self.from_phone,
                    to=to_phone
                )
                logger.info(f"Twilio SMS sent to {to_phone}. SID: {msg.sid}")
                return {
                    "provider": "TWILIO",
                    "status": "SENT",
                    "sid": msg.sid,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Twilio SMS dispatch failed: {e}")
                return {
                    "provider": "TWILIO",
                    "status": "FAILED",
                    "sid": None,
                    "error": str(e)
                }

        # Mock Dry-Run Dispatch
        mock_sid = f"SM_mock_{uuid.uuid4().hex[:16]}"
        logger.info(f"[DRY RUN SMS] To: {to_phone} | SID: {mock_sid} | Text: {message}")
        return {
            "provider": "MOCK_TWILIO",
            "status": "DELIVERED",
            "sid": mock_sid,
            "error": None
        }

    async def send_whatsapp(self, to_phone: str, message: str, advisory_id: str) -> Dict[str, Any]:
        if not self.whatsapp_from:
            return {"provider": "TWILIO", "status": "SKIPPED", "sid": None, "error": "TWILIO_WHATSAPP_FROM not set"}

        if self._client and not settings.DRY_RUN:
            try:
                msg = self._client.messages.create(
                    body=message,
                    from_=f"whatsapp:{self.whatsapp_from}",
                    to=f"whatsapp:{to_phone}"
                )
                logger.info(f"Twilio WhatsApp sent to {to_phone}. SID: {msg.sid}")
                return {"provider": "TWILIO", "status": "SENT", "sid": msg.sid, "error": None}
            except Exception as e:
                logger.error(f"Twilio WhatsApp dispatch failed: {e}")
                return {"provider": "TWILIO", "status": "FAILED", "sid": None, "error": str(e)}

        mock_sid = f"WA_mock_{uuid.uuid4().hex[:16]}"
        logger.info(f"[DRY RUN WHATSAPP] To: {to_phone} | SID: {mock_sid} | Text: {message}")
        return {"provider": "MOCK_TWILIO", "status": "DELIVERED", "sid": mock_sid, "error": None}

    async def make_voice_call(self, to_phone: str, audio_url: str, advisory_id: str) -> Dict[str, Any]:
        if self._client and not settings.DRY_RUN:
            try:
                twiml = f"<Response><Play>{absolute_url(audio_url)}</Play></Response>"
                call = self._client.calls.create(
                    to=to_phone,
                    from_=self.from_phone,
                    twiml=twiml
                )
                logger.info(f"Twilio Voice Call initiated to {to_phone}. SID: {call.sid}")
                return {
                    "provider": "TWILIO",
                    "status": "QUEUED",
                    "sid": call.sid,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Twilio Voice dispatch failed: {e}")
                return {
                    "provider": "TWILIO",
                    "status": "FAILED",
                    "sid": None,
                    "error": str(e)
                }

        mock_call_sid = f"CA_mock_{uuid.uuid4().hex[:16]}"
        logger.info(f"[DRY RUN VOICE] To: {to_phone} | SID: {mock_call_sid} | Audio: {audio_url}")
        return {
            "provider": "MOCK_TWILIO",
            "status": "DELIVERED",
            "sid": mock_call_sid,
            "error": None
        }
