import logging
from datetime import datetime, date
from fastapi import APIRouter, HTTPException

from app.schemas.advisory import SimulationRequest, SimulationResponse
from app.services.crop_engine.loader import crop_loader
from app.services.crop_engine.stage_calculator import StageCalculator
from app.services.crop_engine.rules_engine import RulesEngine
from app.services.data_clients.aggregator import EnvironmentalAggregator
from app.services.advice_generator.generator import AdviceGenerator
from app.services.delivery.tts_service import GoogleTTSService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulate", tags=["Simulate"])

aggregator = EnvironmentalAggregator()
generator = AdviceGenerator()

@router.post("", response_model=SimulationResponse)
async def simulate_farmer_pipeline(payload: SimulationRequest):
    """
    Live Sandbox Pipeline Simulator:
    Executes the entire end-to-end KisanSaathi pipeline live:
    1. Fetches environmental data (Open-Meteo, NASA POWER, ISRIC SoilGrids).
    2. Dynamically loads crop config and determines growth stage from DAS.
    3. Runs deterministic rules engine.
    4. Generates vernacular message using LLM.
    5. Validates against hallucination & numerical drift guardrail.
    6. Synthesizes voice audio for browser preview.
    Zero real SMS or voice calls are placed.
    """
    crop = crop_loader.get_crop(payload.crop_id)
    if not crop:
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{payload.crop_id}' not found in /config/crops"
        )

    # Resolve DAS
    if payload.das is not None:
        das = max(1, payload.das)
    elif payload.sowing_date:
        try:
            s_date = datetime.strptime(payload.sowing_date, "%Y-%m-%d").date()
            das = StageCalculator.calculate_das(s_date)
        except Exception:
            das = 30
    else:
        das = 30

    stage, _ = StageCalculator.resolve_stage(crop, das)

    # 1. Fetch live environmental facts
    env = await aggregator.get_environmental_snapshot(payload.latitude, payload.longitude)

    # 2. Run deterministic rules engine
    advice_items = RulesEngine.evaluate(crop, stage, das, env)

    # 3. Generate vernacular message with anti-hallucination guardrail
    msg, passed, notes, fallback = await generator.generate_advisory(
        crop, stage, das, advice_items, language=payload.language
    )

    # 4. Generate voice audio preview
    audio_url = await GoogleTTSService.synthesize(msg, language=payload.language)

    crop_name = getattr(crop, f"common_name_{payload.language}", crop.common_name_en)

    return SimulationResponse(
        status="success",
        crop_id=crop.crop_id,
        crop_name=crop_name,
        growth_stage=stage.name_en,
        das=das,
        environmental_data=env,
        advice_items=advice_items,
        generated_message=msg,
        language=payload.language,
        validation_passed=passed,
        validation_notes=notes,
        fallback_used=fallback,
        voice_audio_url=audio_url
    )
