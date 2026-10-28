from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

class UrgencyLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AdviceAction(str, Enum):
    IRRIGATE = "IRRIGATE"
    SKIP_IRRIGATION = "SKIP_IRRIGATION"
    SCHEDULE_IRRIGATION = "SCHEDULE_IRRIGATION"
    SAFE_SPRAY = "SAFE_SPRAY"
    AVOID_SPRAY = "AVOID_SPRAY"
    HEAT_ALERT = "HEAT_ALERT"
    FROST_ALERT = "FROST_ALERT"
    RAIN_ALERT = "RAIN_ALERT"
    DROUGHT_ALERT = "DROUGHT_ALERT"
    HARVEST_READY = "HARVEST_READY"
    MONITOR_CROP = "MONITOR_CROP"

class AdviceItem(BaseModel):
    action: AdviceAction
    urgency: UrgencyLevel
    reason_code: str
    params: Dict[str, Any] = Field(default_factory=dict)
    data_confidence: str = Field(default="HIGH", description="HIGH, MEDIUM, or LOW based on data client availability")
    sources_used: List[str] = Field(default_factory=list)

class EnvironmentalSnapshot(BaseModel):
    latitude: float
    longitude: float
    # Weather Forecast
    forecast_max_temp_c: float
    forecast_min_temp_c: float
    forecast_rain_24h_mm: float
    forecast_rain_48h_mm: float
    forecast_rain_7d_mm: float
    rain_probability_pct: float
    wind_speed_kmh: float
    relative_humidity_pct: float
    # Soil Data
    soil_moisture_0_7cm_pct: float
    soil_moisture_7_28cm_pct: float
    soil_temp_0_7cm_c: float
    soil_texture_class: str # e.g. "Clay loam", "Black cotton soil / Clay"
    # Historical Trends (NASA POWER)
    consecutive_dry_days: int # Days with rain < 2.5mm
    cumulative_rain_30d_mm: float
    # Confidence & metadata
    data_confidence: str = "HIGH"
    sources_used: List[str] = Field(default_factory=lambda: ["Open-Meteo", "NASA POWER", "ISRIC SoilGrids"])
