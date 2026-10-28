import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Date, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(120), nullable=False)
    phone_encrypted = Column(Text, nullable=False)
    phone_hash = Column(String(64), nullable=False, index=True)
    language = Column(String(5), nullable=False, default="hi") # "hi", "mr", "en"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=False, default="Maharashtra")
    crop_id = Column(String(100), nullable=False) # e.g. "wheat_maharashtra", "soybean_maharashtra"
    sowing_date = Column(Date, nullable=False)
    
    # Consent and Privacy
    consent_sms = Column(Boolean, default=True, nullable=False)
    consent_voice = Column(Boolean, default=True, nullable=False)
    consent_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False) # Flipped to False if farmer sends "STOP"
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    advisories = relationship("AdvisoryRun", back_populates="farmer", cascade="all, delete-orphan")
