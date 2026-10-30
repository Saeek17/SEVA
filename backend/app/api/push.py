import logging
from datetime import date, timedelta
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.push import PushSubscription
from app.services.crop_engine.loader import crop_loader
from app.services.delivery.push_service import push_enabled

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/push", tags=["Web Push"])

class PushKeys(BaseModel):
    p256dh: str
    auth: str

class PushSubscribeRequest(BaseModel):
    endpoint: str = Field(..., min_length=10)
    keys: PushKeys
    language: str = Field(default="mr", pattern="^(hi|mr|en)$")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    crop_id: str
    das: int = Field(..., ge=1, le=400, description="Crop age in days today; used to derive the sowing date")

class PushUnsubscribeRequest(BaseModel):
    endpoint: str

@router.get("/public-key")
async def get_public_key() -> Dict[str, object]:
    """Tells the PWA whether notifications are available and gives it the VAPID public key."""
    return {"enabled": push_enabled(), "public_key": settings.VAPID_PUBLIC_KEY if push_enabled() else ""}

@router.post("/subscribe", status_code=201)
async def subscribe(payload: PushSubscribeRequest, db: Session = Depends(get_db)):
    if not push_enabled():
        raise HTTPException(status_code=503, detail="Push notifications are not configured on this server.")
    if not crop_loader.get_crop(payload.crop_id):
        raise HTTPException(status_code=404, detail=f"Crop '{payload.crop_id}' not found")

    sowing = date.today() - timedelta(days=payload.das)
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if sub is None:
        sub = PushSubscription(endpoint=payload.endpoint, p256dh=payload.keys.p256dh, auth=payload.keys.auth,
                               language=payload.language, latitude=payload.latitude, longitude=payload.longitude,
                               crop_id=payload.crop_id, sowing_date=sowing)
        db.add(sub)
    else:
        sub.p256dh, sub.auth = payload.keys.p256dh, payload.keys.auth
        sub.language, sub.latitude, sub.longitude = payload.language, payload.latitude, payload.longitude
        sub.crop_id, sub.sowing_date, sub.is_active = payload.crop_id, sowing, True
    db.commit()
    return {"status": "subscribed", "id": sub.id}

@router.post("/unsubscribe")
async def unsubscribe(payload: PushUnsubscribeRequest, db: Session = Depends(get_db)):
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if sub:
        sub.is_active = False
        db.commit()
    return {"status": "unsubscribed"}
