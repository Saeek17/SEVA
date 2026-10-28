from fastapi import APIRouter
from app.config import settings
from app.services.crop_engine.loader import crop_loader

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    crops = crop_loader.load_all_crops()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "crops_loaded_count": len(crops),
        "available_crops": list(crops.keys()),
        "dry_run_mode": settings.DRY_RUN,
        "mock_data_mode": settings.MOCK_DATA
    }
