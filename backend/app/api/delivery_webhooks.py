import logging
from pathlib import Path
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.farmer import Farmer
from app.models.delivery import DeliveryLog
from app.security import hash_phone
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/delivery", tags=["Delivery & Webhooks"])

def _valid_twilio_signature(request: Request, form) -> bool:
    """
    Reject forged webhook calls (they would trigger paid callbacks). Enforced only when real Twilio
    credentials are configured and DRY_RUN is off, so local development keeps working.
    """
    if settings.DRY_RUN or not settings.TWILIO_AUTH_TOKEN:
        return True
    from twilio.request_validator import RequestValidator
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    url = f"{base}{request.url.path}" if base else str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    return RequestValidator(settings.TWILIO_AUTH_TOKEN).validate(url, dict(form), signature)

async def _callback_task(phone: str):
    # Own session: the request-scoped one is closed once the TwiML response has been sent.
    from app.services.scheduler.task_scheduler import scheduler_service
    db = SessionLocal()
    try:
        found = await scheduler_service.call_back_farmer(phone, db)
        if not found:
            logger.info("Missed call from an unregistered number; no callback placed.")
    except Exception as e:
        logger.error(f"Missed-call callback failed: {e}")
    finally:
        db.close()

@router.post("/webhooks/ivr")
async def missed_call_ivr(request: Request, background: BackgroundTasks):
    """
    Missed-call IVR. Point the Twilio number's "A call comes in" webhook here.
    The call is rejected (free for the farmer, shows as a missed call), then KisanSaathi calls the
    farmer back and plays today's advice in their language. Works on any basic phone.
    """
    form = await request.form()
    if not _valid_twilio_signature(request, form):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    caller = form.get("From")
    if caller:
        background.add_task(_callback_task, caller)
    return Response(content='<Response><Reject reason="rejected"/></Response>', media_type="application/xml")
AUDIO_DIR = settings.BACKEND_DIR / "app" / "static" / "audio"

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve synthesized TTS audio for browser preview and voice call playback."""
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    media_type = "audio/mpeg" if file_path.suffix == ".mp3" else "audio/wav"
    return FileResponse(file_path, media_type=media_type)

@router.post("/webhooks/sms")
async def twilio_sms_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Twilio SMS webhook handling:
    1. Status callbacks (DELIVERED, FAILED, UNDELIVERED).
    2. Inbound opt-out keywords ('STOP', 'थांबवा', 'रोकें') setting is_active = False.
    """
    form_data = await request.form()
    if not _valid_twilio_signature(request, form_data):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    message_sid = form_data.get("MessageSid") or form_data.get("SmsSid")
    message_status = form_data.get("MessageStatus") or form_data.get("SmsStatus")
    body = (form_data.get("Body") or "").strip().upper()
    from_phone = form_data.get("From")

    logger.info(f"Received SMS Webhook: SID={message_sid}, Status={message_status}, Body='{body}'")

    # 1. Update delivery status if tracking SID
    if message_sid and message_status:
        log = db.query(DeliveryLog).filter(DeliveryLog.external_sid == message_sid).first()
        if log:
            log.status = message_status.upper()
            db.commit()

    # 2. Check for STOP / Opt-Out request
    opt_out_keywords = {"STOP", "UNSUBSCRIBE", "CANCEL", "QUIT", "END", "थांबवा", "रोकें", "बंद"}
    if body in opt_out_keywords and from_phone:
        p_hash = hash_phone(from_phone)
        farmer = db.query(Farmer).filter(Farmer.phone_hash == p_hash).first()
        if farmer:
            farmer.is_active = False
            db.commit()
            logger.info(f"Farmer {farmer.id} opted out via STOP keyword. Set is_active=False.")
            twiml_resp = (
                "<Response><Message>KisanSaathi: You have successfully unsubscribed from agro-advisories. "
                "Reply START anytime to resume.</Message></Response>"
            )
            return Response(content=twiml_resp, media_type="application/xml")

    return Response(content="<Response></Response>", media_type="application/xml")

@router.post("/webhooks/voice")
async def twilio_voice_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Twilio Voice status callback and TwiML responder.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")

    if call_sid and call_status:
        log = db.query(DeliveryLog).filter(DeliveryLog.external_sid == call_sid).first()
        if log:
            log.status = call_status.upper()
            db.commit()

    return Response(
        content="<Response><Say language='hi-IN'>KisanSaathi agro advisory</Say></Response>",
        media_type="application/xml"
    )
