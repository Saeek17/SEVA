import pytest
from app.schemas.rules import (
    AdviceAction,
    UrgencyLevel,
    EnvironmentalSnapshot
)
from app.services.crop_engine.loader import CropConfigLoader
from app.services.crop_engine.stage_calculator import StageCalculator
from app.services.crop_engine.rules_engine import RulesEngine

@pytest.fixture
def wheat_crop():
    loader = CropConfigLoader()
    return loader.get_crop("wheat_maharashtra")

@pytest.fixture
def soybean_crop():
    loader = CropConfigLoader()
    return loader.get_crop("soybean_maharashtra")

def test_critical_irrigation_trigger(wheat_crop):
    # Wheat at CRI stage (DAS 21): soil moisture depleted to 25% (trigger is 35%), dry weather ahead
    stage, _ = StageCalculator.resolve_stage(wheat_crop, das=21)
    env = EnvironmentalSnapshot(
        latitude=18.52,
        longitude=73.85,
        forecast_max_temp_c=28.0,
        forecast_min_temp_c=14.0,
        forecast_rain_24h_mm=0.0,
        forecast_rain_48h_mm=0.0,
        forecast_rain_7d_mm=0.0,
        rain_probability_pct=5.0,
        wind_speed_kmh=8.0,
        relative_humidity_pct=45.0,
        soil_moisture_0_7cm_pct=25.0, # Depleted below 35% trigger
        soil_moisture_7_28cm_pct=28.0,
        soil_temp_0_7cm_c=22.0,
        soil_texture_class="Clay Loam",
        consecutive_dry_days=8,
        cumulative_rain_30d_mm=10.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo", "ISRIC"]
    )

    items = RulesEngine.evaluate(wheat_crop, stage, das=21, env=env)
    irrigation_item = next((i for i in items if i.action == AdviceAction.IRRIGATE), None)
    
    assert irrigation_item is not None
    assert irrigation_item.urgency == UrgencyLevel.HIGH
    assert irrigation_item.reason_code == "CRITICAL_STAGE_MOISTURE_DEFICIT"
    assert irrigation_item.params["soil_moisture_pct"] == 25.0

def test_skip_irrigation_due_to_forecast_rain(wheat_crop):
    # Soil moisture is low (25%), but 30mm rainfall forecast in next 48h -> MUST SKIP
    stage, _ = StageCalculator.resolve_stage(wheat_crop, das=21)
    env = EnvironmentalSnapshot(
        latitude=18.52,
        longitude=73.85,
        forecast_max_temp_c=27.0,
        forecast_min_temp_c=16.0,
        forecast_rain_24h_mm=18.0,
        forecast_rain_48h_mm=30.0, # Significant rain imminent
        forecast_rain_7d_mm=45.0,
        rain_probability_pct=80.0,
        wind_speed_kmh=12.0,
        relative_humidity_pct=75.0,
        soil_moisture_0_7cm_pct=25.0,
        soil_moisture_7_28cm_pct=28.0,
        soil_temp_0_7cm_c=22.0,
        soil_texture_class="Clay Loam",
        consecutive_dry_days=0,
        cumulative_rain_30d_mm=10.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo"]
    )

    items = RulesEngine.evaluate(wheat_crop, stage, das=21, env=env)
    skip_item = next((i for i in items if i.action == AdviceAction.SKIP_IRRIGATION), None)
    
    assert skip_item is not None
    assert skip_item.reason_code == "ANTICIPATED_RAIN_OR_SATURATED"
    # Should not advise irrigation
    assert not any(i.action == AdviceAction.IRRIGATE for i in items)

