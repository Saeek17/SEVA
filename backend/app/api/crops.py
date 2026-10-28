from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.crop_engine.loader import crop_loader
from app.services.crop_engine.stage_calculator import StageCalculator

router = APIRouter(prefix="/crops", tags=["Crops"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_crops():
    """Dynamically discover and list all available crops from /config/crops/*.yaml."""
    return crop_loader.list_available_crops()

@router.get("/{crop_id}")
async def get_crop(crop_id: str):
    """Retrieve full configuration and stage-by-stage thresholds for a given crop."""
    crop = crop_loader.get_crop(crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop config '{crop_id}' not found.")
    return crop.model_dump()

@router.get("/{crop_id}/stage/{das}")
async def resolve_crop_stage(crop_id: str, das: int):
    """Resolve active growth stage for a given crop at specified Days After Sowing (DAS)."""
    crop = crop_loader.get_crop(crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop config '{crop_id}' not found.")
    stage, is_post_maturity = StageCalculator.resolve_stage(crop, das)
    return {
        "crop_id": crop.crop_id,
        "das": das,
        "stage": stage.model_dump(),
        "is_post_maturity": is_post_maturity
    }
