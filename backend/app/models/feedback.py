import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime

from app.database import Base

class AdviceFeedback(Base):
    """Anonymous thumbs up/down on an advice card. No farmer identity or location is stored."""
    __tablename__ = "advice_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    helpful = Column(Boolean, nullable=False)
    crop_id = Column(String(100), nullable=False)
    action = Column(String(40), nullable=False)
    reason_code = Column(String(80), nullable=True)
    das = Column(Integer, nullable=True)
    language = Column(String(5), nullable=False, default="mr")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
