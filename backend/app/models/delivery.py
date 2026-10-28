import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    advisory_run_id = Column(String(36), ForeignKey("advisory_runs.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(20), nullable=False) # SMS, VOICE
    provider = Column(String(50), nullable=False, default="TWILIO") # TWILIO, EXOTEL, MOCK
    external_sid = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="QUEUED") # QUEUED, SENT, DELIVERED, FAILED
    attempt_count = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    dispatched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    advisory_run = relationship("AdvisoryRun", back_populates="delivery_logs")
