from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.crops import router as crops_router
from app.api.evaluation import router as eval_router
from app.api.delivery_webhooks import router as delivery_router
from app.api.farmers import router as farmers_router
from app.api.advisories import router as advisories_router
from app.api.simulate import router as simulate_router
from app.api.push import router as push_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(crops_router)
api_router.include_router(farmers_router)
api_router.include_router(advisories_router)
api_router.include_router(simulate_router)
api_router.include_router(eval_router)
api_router.include_router(delivery_router)
api_router.include_router(push_router)

__all__ = ["api_router"]
