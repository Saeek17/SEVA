import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base

class AdvisoryRun(Base):
    __tablename__ = "advisory_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farmer_id = Column(String(36), ForeignKey("farmers.id", ondelete="SET NULL"), nullable=True)
    crop_id = Column(String(100), nullable=False)
    growth_stage = Column(String(100), nullable=False)
    das = Column(Integer, nullable=False) # Days After Sowing

    # Snapshots stored as JSON strings for cross-DB compatibility (SQLite + Postgres)
    raw_weather_snapshot = Column(Text, nullable=True)
    raw_soil_snapshot = Column(Text, nullable=True)

    data_confidence = Column(String(20), default="HIGH") # "HIGH", "MEDIUM", "LOW"
    sources_used = Column(String(255), default="Open-Meteo, NASA POWER, ISRIC SoilGrids")

    # Vernacular output
    generated_message = Column(Text, nullable=False)
    language = Column(String(5), default="hi")
    validation_passed = Column(Boolean, default=True)
    validation_notes = Column(Text, nullable=True)
    fallback_used = Column(String(30), default="NONE") # "NONE", "DLT_TEMPLATE"
    voice_audio_path = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    farmer = relationship("Farmer", back_populates="advisories")
    advice_items = relationship("AdviceItemModel", back_populates="advisory_run", cascade="all, delete-orphan")
    delivery_logs = relationship("DeliveryLog", back_populates="advisory_run", cascade="all, delete-orphan")

    def get_weather_json(self):
        try:
            return json.loads(self.raw_weather_snapshot) if self.raw_weather_snapshot else {}
        except Exception:
            return {}

    def get_soil_json(self):
        try:
            return json.loads(self.raw_soil_snapshot) if self.raw_soil_snapshot else {}
        except Exception:
            return {}

class AdviceItemModel(Base):
    __tablename__ = "advice_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    advisory_run_id = Column(String(36), ForeignKey("advisory_runs.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False) # IRRIGATE, SAFE_SPRAY, etc.
    urgency = Column(String(20), nullable=False) # HIGH, MEDIUM, LOW
    reason_code = Column(String(100), nullable=False)
    params_json = Column(Text, nullable=True)
    source_citation = Column(String(255), nullable=True)
    priority_rank = Column(Integer, default=1)

    advisory_run = relationship("AdvisoryRun", back_populates="advice_items")

    def get_params(self):
        try:
            return json.loads(self.params_json) if self.params_json else {}
        except Exception:
            return {}
