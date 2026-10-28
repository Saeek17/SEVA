from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.schemas.rules import AdviceItem, EnvironmentalSnapshot

class AdvisoryRunResponse(BaseModel):
    id: str
    farmer_id: Optional[str] = None
    crop_id: str
    growth_stage: str
    das: int
    data_confidence: str
    sources_used: str
    generated_message: str
    language: str
    validation_passed: bool
    validation_notes: Optional[str] = None
    fallback_used: str
    voice_audio_path: Optional[str] = None
    created_at: datetime
    advice_items: List[AdviceItem] = []
    model_config = {"from_attributes": True}

class SimulationRequest(BaseModel):
    latitude: float
    longitude: float
    crop_id: str
    sowing_date: Optional[str] = None # YYYY-MM-DD
    das: Optional[int] = None # If given directly
    language: str = "hi" # hi, mr, en
    farmer_name: Optional[str] = "Demo Farmer"

class SimulationResponse(BaseModel):
    status: str = "success"
    crop_id: str
    crop_name: str
    growth_stage: str
    das: int
    environmental_data: EnvironmentalSnapshot
    advice_items: List[AdviceItem]
    generated_message: str
    language: str
    validation_passed: bool
    validation_notes: Optional[str] = None
    fallback_used: str
    voice_audio_url: Optional[str] = None
