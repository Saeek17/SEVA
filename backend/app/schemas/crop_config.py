from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator

class Citation(BaseModel):
    document: str = Field(..., description="Name of manual, journal, or university package of practices")
    section: str = Field(..., description="Section, chapter, or page number")

class GeneralThresholds(BaseModel):
    heat_stress_warning_c: float = Field(..., description="Ambient temperature triggering heat alert")
    heat_stress_source: str = Field(..., description="Document source or citation")
    frost_stress_warning_c: float = Field(..., description="Ambient temperature triggering frost alert")
    frost_stress_source: str = Field(..., description="Document source or citation")
    excess_rain_24h_mm: float = Field(..., description="24-hour rainfall triggering waterlogging alert")
    excess_rain_source: str = Field(..., description="Document source or citation")

class TemperatureThresholds(BaseModel):
    min_optimal_c: float
    max_optimal_c: float
    heat_stress_c: float
    frost_stress_c: float
    source: str

    @model_validator(mode="after")
    def check_temp_order(self):
        if self.min_optimal_c > self.max_optimal_c:
            raise ValueError(f"min_optimal_c ({self.min_optimal_c}) cannot exceed max_optimal_c ({self.max_optimal_c})")
        if self.frost_stress_c > self.min_optimal_c:
            raise ValueError(f"frost_stress_c ({self.frost_stress_c}) must be <= min_optimal_c ({self.min_optimal_c})")
        return self

class MoistureThresholds(BaseModel):
    root_depth_cm: int = Field(..., gt=0)
    depletion_trigger_pct: float = Field(..., ge=0.0, le=100.0, description="Available soil moisture percentage that triggers irrigation")
    waterlogging_threshold_pct: float = Field(default=85.0, ge=0.0, le=100.0)
    source: str

class SprayingConstraints(BaseModel):
    max_wind_kmh: float = Field(..., gt=0)
    min_temp_c: float
    max_temp_c: float
    max_rain_probability_pct: float = Field(..., ge=0.0, le=100.0)
    min_relative_humidity_pct: float = Field(..., ge=0.0, le=100.0)
    source: str

    @model_validator(mode="after")
    def check_spray_temps(self):
        if self.min_temp_c > self.max_temp_c:
            raise ValueError("min_temp_c cannot exceed max_temp_c for spraying")
        return self

class GrowthStage(BaseModel):
    stage_id: str = Field(..., min_length=2)
    name_en: str
    name_hi: str
    name_mr: str
    das_start: int = Field(..., ge=1)
    das_end: int = Field(..., ge=1)
    critical_for_irrigation: bool = False
    critical_reason: Optional[str] = None
    moisture: MoistureThresholds
    temperature: TemperatureThresholds
    spraying: SprayingConstraints

    @model_validator(mode="after")
    def validate_stage_ranges(self):
        if self.das_start > self.das_end:
            raise ValueError(f"Stage '{self.stage_id}': das_start ({self.das_start}) cannot exceed das_end ({self.das_end})")
        return self

class CropConfig(BaseModel):
    crop_id: str = Field(..., min_length=2)
    common_name_en: str
    common_name_hi: str
    common_name_mr: str
    scientific_name: str
    typical_duration_days: int = Field(..., ge=30, le=365)
    region: str
    citations: List[Citation]
    general_thresholds: GeneralThresholds
    stages: List[GrowthStage]

    @field_validator("stages")
    @classmethod
    def validate_stages(cls, stages: List[GrowthStage]):
        if not stages:
            raise ValueError("Crop configuration must define at least one growth stage")
        # Check chronological ordering and no overlapping or negative gaps
        sorted_stages = sorted(stages, key=lambda s: s.das_start)
        for i in range(len(sorted_stages) - 1):
            curr = sorted_stages[i]
            nxt = sorted_stages[i + 1]
            if curr.das_end >= nxt.das_start:
                raise ValueError(
                    f"Overlapping DAS ranges between stage '{curr.stage_id}' ({curr.das_start}-{curr.das_end}) "
                    f"and stage '{nxt.stage_id}' ({nxt.das_start}-{nxt.das_end})"
                )
        return stages
