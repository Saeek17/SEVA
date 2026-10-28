import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.services.crop_engine.loader import crop_loader
from app.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kisansaathi")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    # Dynamic Crop Discovery & Validation
    logger.info("Discovering crop configurations from /config/crops...")
    crops = crop_loader.load_all_crops(force_reload=True)
    logger.info(f"Successfully loaded {len(crops)} crops: {list(crops.keys())}")

    yield

    logger.info("Shutting down KisanSaathi API...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hyperlocal Vernacular Agro-Advisory Engine for Smallholder Farmers",
    lifespan=lifespan
)

# CORS Middleware (supports local development with Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to configured frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_v1": "/api/v1"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
