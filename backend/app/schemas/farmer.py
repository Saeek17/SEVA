from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re

class FarmerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    language: str = Field(default="hi", pattern="^(hi|mr|en)$")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    district: Optional[str] = None
    state: str = Field(default="Maharashtra")
    crop_id: str = Field(..., min_length=2)
    sowing_date: date
    consent_sms: bool = True
    consent_voice: bool = True

class FarmerCreate(FarmerBase):
    phone_number: str = Field(..., description="Indian 10-digit mobile or E.164 phone (+91...)")

    @field_validator("phone_number")
    @classmethod
    def validate_indian_phone(cls, v: str):
        clean = re.sub(r"[\s\-\(\)]", "", v)
        # Check standard 10-digit or +91 / 0 prefixed
        if re.match(r"^(\+91|91|0)?[6-9]\d{9}$", clean):
            # Normalize to +91XXXXXXXXXX
            if clean.startswith("+91"):
                return clean
            elif clean.startswith("91") and len(clean) == 12:
                return f"+{clean}"
            elif clean.startswith("0") and len(clean) == 11:
                return f"+91{clean[1:]}"
            elif len(clean) == 10:
                return f"+91{clean}"
            return clean
        raise ValueError("Invalid phone number. Must be a valid 10-digit Indian mobile number (+91XXXXXXXXXX).")

    @field_validator("consent_sms", "consent_voice")
    @classmethod
    def check_consent(cls, v: bool):
        if not v:
            raise ValueError("Farmer consent is mandatory for receiving advisory communications.")
        return v

class FarmerResponse(FarmerBase):
    id: str
    phone_masked: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
