import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base directory for the KisanSaathi project
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
CONFIG_CROPS_DIR = PROJECT_ROOT / "config" / "crops"
DATA_DIR = PROJECT_ROOT / "data"

class Settings(BaseSettings):
    APP_NAME: str = "KisanSaathi"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database: Default to SQLite for seamless local dev; PostgreSQL supported
    DATABASE_URL: str = "sqlite:///./kisansaathi.db"

    # Security: 32-urlsafe base64-encoded key for Fernet AES PII encryption
    # Default fallback provided for mock/dev environment
    ENCRYPTION_KEY: str = "rV2wYpE8Z6tX0cM3vB1nK7jH5fD4sA9qL2wE5rT8yU1="
    SECRET_KEY: str = "kisansaathi-super-secret-jwt-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    # External APIs
    GEMINI_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_PHONE: str = "+15005550006" # Standard Twilio test number
    TWILIO_WHATSAPP_FROM: str = "" # e.g. "+14155238886" (Twilio WhatsApp sandbox/sender); blank disables WhatsApp
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Public HTTPS origin of this API (e.g. https://api.example.com). Twilio must fetch audio from it,
    # so relative /api/v1/... audio paths are made absolute with this value before voice calls.
    PUBLIC_BASE_URL: str = ""

    # Web Push (VAPID). Generate with: python -m scripts.generate_vapid
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@kisansaathi.local"

    # Background scheduler (06:30 IST morning batch + hourly hazard check)
    SCHEDULER_ENABLED: bool = True
    MORNING_BATCH_HOUR: int = 6
    MORNING_BATCH_MINUTE: int = 30

    # Dry-Run / Mock Modes (Allows full app to run without paid keys)
    DRY_RUN: bool = True
    MOCK_DATA: bool = False # If true, simulates weather/soil when offline

    # Caching TTLs (in seconds)
    CACHE_WEATHER_TTL_SEC: int = 10800 # 3 hours
    CACHE_HISTORICAL_TTL_SEC: int = 86400 # 24 hours
    CACHE_SOIL_TTL_SEC: int = 31536000 # 1 year (permanent)

    # Directories
    BACKEND_DIR: Path = BACKEND_DIR
    CROPS_CONFIG_PATH: Path = CONFIG_CROPS_DIR
    DATA_PATH: Path = DATA_DIR

    model_config = SettingsConfigDict(
        env_file=[str(PROJECT_ROOT / ".env"), str(BACKEND_DIR / ".env")],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
