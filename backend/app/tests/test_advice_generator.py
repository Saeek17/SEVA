import pytest
from app.services.crop_engine.loader import CropConfigLoader
from app.services.crop_engine.stage_calculator import StageCalculator
from app.services.crop_engine.rules_engine import RulesEngine
from app.services.advice_generator.generator import AdviceGenerator
from app.services.advice_generator.template_fallback import TemplateFallback
from app.schemas.rules import EnvironmentalSnapshot, AdviceAction, AdviceItem, UrgencyLevel

@pytest.fixture
def wheat_crop():
    loader = CropConfigLoader()
    return loader.get_crop("wheat_maharashtra")

@pytest.mark.asyncio
async def test_advice_generation_end_to_end_hindi(wheat_crop):
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
        soil_moisture_0_7cm_pct=25.0,
        soil_moisture_7_28cm_pct=28.0,
        soil_temp_0_7cm_c=22.0,
        soil_texture_class="Clay Loam",
        consecutive_dry_days=8,
        cumulative_rain_30d_mm=10.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo"]
    )

    items = RulesEngine.evaluate(wheat_crop, stage, das=21, env=env)
    generator = AdviceGenerator()
    msg, passed, notes, fallback = await generator.generate_advisory(
        wheat_crop, stage, das=21, advice_items=items, language="hi"
    )

    assert len(msg) > 10
    assert len(msg) <= 320
    assert passed is True
    assert fallback == "NONE"

@pytest.mark.asyncio
async def test_advice_generation_marathi(wheat_crop):
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
        soil_moisture_0_7cm_pct=25.0,
        soil_moisture_7_28cm_pct=28.0,
        soil_temp_0_7cm_c=22.0,
        soil_texture_class="Clay Loam",
        consecutive_dry_days=8,
        cumulative_rain_30d_mm=10.0,
        data_confidence="HIGH",
        sources_used=["Open-Meteo"]
    )

    items = RulesEngine.evaluate(wheat_crop, stage, das=21, env=env)
    generator = AdviceGenerator()
    msg, passed, notes, fallback = await generator.generate_advisory(
        wheat_crop, stage, das=21, advice_items=items, language="mr"
    )

    assert len(msg) > 10
    assert len(msg) <= 320
    assert "पाणी" in msg or "सिंचन" in msg
    assert passed is True

def test_dlt_template_fallback_rendering():
    item = AdviceItem(
        action=AdviceAction.IRRIGATE,
        urgency=UrgencyLevel.HIGH,
        reason_code="CRITICAL_STAGE_MOISTURE_DEFICIT",
        params={"soil_moisture_pct": 28.5, "rain_prob_pct": 10.0, "das": 21},
        sources_used=["MPKV PoP"]
    )
    rendered = TemplateFallback.render(item, "गेहूं", "ताज जड़", "hi")
    assert "किसान साथी" in rendered
    assert "28.5" in rendered or "28" in rendered
    assert "{" not in rendered # No unrendered template brackets
