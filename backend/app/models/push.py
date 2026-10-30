import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Date, Text

from app.database import Base

class PushSubscription(Base):
    """A browser/PWA Web Push subscription plus the farm context needed to build its daily advice."""
    __tablename__ = "push_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    language = Column(String(5), nullable=False, default="mr")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    crop_id = Column(String(100), nullable=False)
    sowing_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
