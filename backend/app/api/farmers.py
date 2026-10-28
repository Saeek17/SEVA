import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerResponse
from app.security import encrypt_phone, hash_phone, mask_phone, decrypt_phone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/farmers", tags=["Farmers"])

@router.get("", response_model=List[FarmerResponse])
async def list_farmers(
    crop_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Farmer)
    if crop_id:
        query = query.filter(Farmer.crop_id == crop_id)
    if is_active is not None:
        query = query.filter(Farmer.is_active == is_active)

    farmers = query.order_by(Farmer.created_at.desc()).all()
    results = []
    for f in farmers:
        decrypted = decrypt_phone(f.phone_encrypted)
        results.append(
            FarmerResponse(
                id=f.id,
                full_name=f.full_name,
                phone_masked=mask_phone(decrypted),
                language=f.language,
                latitude=f.latitude,
                longitude=f.longitude,
                district=f.district,
                state=f.state,
                crop_id=f.crop_id,
                sowing_date=f.sowing_date,
                consent_sms=f.consent_sms,
                consent_voice=f.consent_voice,
                is_active=f.is_active,
                created_at=f.created_at,
                updated_at=f.updated_at
            )
        )
    return results

@router.post("", response_model=FarmerResponse, status_code=201)
async def register_farmer(payload: FarmerCreate, db: Session = Depends(get_db)):
    """
    Register a new smallholder farmer.
    Encrypts phone number with Fernet AES-256 at rest, computes indexed HMAC-SHA256,
    and logs consent.
    """
    p_hash = hash_phone(payload.phone_number)
    existing = db.query(Farmer).filter(Farmer.phone_hash == p_hash).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A farmer with this mobile number is already registered."
        )

    farmer = Farmer(
        full_name=payload.full_name,
        phone_encrypted=encrypt_phone(payload.phone_number),
        phone_hash=p_hash,
        language=payload.language,
        latitude=payload.latitude,
        longitude=payload.longitude,
        district=payload.district or "Maharashtra",
        state=payload.state,
        crop_id=payload.crop_id,
        sowing_date=payload.sowing_date,
        consent_sms=payload.consent_sms,
        consent_voice=payload.consent_voice,
        consent_timestamp=datetime.utcnow(),
        is_active=True
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)

    return FarmerResponse(
        id=farmer.id,
        full_name=farmer.full_name,
        phone_masked=mask_phone(payload.phone_number),
        language=farmer.language,
        latitude=farmer.latitude,
        longitude=farmer.longitude,
        district=farmer.district,
        state=farmer.state,
        crop_id=farmer.crop_id,
        sowing_date=farmer.sowing_date,
        consent_sms=farmer.consent_sms,
        consent_voice=farmer.consent_voice,
        is_active=farmer.is_active,
        created_at=farmer.created_at,
        updated_at=farmer.updated_at
    )

@router.get("/{farmer_id}", response_model=FarmerResponse)
async def get_farmer(farmer_id: str, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    decrypted = decrypt_phone(farmer.phone_encrypted)
    return FarmerResponse(
        id=farmer.id,
        full_name=farmer.full_name,
        phone_masked=mask_phone(decrypted),
        language=farmer.language,
        latitude=farmer.latitude,
        longitude=farmer.longitude,
        district=farmer.district,
        state=farmer.state,
        crop_id=farmer.crop_id,
        sowing_date=farmer.sowing_date,
        consent_sms=farmer.consent_sms,
        consent_voice=farmer.consent_voice,
        is_active=farmer.is_active,
        created_at=farmer.created_at,
        updated_at=farmer.updated_at
    )

@router.delete("/{farmer_id}")
async def deactivate_farmer(farmer_id: str, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    farmer.is_active = False
    db.commit()
    return {"status": "deactivated", "farmer_id": farmer_id}