def test_spray_wind_drift_hazard(soybean_crop):
    # Soybean at flowering (DAS 45): wind is 19 km/h (limit is 12 km/h) -> AVOID_SPRAY
    stage, _ = StageCalculator.resolve_stage(soybean_crop, das=45)
    env = EnvironmentalSnapshot(
        latitude=18.40,
        longitude=76.56,
        forecast_max_temp_c=29.0,
        forecast_min_temp_c=21.0,
        forecast_rain_24h_mm=0.0,
        forecast_rain_48h_mm=0.0,
        forecast_rain_7d_mm=5.0,
        rain_probability_pct=10.0,
        wind_speed_kmh=19.0, # Exceeds 12 km/h threshold
        relative_humidity_pct=50.0,
        soil_moisture_0_7cm_pct=40.0,
        soil_moisture_7_28cm_pct=42.0,
        soil_temp_0_7cm_c=25.0,
        soil_texture_class="Black Cotton Soil",
        consecutive_dry_days=4,
        cumulative_rain_30d_mm=35.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo"]
    )

    items = RulesEngine.evaluate(soybean_crop, stage, das=45, env=env)
    spray_item = next((i for i in items if i.action in (AdviceAction.AVOID_SPRAY, AdviceAction.SAFE_SPRAY)), None)
    
    assert spray_item is not None
    assert spray_item.action == AdviceAction.AVOID_SPRAY
    assert spray_item.reason_code == "HIGH_WIND_DRIFT_HAZARD"

def test_heat_stress_alert(wheat_crop):
    # Wheat at flowering (DAS 65): max temp reaches 36C (heat stress limit is 34C) -> HEAT_ALERT
    stage, _ = StageCalculator.resolve_stage(wheat_crop, das=65)
    env = EnvironmentalSnapshot(
        latitude=18.52,
        longitude=73.85,
        forecast_max_temp_c=36.0, # Triggers heat alert
        forecast_min_temp_c=18.0,
        forecast_rain_24h_mm=0.0,
        forecast_rain_48h_mm=0.0,
        forecast_rain_7d_mm=0.0,
        rain_probability_pct=5.0,
        wind_speed_kmh=9.0,
        relative_humidity_pct=35.0,
        soil_moisture_0_7cm_pct=38.0,
        soil_moisture_7_28cm_pct=40.0,
        soil_temp_0_7cm_c=28.0,
        soil_texture_class="Clay Loam",
        consecutive_dry_days=10,
        cumulative_rain_30d_mm=5.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo"]
    )

    items = RulesEngine.evaluate(wheat_crop, stage, das=65, env=env)
    heat_alert = next((i for i in items if i.action == AdviceAction.HEAT_ALERT), None)
    
    assert heat_alert is not None
    assert heat_alert.urgency == UrgencyLevel.HIGH
    assert heat_alert.reason_code == "EXTREME_HEAT_STRESS"

def test_maturity_irrigation_withhold_and_harvest(wheat_crop):
    # Wheat at maturity (DAS 115): withhold irrigation, plan harvest
    stage, _ = StageCalculator.resolve_stage(wheat_crop, das=115)
    env = EnvironmentalSnapshot(
        latitude=18.52,
        longitude=73.85,
        forecast_max_temp_c=32.0,
        forecast_min_temp_c=16.0,
        forecast_rain_24h_mm=0.0,
        forecast_rain_48h_mm=0.0,
        forecast_rain_7d_mm=0.0, # Clear dry week ahead
        rain_probability_pct=5.0,
        wind_speed_kmh=10.0,
        relative_humidity_pct=30.0,
        soil_moisture_0_7cm_pct=15.0,
        soil_moisture_7_28cm_pct=20.0,
        soil_temp_0_7cm_c=26.0,
        soil_texture_class="Clay Loam",
        consecutive_dry_days=15,
        cumulative_rain_30d_mm=0.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo"]
    )

    items = RulesEngine.evaluate(wheat_crop, stage, das=115, env=env)
    
    # Must withhold irrigation
    skip_irr = next((i for i in items if i.action == AdviceAction.SKIP_IRRIGATION), None)
    assert skip_irr is not None
    assert skip_irr.reason_code == "MATURITY_WITHHOLD_IRRIGATION"

    # Must advise harvest readiness
    harvest_item = next((i for i in items if i.action == AdviceAction.HARVEST_READY), None)
    assert harvest_item is not None
    assert harvest_item.urgency == UrgencyLevel.HIGH
