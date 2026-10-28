import pytest
from pathlib import Path
from pydantic import ValidationError
from app.services.crop_engine.loader import CropConfigLoader
from app.schemas.crop_config import CropConfig, GrowthStage, MoistureThresholds, TemperatureThresholds, SprayingConstraints

def test_load_official_crops():
    loader = CropConfigLoader()
    crops = loader.load_all_crops(force_reload=True)
    assert "wheat_maharashtra" in crops
    assert "soybean_maharashtra" in crops

    wheat = crops["wheat_maharashtra"]
    assert wheat.common_name_en == "Wheat"
    assert len(wheat.stages) >= 4
    assert len(wheat.citations) >= 1
    # Check that CRI stage is marked critical for irrigation
    cri_stage = next(s for s in wheat.stages if s.stage_id == "germination_crown_root")
    assert cri_stage.critical_for_irrigation is True
    assert cri_stage.moisture.depletion_trigger_pct == 35.0

    soybean = crops["soybean_maharashtra"]
    assert soybean.common_name_en == "Soybean"
    assert len(soybean.stages) >= 4
    flowering = next(s for s in soybean.stages if s.stage_id == "flowering")
    assert flowering.critical_for_irrigation is True

def test_malformed_overlapping_stages_fails_loudly():
    malformed_data = {
        "crop_id": "invalid_crop",
        "common_name_en": "Invalid",
        "common_name_hi": "अमान्य",
        "common_name_mr": "अवैध",
        "scientific_name": "Test test",
        "typical_duration_days": 100,
        "region": "Maharashtra",
        "citations": [{"document": "Test", "section": "p.1"}],
        "general_thresholds": {
            "heat_stress_warning_c": 35.0,
            "heat_stress_source": "Test",
            "frost_stress_warning_c": 5.0,
            "frost_stress_source": "Test",
            "excess_rain_24h_mm": 40.0,
            "excess_rain_source": "Test"
        },
        "stages": [
            {
                "stage_id": "stage_1",
                "name_en": "Stage 1",
                "name_hi": "चरण 1",
                "name_mr": "टप्पा 1",
                "das_start": 1,
                "das_end": 30, # Overlaps with stage 2 starting at 25
                "critical_for_irrigation": True,
                "moisture": {"root_depth_cm": 20, "depletion_trigger_pct": 40.0, "source": "Test"},
                "temperature": {"min_optimal_c": 15.0, "max_optimal_c": 25.0, "heat_stress_c": 35.0, "frost_stress_c": 5.0, "source": "Test"},
                "spraying": {"max_wind_kmh": 15.0, "min_temp_c": 15.0, "max_temp_c": 30.0, "max_rain_probability_pct": 30.0, "min_relative_humidity_pct": 40.0, "source": "Test"}
            },
            {
                "stage_id": "stage_2",
                "name_en": "Stage 2",
                "name_hi": "चरण 2",
                "name_mr": "टप्पा 2",
                "das_start": 25, # OVERLAP
                "das_end": 50,
                "critical_for_irrigation": False,
                "moisture": {"root_depth_cm": 30, "depletion_trigger_pct": 40.0, "source": "Test"},
                "temperature": {"min_optimal_c": 15.0, "max_optimal_c": 25.0, "heat_stress_c": 35.0, "frost_stress_c": 5.0, "source": "Test"},
                "spraying": {"max_wind_kmh": 15.0, "min_temp_c": 15.0, "max_temp_c": 30.0, "max_rain_probability_pct": 30.0, "min_relative_humidity_pct": 40.0, "source": "Test"}
            }
        ]
    }
    with pytest.raises(ValidationError) as excinfo:
        CropConfig(**malformed_data)
    assert "Overlapping DAS ranges" in str(excinfo.value)
